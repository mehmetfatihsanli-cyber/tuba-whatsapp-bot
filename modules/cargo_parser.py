# -*- coding: utf-8 -*-
"""
Satış siparişi: müşterinin tek mesajda gönderdiği kargo bilgisini parse eder.
Beklenen format: Ad Soyad, Telefon, İl İlçe Açık Adres, Ürün Kodu, Renk, Beden
(virgül veya satır ile ayrılabilir)
"""
import re


def parse_cargo_message(text):
    """
    Metinden isim, telefon, il, ilçe, adres, ürün kodu, renk, beden çıkarır.
    Returns: dict with keys name, surname, phone, city, district, address, product_code, color, size.
    Eksik alanlar None veya boş string. Hepsi doluysa sipariş oluşturmaya yeterli kabul edilir.
    """
    if not text or not isinstance(text, str):
        return {}
    text = text.strip()
    # Virgül veya satır sonu ile böl
    parts = re.split(r"[,;\n]+", text)
    parts = [p.strip() for p in parts if p.strip()]
    result = {
        "name": None,
        "surname": None,
        "phone": None,
        "city": None,
        "district": None,
        "address": None,
        "product_code": None,
        "color": None,
        "size": None,
    }
    phone_re = re.compile(r"(?:\+90\s*)?0?\s*5\d{2}\s*\d{3}\s*\d{2}\s*\d{2}")
    product_re = re.compile(r"(\d{2,6}[\-_]?\d{0,6})")
    size_re = re.compile(r"^(XX?L|S|M|L|\d{2})$", re.I)

    # Format: Ad Soyad, Telefon, İl İlçe Açık Adres, Ürün Kodu, Renk, Beden (6 parça)
    if len(parts) >= 6:
        name_part = parts[0]
        if " " in name_part:
            n = name_part.split(None, 1)
            result["name"], result["surname"] = n[0], (n[1] if len(n) > 1 else "")
        else:
            result["name"] = name_part
        ph = "".join(c for c in parts[1] if c.isdigit())
        if len(ph) >= 10:
            result["phone"] = ("0" + ph[-10:]) if not ph.startswith("0") else ph[:11]
        addr_block = parts[2]
        words = addr_block.split(None, 2)
        if len(words) >= 2:
            result["city"], result["district"] = words[0], words[1]
            result["address"] = words[2] if len(words) > 2 else addr_block
        else:
            result["address"] = addr_block
        result["product_code"] = parts[3].replace(" ", "")
        result["color"] = parts[4]
        result["size"] = parts[5]
        return result

    # Serbest format: telefon ve ürün kodu regex ile bul
    for p in parts:
        m = phone_re.search(p)
        if m:
            ph = "".join(c for c in p if c.isdigit())
            if len(ph) >= 10:
                result["phone"] = ("0" + ph[-10:]) if not ph.startswith("0") else ph[:11]
        if product_re.search(p) and (("-" in p or "_" in p) or len(p) <= 12):
            result["product_code"] = p.replace(" ", "").replace("_", "-")
        if size_re.match(p):
            result["size"] = p
    if parts and not result["name"] and not phone_re.search(parts[0]):
        name_part = parts[0]
        if " " in name_part:
            n = name_part.split(None, 1)
            result["name"], result["surname"] = n[0], (n[1] if len(n) > 1 else "")
        else:
            result["name"] = name_part
    for p in parts:
        if p and len(p) > 2 and not result["color"] and p != result.get("name") and p != result.get("product_code") and not phone_re.search(p) and not size_re.match(p):
            result["color"] = p
            break
    for p in parts:
        if len(p) > 5 and " " in p and not result["address"] and not phone_re.search(p):
            words = p.split(None, 2)
            if len(words) >= 2:
                result["city"], result["district"] = words[0], words[1]
                result["address"] = words[2] if len(words) > 2 else p
            break
    return result


def cargo_parse_sufficient(parsed):
    """Parse edilmiş dict sipariş oluşturmak için yeterli mi? (isim, telefon, adres, ürün kodu, beden min.)"""
    if not parsed:
        return False
    return bool(
        (parsed.get("name") or parsed.get("surname"))
        and parsed.get("phone")
        and (parsed.get("address") or (parsed.get("city") and parsed.get("district")))
        and parsed.get("product_code")
        and parsed.get("size")
    )


# Ödeme tercihi: mesajdan hangi ödeme türü seçildi?
PAYMENT_KEYWORDS = {
    "kapıda_nakit": ["kapıda nakit", "kapida nakit", "nakit", "kapıda ödeme nakit"],
    "kapıda_kredi": ["kapıda kredi", "kapida kredi", "kredi kartı", "kredi karti", "kapıda kart"],
    "havale": ["havale", "eft", "iban", "banka", "virman"],
    "peşin": ["peşin", "pesin", "önceden ödeme", "önceden odeme"],
}


def parse_payment_type(text):
    """
    Mesajdan ödeme türünü çıkarır.
    Returns: 'kapıda_nakit' | 'kapıda_kredi' | 'havale' | 'peşin' | None
    """
    if not text or not isinstance(text, str):
        return None
    t = text.lower().strip()
    for slug, keywords in PAYMENT_KEYWORDS.items():
        if any(k in t for k in keywords):
            return slug
    return None


def is_cargo_confirmation(text):
    """Müşteri 'tamam', 'gönderin', 'kargo ile gönderin' gibi onay verdi mi?"""
    if not text or not isinstance(text, str):
        return False
    t = text.lower().strip()
    onay = [
        "tamam", "gönderin", "gonderin", "gönder", "gonder",
        "kargo ile gönderin", "kargo ile gonderin", "kargoya verin", "kargoya ver",
        "onaylıyorum", "onayliyorum", "onay", "alıyorum", "aliyorum",
        "evet gönderin", "evet gonderin", "evet tamam", "olur", "olsun",
    ]
    return any(o in t for o in onay) or t in ("tamam", "evet", "olur", "gönder", "gonder")


def wants_different_address(text):
    """Değişim: müşteri 'başka adrese / farklı adrese gönderin' mi diyor?"""
    if not text or not isinstance(text, str):
        return False
    t = text.lower().strip()
    return any(k in t for k in [
        "farklı adres", "farkli adres", "başka adres", "baska adres",
        "farklı adrese", "farkli adrese", "başka adrese", "baska adrese",
        "yeni adres", "yeni adrese", "farklı adrese gönder", "başka adrese gönder",
    ])


def address_only_sufficient(parsed):
    """Değişim için sadece adres bilgisi yeterli mi? (il/ilçe/adres; isim/telefon sonradan doldurulabilir)"""
    if not parsed:
        return False
    return bool(parsed.get("address") or (parsed.get("city") and parsed.get("district")))


def message_looks_like_purchase_and_cargo(text):
    """
    Mesaj net satış + kargo niyeti mi? (Ürün kodu + almak istiyorum/sipariş + kargo/kapıda.)
    Bu durumda AI beklemeden hemen kargo bilgisi isteyip sales_cargo_pending'e alınır.
    """
    if not text or not isinstance(text, str):
        return False
    t = text.lower().strip()
    # Ürün kodu benzeri: 2221-999, 2221 999, 4+ rakam ve tire/nokta
    has_product_code = bool(re.search(r"\d{2,6}[\-\s_]?\d{0,6}", text))
    purchase = any(k in t for k in [
        "almak istiyorum", "alabilir miyim", "alabilirmiyim", "sipariş vericem", "sipariş vermek",
        "sipariş", "istiyorum", "alayım", "alabilir misiniz", "gönderebilir misiniz", "gönderebilirmisiniz",
        "kargo ile al", "kapıda ödeme olarak", "kapıda ödemeli",
    ])
    shipping = any(k in t for k in [
        "kargo", "kapıda", "kapida", "gönder", "gonder", "adresime", "adrese",
    ])
    return bool(has_product_code and purchase and shipping)
