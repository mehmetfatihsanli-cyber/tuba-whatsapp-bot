# N11 Partner API: sipariş çekme (placeholder – gerçek endpoint ileride bağlanacak).
# Şimdilik Supabase'den şifreleri çekip sahte/placeholder endpoint'e istek atar; hata döndürür.

import base64
import logging
import requests

logger = logging.getLogger(__name__)

# Placeholder: gerçek N11 sipariş API endpoint'i ileride buraya yazılacak
N11_ORDERS_URL = "https://api.n11.com/ws/OrderService.wsdl"


def get_n11_orders(tenant_id, supabase_client):
    """
    Tenant'ın N11 bilgilerini Supabase'den alır, sipariş API'sine istek atar.
    Returns: (orders, stats, error)
    - orders: list of dicts (order_no, customer, product, amount, status)
    - stats: dict (pending, shipping, returns, balance) veya None
    - error: None veya hata mesajı. Hiçbir durumda exception fırlatmaz.
    """
    orders = []
    stats = None
    error = None

    if not tenant_id:
        return orders, stats, "Tenant bilgisi yok."
    if not supabase_client:
        return orders, stats, "Veritabanı bağlantısı yok."

    try:
        r = supabase_client.table("tenants").select(
            "n11_seller_id, n11_api_key, n11_api_secret"
        ).eq("tenant_id", tenant_id).limit(1).execute()
        if not r.data or len(r.data) == 0:
            return orders, stats, "N11 API bilgileri bulunamadı. Lütfen Entegrasyonlar sayfasından kaydedin."
        row = r.data[0]
        seller_id = (row.get("n11_seller_id") or "").strip()
        api_key = (row.get("n11_api_key") or "").strip()
        api_secret = (row.get("n11_api_secret") or "").strip()
        if not seller_id or not api_key or not api_secret:
            return orders, stats, "API bağlantısı kurulamadı. Lütfen API Ayarları sayfasından bilgilerinizi kontrol edin."
    except Exception as e:
        logger.warning("N11 tenant bilgisi okunamadı: %s", e)
        return orders, stats, "API bağlantısı kurulamadı. Lütfen API Ayarları sayfasından bilgilerinizi kontrol edin."

    auth_str = f"{api_key}:{api_secret}"
    try:
        auth_b64 = base64.b64encode(auth_str.encode("utf-8")).decode("ascii")
    except Exception as e:
        logger.warning("N11 Basic auth encode hatası: %s", e)
        return orders, stats, "API bağlantısı kurulamadı. Lütfen API Ayarları sayfasından bilgilerinizi kontrol edin."

    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.get(N11_ORDERS_URL, headers=headers, timeout=15)
    except requests.exceptions.Timeout:
        return orders, stats, "API bağlantısı kurulamadı. Lütfen API Ayarları sayfasından bilgilerinizi kontrol edin."
    except requests.exceptions.RequestException as e:
        logger.warning("N11 API istek hatası: %s", e)
        return orders, stats, "API bağlantısı kurulamadı. Lütfen API Ayarları sayfasından bilgilerinizi kontrol edin."

    if resp.status_code == 401:
        return orders, stats, "API bağlantısı kurulamadı. Lütfen API Ayarları sayfasından bilgilerinizi kontrol edin."
    if resp.status_code == 403:
        return orders, stats, "API bağlantısı kurulamadı. Lütfen API Ayarları sayfasından bilgilerinizi kontrol edin."
    if resp.status_code != 200:
        logger.warning("N11 API %s", resp.status_code)
        return orders, stats, "API bağlantısı kurulamadı. Lütfen API Ayarları sayfasından bilgilerinizi kontrol edin."

    try:
        data = resp.json()
    except Exception:
        # N11 WSDL XML dönebilir; JSON değilse hata
        return orders, stats, "API yanıtı işlenemedi."

    content = data.get("content") or data.get("data") or data.get("orders") if isinstance(data, dict) else []
    if not isinstance(content, list):
        content = []

    for item in content:
        if not isinstance(item, dict):
            continue
        orders.append({
            "order_no": str(item.get("orderNumber") or item.get("id") or item.get("orderId") or "—"),
            "customer": (item.get("customerName") or item.get("buyerName") or "—")[:80],
            "product": (item.get("productName") or "—")[:60],
            "amount": float(item.get("totalAmount") or item.get("totalPrice") or item.get("grossAmount") or 0),
            "status": str(item.get("status") or "—"),
        })

    pending = sum(1 for o in orders if o.get("status") and any(x in str(o["status"]) for x in ("Created", "Picking", "Invoiced", "Beklemede")))
    shipping = sum(1 for o in orders if o.get("status") and "Shipped" in str(o["status"]))
    returns = sum(1 for o in orders if o.get("status") and ("Return" in str(o["status"]) or "İade" in str(o["status"])))
    stats = {
        "pending": pending,
        "shipping": shipping,
        "returns": returns,
        "balance": sum(o.get("amount") or 0 for o in orders),
    }
    return orders, stats, None
