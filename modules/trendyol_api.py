# Trendyol Partner API: sipariş çekme (Basic Auth).
# Dokümantasyon: https://developers.trendyol.com

import base64
import logging
import requests

logger = logging.getLogger(__name__)

TRENDYOL_ORDERS_URL = "https://apigw.trendyol.com/integration/order/sellers/{seller_id}/orders"
USER_AGENT_TEMPLATE = "{seller_id} - SelfIntegration"  # Max 30 karakter


def get_trendyol_orders(tenant_id, supabase_client):
    """
    Tenant'ın Trendyol bilgilerini Supabase'den alır, Trendyol Sipariş API'sine GET atar.
    Returns: (orders, stats, error)
    - orders: list of dicts with order_no, customer, product, amount, status (tablo için)
    - stats: dict with pending, shipping, returns, balance (özet kartlar için)
    - error: None veya hata mesajı (API/şifre hatası). Hata varsa orders=[], stats=None.
    Hiçbir durumda exception fırlatmaz; çökme olmaz.
    """
    orders = []
    stats = None
    error = None

    if not tenant_id:
        return orders, stats, "Tenant bilgisi yok."
    if not supabase_client:
        return orders, stats, "Veritabanı bağlantısı yok."

    # 1. Supabase'den Trendyol şifrelerini çek
    try:
        r = supabase_client.table("tenants").select(
            "trendyol_seller_id, trendyol_api_key, trendyol_api_secret"
        ).eq("tenant_id", tenant_id).limit(1).execute()
        if not r.data or len(r.data) == 0:
            return orders, stats, "Trendyol API bilgileri bulunamadı. Lütfen Entegrasyonlar sayfasından kaydedin."
        row = r.data[0]
        seller_id = (row.get("trendyol_seller_id") or "").strip()
        api_key = (row.get("trendyol_api_key") or "").strip()
        api_secret = (row.get("trendyol_api_secret") or "").strip()
        if not seller_id or not api_key or not api_secret:
            return orders, stats, "API bağlantısı kurulamadı. Lütfen API Ayarları sayfasından bilgilerinizi kontrol edin."
    except Exception as e:
        logger.warning("Trendyol tenant bilgisi okunamadı: %s", e)
        return orders, stats, "API bağlantısı kurulamadı. Lütfen API Ayarları sayfasından bilgilerinizi kontrol edin."

    # 2. Basic Auth: API Key : API Secret (Base64)
    auth_str = f"{api_key}:{api_secret}"
    try:
        auth_b64 = base64.b64encode(auth_str.encode("utf-8")).decode("ascii")
    except Exception as e:
        logger.warning("Trendyol Basic auth encode hatası: %s", e)
        return orders, stats, "API bağlantısı kurulamadı. Lütfen API Ayarları sayfasından bilgilerinizi kontrol edin."

    url = TRENDYOL_ORDERS_URL.format(seller_id=seller_id)
    user_agent = USER_AGENT_TEMPLATE.format(seller_id=seller_id)[:30]
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "User-Agent": user_agent,
        "Content-Type": "application/json",
    }
    params = {"page": 0, "size": 50}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
    except requests.exceptions.Timeout:
        return orders, stats, "API bağlantısı kurulamadı. Lütfen API Ayarları sayfasından bilgilerinizi kontrol edin."
    except requests.exceptions.RequestException as e:
        logger.warning("Trendyol API istek hatası: %s", e)
        return orders, stats, "API bağlantısı kurulamadı. Lütfen API Ayarları sayfasından bilgilerinizi kontrol edin."

    if resp.status_code == 401:
        return orders, stats, "API bağlantısı kurulamadı. Lütfen API Ayarları sayfasından bilgilerinizi kontrol edin."
    if resp.status_code == 403:
        return orders, stats, "API bağlantısı kurulamadı. Lütfen API Ayarları sayfasından bilgilerinizi kontrol edin."
    if resp.status_code == 429:
        return orders, stats, "Çok fazla istek. Lütfen kısa süre sonra tekrar deneyin."
    if resp.status_code != 200:
        try:
            err_body = resp.text[:200]
        except Exception:
            err_body = ""
        logger.warning("Trendyol API %s: %s", resp.status_code, err_body)
        return orders, stats, "API bağlantısı kurulamadı. Lütfen API Ayarları sayfasından bilgilerinizi kontrol edin."

    try:
        data = resp.json()
    except Exception as e:
        logger.warning("Trendyol API JSON parse: %s", e)
        return orders, stats, "API yanıtı işlenemedi."

    # 3. content listesini al (paginated yapı)
    content = data.get("content") if isinstance(data, dict) else None
    if not isinstance(content, list):
        content = []

    # 4. Her siparişi tablo satırına dönüştür (Trendyol alan adlarına göre)
    for item in content:
        if not isinstance(item, dict):
            continue
        order_number = item.get("orderNumber") or str(item.get("id", ""))
        # Müşteri: shipmentAddress veya customerFirstName/lastName
        addr = item.get("shipmentAddress") or {}
        if isinstance(addr, dict):
            first = (addr.get("firstName") or "").strip()
            last = (addr.get("lastName") or "").strip()
            customer = f"{first} {last}".strip() or (addr.get("fullName") or "—")
        else:
            customer = item.get("customerName") or "—"
        # Ürün: lines[0].productName veya productName
        lines = item.get("lines") or item.get("orderLines") or []
        if lines and isinstance(lines[0], dict):
            product = (lines[0].get("productName") or "—")[:60]
        else:
            product = (item.get("productName") or "—")[:60]
        # Tutar
        amount = item.get("grossAmount") or item.get("totalPrice") or item.get("totalAmount") or 0
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            amount = 0
        # Durum
        status = (item.get("status") or item.get("orderStatus") or "—")
        if isinstance(status, dict):
            status = status.get("name") or str(status)
        orders.append({
            "order_no": str(order_number),
            "customer": customer or "—",
            "product": product or "—",
            "amount": amount,
            "status": str(status),
        })

    # 5. Özet istatistikler (sipariş durumuna göre sayım)
    pending = sum(1 for o in orders if o.get("status") and any(x in str(o["status"]) for x in ("Created", "Picking", "Invoiced")))
    shipping = sum(1 for o in orders if o.get("status") and "Shipped" in str(o["status"]))
    returns = sum(1 for o in orders if o.get("status") and ("Return" in str(o["status"]) or "İade" in str(o["status"])))
    total_amount = sum(o.get("amount") or 0 for o in orders)
    stats = {
        "pending": pending,
        "shipping": shipping,
        "returns": returns,
        "balance": total_amount,
    }

    return orders, stats, None
