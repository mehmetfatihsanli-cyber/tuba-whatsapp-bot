import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class ButikSistemClient:
    def __init__(self):
        self.base_url = os.getenv("BUTIK_API_URL", "https://tm2.butiksistem.com/rest/")
        self.username = os.getenv("BUTIK_API_USER")
        self.password = os.getenv("BUTIK_API_PASS")
        
        if self.base_url and not self.base_url.endswith('/'):
            self.base_url += '/'

    def get_headers(self):
        return {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def get_auth_payload(self):
        # KRITIK DUZELTME: "userName" (N buyuk)
        return {
            "userName": self.username,
            "password": self.password
        }

    def get_orders(self, days=7, limit=10):
        if not self.username or not self.password:
            print("❌ HATA: Kullanıcı bilgileri eksik!")
            return None

        # API en fazla 30 günlük aralık kabul ediyor (MaxQueryRangeIs30Days)
        days = min(int(days), 30)

        endpoint = f"{self.base_url}order/get"
        
        # Tarih formati: Sadece YYYY-MM-DD
        bugun = datetime.now()
        baslangic = bugun - timedelta(days=days)
        str_start = baslangic.strftime("%Y-%m-%d")
        str_end = bugun.strftime("%Y-%m-%d")

        print(f"📡 ButikSistem Bağlanıyor... ({str_start} - {str_end})")

        payload = {
            "auth": self.get_auth_payload(),
            "arguments": {
                "startTime": str_start,
                "endTime": str_end,
                "limit": limit
            }
        }

        try:
            response = requests.post(endpoint, json=payload, headers=self.get_headers(), timeout=15)
            data = response.json()
            
            if data.get("status") is True:
                print(f"✅ BAŞARILI! Toplam Sipariş: {data['result']['total']}")
                return data['result']['data']
            else:
                print(f"❌ API Hatası: {data.get('error')}")
                return None
        except Exception as e:
            print(f"⚠️ Bağlantı Hatası: {e}")
            return None

    def check_order_by_phone(self, phone, days=30):
        """
        Telefon numarasına göre sipariş sorgula
        """
        # Telefon numarasını temizle (sadece rakamlar)
        clean_phone = ''.join(filter(str.isdigit, str(phone)))
        
        # Son X günün siparişlerini al
        orders = self.get_orders(days=days, limit=100)
        
        if not orders:
            return {
                "found": False,
                "message": "Sipariş bulunamadı",
                "orders": []
            }
        
        # Telefon numarasına göre filtrele
        matching_orders = []
        for order in orders:
            order_phone = order.get('orderPhone', '') or ''
            order_phone_clean = ''.join(filter(str.isdigit, str(order_phone)))
            
            if clean_phone in order_phone_clean or order_phone_clean in clean_phone:
                matching_orders.append(order)
        
        if matching_orders:
            return {
                "found": True,
                "message": f"{len(matching_orders)} sipariş bulundu",
                "orders": matching_orders
            }
        else:
            return {
                "found": False,
                "message": "Bu telefon numarasına ait sipariş bulunamadı",
                "orders": []
            }

    def get_last_order_delivery_and_variant(self, phone):
        """
        Değişim kargosu için: son siparişin teslimat adresi + ilk kalemin variantId.
        Returns: {"delivery": {name, surName, phone, address, city, district}, "variant_id": int|None, "order": dict}|None
        """
        result = self.check_order_by_phone(phone, days=90)
        if not result.get("found") or not result.get("orders"):
            return None
        orders = result["orders"]
        # En son sipariş (listenin ilk elemanı; API genelde yeniden eskiye sıralar)
        order = orders[0]
        # Butik API: deliveryFirstName, deliveryLastName, deliveryCity, deliveryDistrict, deliveryAddress, deliveryPhone
        fn = (order.get("deliveryFirstName") or order.get("delivery_first_name") or "").strip()
        ln = (order.get("deliveryLastName") or order.get("delivery_last_name") or "").strip()
        ph = (order.get("deliveryPhone") or order.get("orderPhone") or order.get("delivery_phone") or "").strip()
        ph = "".join(c for c in str(ph) if c.isdigit())
        if len(ph) >= 10 and not ph.startswith("0"):
            ph = "0" + ph[-10:]
        city = (order.get("deliveryCity") or order.get("delivery_city") or "").strip()
        district = (order.get("deliveryDistrict") or order.get("delivery_district") or "").strip()
        address = (order.get("deliveryAddress") or order.get("delivery_address") or "").strip()
        delivery = {
            "name": fn or "Müşteri",
            "surName": ln or fn or "Müşteri",
            "phone": ph or str(phone),
            "city": city,
            "district": district,
            "address": address or f"{city} {district}".strip(),
        }
        variant_id = None
        items = order.get("items") or order.get("orderItems") or []
        if items:
            first = items[0]
            vid = first.get("variantId") or first.get("variant_id")
            if vid:
                variant_id = int(vid)
            else:
                model = first.get("productModelCode") or first.get("product_model_code") or ""
                color = first.get("productColorCode") or first.get("product_color_code") or ""
                vname = (first.get("variantName") or first.get("variant_name") or "").strip()
                if model or color or vname:
                    code = f"{model}-{color}".strip("-") or (model or color)
                    product = self.get_product_with_variants(code) if code else None
                    if product and product.get("variants"):
                        for v in product.get("variants") or []:
                            if (v.get("name") or "").strip() == vname or not vname:
                                variant_id = int(v.get("id") or v.get("variantId") or 0)
                                break
                        if variant_id is None and product.get("variants"):
                            variant_id = int((product["variants"][0].get("id") or product["variants"][0].get("variantId") or 0))
        return {"delivery": delivery, "variant_id": variant_id, "order": order}

    def get_product_by_model_code(self, model_code):
        """
        Butik API product/get ile ürün bilgisi ve stok getir.
        Sitedeki "2209-t1" = Butik'te modelCode "2209" + colorCode "t1" (ayrı alanlar). Önce bu ayrım denenir.
        Returns: None veya {"isim", "fiyat", "stok", "varyantlar", "product_url"}
        """
        if not self.username or not self.password or not (model_code and str(model_code).strip()):
            return None
        raw = str(model_code).strip()
        # Sitedeki ürün kodu "2209-t1" veya "2209_t1" = Butik'te modelCode + colorCode ayrı
        for sep in ("-", "_"):
            if sep in raw:
                parts = raw.split(sep, 1)
                if len(parts) == 2 and parts[0].strip() and parts[1].strip():
                    urun = self._get_product_by_model_and_color(parts[0].strip(), parts[1].strip())
                    if urun is not None:
                        return urun
                break
        # Tek parça veya ayrım sonuç vermediyse: tam string ile modelCode/productCode dene
        for code in (raw, raw.replace("_", "-"), raw.replace("-", "_")):
            urun = self._get_product_by_model_code_once(code)
            if urun is not None:
                return urun
        return None

    def _get_product_by_model_and_color(self, model_part, color_part):
        """Butik'te modelCode + colorCode ile tek ürün getir (örn. 2209 + t1)."""
        if not model_part or not color_part:
            return None
        endpoint = f"{self.base_url}product/get"
        payload = {
            "auth": self.get_auth_payload(),
            "arguments": {"modelCode": model_part, "colorCode": color_part}
        }
        try:
            response = requests.post(endpoint, json=payload, headers=self.get_headers(), timeout=10)
            data = response.json()
            if data.get("status") is not True:
                return None
            result = data.get("result") or data.get("data") or {}
            items = result.get("data") if isinstance(result.get("data"), list) else (result.get("data") and [result["data"]]) or []
            if not items and isinstance(result, list):
                items = result
            if not items and isinstance(data.get("data"), list):
                items = data["data"]
            if not items:
                return None
            # Aynı model+color eşleşen ilk ürün (API bazen fazla dönebilir)
            for p in items:
                if str(p.get("modelCode") or "") == str(model_part) and str(p.get("colorCode") or "") == str(color_part):
                    return self._parse_product_item(p, f"{model_part}-{color_part}")
            return self._parse_product_item(items[0], f"{model_part}-{color_part}")
        except Exception as e:
            print(f"⚠️ Butik modelCode+colorCode hatası: {e}")
            return None

    def _get_product_by_model_code_once(self, model_code):
        """Tek bir ürün kodu ile product/get dene. Butik API bazen modelCode, bazen productCode veya modelCodes (dizi) kabul ediyor; hepsi denenecek."""
        endpoint = f"{self.base_url}product/get"
        # Sitedeki "Ürün Kodu" = Butik'te modelCode / productCode (aynı değer). API farklı parametre isimleri kullanabiliyor.
        for arg_name, arg_value in [
            ("modelCode", model_code),
            ("productCode", model_code),
            ("modelCodes", [model_code]),
        ]:
            payload = {
                "auth": self.get_auth_payload(),
                "arguments": {arg_name: arg_value}
            }
            try:
                response = requests.post(endpoint, json=payload, headers=self.get_headers(), timeout=10)
                data = response.json()
                if data.get("status") is not True:
                    continue
                result = data.get("result") or data.get("data") or {}
                items = result.get("data") if isinstance(result.get("data"), list) else (result.get("data") and [result["data"]]) or []
                if not items and isinstance(result, list):
                    items = result
                if not items and isinstance(result, dict) and result.get("id") is not None:
                    items = [result]
                if not items and isinstance(data.get("data"), list):
                    items = data["data"]
                if items:
                    # productCode bazen filtre uygulamayıp tüm listeyi döndürüyor (1178 ürün); ilk ürünü verme, eşleşeni bul
                    if len(items) > 50:
                        code_norm = (model_code or "").replace("_", "-")
                        for p in items:
                            if (str(p.get("modelCode") or "") + "-" + str(p.get("colorCode") or "")).strip("-") == code_norm:
                                return self._parse_product_item(p, model_code)
                        continue  # eşleşen yok, sonraki arg denesin
                    break
            except Exception:
                continue
        else:
            return None
        try:
            return self._parse_product_item(items[0], model_code)
        except Exception as e:
            print(f"⚠️ Butik product/get hatası: {e}")
            return None

    @staticmethod
    def _urun_adi_to_url_slug(urun_adi):
        """Ürün adından Tuba sitesi URL slug'ı üretir. Örn: Behlül Ferace Elbise Kırmızı → https://www.tubamutioglu.com/behlul-ferace-elbise-kirmizi"""
        if not (urun_adi and isinstance(urun_adi, str)):
            return ""
        tr_map = {"ü": "u", "Ü": "u", "ı": "i", "İ": "i", "I": "i", "ğ": "g", "Ğ": "g", "ş": "s", "Ş": "s", "ö": "o", "Ö": "o", "ç": "c", "Ç": "c"}
        s = urun_adi.strip()
        for tr_char, ascii_char in tr_map.items():
            s = s.replace(tr_char, ascii_char)
        s = s.lower()
        s = "".join(c if c.isalnum() or c in " -" else " " for c in s)
        slug = "-".join(s.split()).strip("-")
        if not slug:
            return ""
        base = os.getenv("TUBA_SITE_BASE_URL", "https://www.tubamutioglu.com").rstrip("/")
        return f"{base}/{slug}"

    def _parse_product_item(self, p, model_code_fallback):
        """API'den gelen tek ürün objesini {isim, fiyat, stok, varyantlar, product_url} formatına çevirir."""
        variants = p.get("variants") or p.get("variantsList") or []
        if isinstance(variants, dict):
            variants = [{"variantName": k, "quantity": v} for k, v in variants.items()]
        stok_toplam = sum(int(v.get("quantity") or v.get("stock") or 0) for v in variants)
        varyant_metni = " ".join(f"{v.get('name', v.get('variantName', ''))} stok:{v.get('quantity', 0)}" for v in variants[:10])
        isim = p.get("name") or p.get("title") or str(model_code_fallback)
        # Sitedeki gerçek URL slug tabanlı: https://www.tubamutioglu.com/behlul-ferace-elbise-kirmizi
        product_url = self._urun_adi_to_url_slug(isim)
        return {
            "isim": isim,
            "fiyat": float(p.get("salePrice") or p.get("price") or 0),
            "stok": int(p.get("totalQuantity") or p.get("stock") or stok_toplam or p.get("quantity") or 0),
            "varyantlar": varyant_metni or str(p.get("modelCode") or model_code_fallback),
            "product_url": product_url,
        }

    def urunleri_getir(self, status=1):
        """
        Butik API product/get ile tüm (veya status filtrelı) ürünleri getir.
        XML alternatifi: Tuba sitesi XML değişirse sync için Butik'ten ürün listesi alınabilir.
        Returns: [ {"id", "isim", "aciklama", "fiyat", "stok", "gorsel", "varyantlar", "product_url"}, ... ]
        """
        if not self.username or not self.password:
            return []
        endpoint = f"{self.base_url}product/get"
        payload = {
            "auth": self.get_auth_payload(),
            "arguments": {} if status is None else {"status": int(status)},
        }
        try:
            response = requests.post(endpoint, json=payload, headers=self.get_headers(), timeout=30)
            data = response.json()
            if data.get("status") is not True:
                return []
            result = data.get("result") or data.get("data") or {}
            items = result.get("data") if isinstance(result.get("data"), list) else (result.get("data") and [result["data"]]) or []
            if not items and isinstance(result, list):
                items = result
            base_url = os.getenv("TUBA_URUN_URL_TEMPLATE", "https://www.tubamutioglu.com/urun/{id}").strip()
            out = []
            for p in items:
                variants = p.get("variants") or p.get("variantsList") or []
                if isinstance(variants, dict):
                    variants = [{"variantName": k, "quantity": v} for k, v in variants.items()]
                stok_toplam = sum(int(v.get("quantity") or v.get("stock") or 0) for v in variants)
                varyant_metni = " ".join(f"{v.get('variantName', '')} {v.get('quantity', 0)}" for v in variants[:15])
                urun_id = str(p.get("modelCode") or p.get("id") or "")
                product_url = base_url.replace("{id}", urun_id) if "{id}" in base_url and urun_id else ""
                out.append({
                    "id": urun_id,
                    "isim": p.get("name") or p.get("title") or urun_id,
                    "aciklama": p.get("description") or p.get("details") or "",
                    "fiyat": float(p.get("salePrice") or p.get("price") or 0),
                    "stok": int(p.get("totalQuantity") or p.get("stock") or stok_toplam or p.get("quantity") or 0),
                    "gorsel": p.get("image") or p.get("imageLink") or "",
                    "varyantlar": varyant_metni,
                    "product_url": product_url,
                })
            return out
        except Exception as e:
            print(f"⚠️ Butik urunleri_getir hatası: {e}")
            return []

    def get_payment_types(self):
        """Ödeme tipleri (Kapıda nakit, Havale vb.) - order/add için orderPaymentTypeId seçimi."""
        if not self.username or not self.password:
            return []
        endpoint = f"{self.base_url}order/getPaymentType"
        payload = {"auth": self.get_auth_payload(), "arguments": {}}
        try:
            response = requests.post(endpoint, json=payload, headers=self.get_headers(), timeout=10)
            data = response.json()
            if data.get("status") is not True:
                return []
            result = data.get("result") or data.get("data")
            if isinstance(result, list):
                return result
            if isinstance(result, dict) and "data" in result:
                return result.get("data") or []
            return []
        except Exception as e:
            print(f"⚠️ Butik get_payment_types hatası: {e}")
            return []

    def get_product_with_variants(self, model_code, color_code=None):
        """
        Ürün bilgisi + varyant listesi (variantId, variantName) - sipariş eklerken item için gerekli.
        model_code: "2221" veya "2221-999" (ayırırsak 2221 + 999). color_code verilmezse model_code içinden ayrıştırılır.
        Returns: { "product_id", "sale_price", "variants": [ { "id", "name" } ], "model_code", "color_code" } veya None
        """
        if not self.username or not self.password or not model_code:
            return None
        mc, cc = model_code.strip(), (color_code or "").strip()
        if "-" in mc and not cc:
            parts = mc.split("-", 1)
            mc, cc = parts[0].strip(), (parts[1].strip() if len(parts) > 1 else "")
        if not cc and "_" in mc:
            parts = mc.split("_", 1)
            mc, cc = parts[0].strip(), (parts[1].strip() if len(parts) > 1 else "")
        payload_args = {"modelCode": mc}
        if cc:
            payload_args["colorCode"] = cc
        endpoint = f"{self.base_url}product/get"
        payload = {"auth": self.get_auth_payload(), "arguments": payload_args}
        try:
            response = requests.post(endpoint, json=payload, headers=self.get_headers(), timeout=10)
            data = response.json()
            if data.get("status") is not True:
                return None
            result = data.get("result") or data.get("data") or {}
            items = result.get("data") if isinstance(result.get("data"), list) else ([result.get("data")] if result.get("data") else [])
            if not items and isinstance(result, list):
                items = result
            if not items:
                return None
            p = items[0]
            variants_raw = p.get("variants") or p.get("variantsList") or []
            if isinstance(variants_raw, dict):
                variants_raw = [{"variantName": k, "id": v} if isinstance(v, (int, str)) else {"variantName": k, **v} for k, v in variants_raw.items()]
            variants = []
            for v in variants_raw:
                vid = v.get("id") or v.get("variantId") or v.get("variant_id")
                vname = (v.get("variantName") or v.get("name") or str(vid) or "").strip()
                if vid is not None:
                    variants.append({"id": str(vid), "name": vname})
            if not variants and variants_raw:
                for i, v in enumerate(variants_raw):
                    vname = (v.get("variantName") or v.get("name") or "").strip()
                    variants.append({"id": str(v.get("id", i)), "name": vname})
            return {
                "product_id": p.get("id"),
                "sale_price": float(p.get("salePrice") or p.get("price") or 0),
                "variants": variants,
                "model_code": mc,
                "color_code": cc or "",
            }
        except Exception as e:
            print(f"⚠️ Butik get_product_with_variants hatası: {e}")
            return None

    def create_order(self, custom_order_id, delivery, billing, items, order_payment_type_id,
                     order_shipping_value=50.0, order_products_value=None, description="", who_pays_shipping="sender"):
        """
        Butik order/add ile sipariş (kargo) oluşturur.
        delivery/billing: { name, surName, mail?, phone, address, city, district }
        items: [ { "variantId": "123", "quantity": 1 } ]
        order_payment_type_id: get_payment_types() ile alınan id (Kapıda nakit vb.)
        who_pays_shipping: "sender" (varsayılan) veya "recipient" (değişimde müşteri öder)
        """
        if not self.username or not self.password:
            return {"ok": False, "error": "Butik API bilgileri yok"}
        if order_products_value is None and items:
            order_products_value = 0
        endpoint = f"{self.base_url}order/add"
        delivery_payload = {
            "name": (delivery.get("name") or "").strip()[:100],
            "surName": (delivery.get("surName") or delivery.get("surname") or "").strip()[:100],
            "mail": (delivery.get("mail") or delivery.get("email") or "siparis@tubamutioglu.com")[:100],
            "phone": "".join(c for c in str(delivery.get("phone") or "") if c.isdigit())[:20],
            "address": (delivery.get("address") or "").strip()[:500],
            "city": (delivery.get("city") or "").strip()[:100],
            "district": (delivery.get("district") or "").strip()[:100],
        }
        if who_pays_shipping and str(who_pays_shipping).lower() == "recipient":
            delivery_payload["whoPaysShipping"] = "recipient"
        payload = {
            "auth": self.get_auth_payload(),
            "arguments": {
                "customOrderId": str(custom_order_id),
                "orderDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "orderPaymentTypeId": int(order_payment_type_id),
                "orderShippingValue": float(order_shipping_value),
                "orderProductsValue": float(order_products_value or 0),
                "description": str(description)[:500],
                "delivery": delivery_payload,
                "billing": {
                    "name": (billing.get("name") or delivery.get("name") or "").strip()[:100],
                    "surName": (billing.get("surName") or billing.get("surName") or delivery.get("surName") or "").strip()[:100],
                    "mail": (billing.get("mail") or billing.get("email") or delivery.get("mail") or "siparis@tubamutioglu.com")[:100],
                    "phone": "".join(c for c in str(billing.get("phone") or delivery.get("phone") or "") if c.isdigit())[:20],
                    "address": (billing.get("address") or delivery.get("address") or "").strip()[:500],
                    "city": (billing.get("city") or delivery.get("city") or "").strip()[:100],
                    "district": (billing.get("district") or delivery.get("district") or "").strip()[:100],
                },
                "items": [{"variantId": str(it.get("variantId")), "quantity": int(it.get("quantity", 1))} for it in items],
            }
        }
        try:
            response = requests.post(endpoint, json=payload, headers=self.get_headers(), timeout=15)
            data = response.json()
            if data.get("status") is True:
                order_id = data.get("result") or data.get("data")
                return {"ok": True, "order_id": order_id, "custom_order_id": custom_order_id}
            return {"ok": False, "error": data.get("error") or data.get("message") or str(data)}
        except Exception as e:
            return {"ok": False, "error": str(e)}
