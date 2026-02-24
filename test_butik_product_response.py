#!/usr/bin/env python3
"""
Butik API product/get ham cevabını görmek için test scripti.
Çalıştır: python3 test_butik_product_response.py
.env'deki BUTIK_API_* değişkenleri kullanılır. Çıkan JSON'u kopyalayıp paylaşabilirsin.
"""
import os
import json
from dotenv import load_dotenv

load_dotenv()

def main():
    url = os.getenv("BUTIK_API_URL", "https://tm2.butiksistem.com/rest/").rstrip("/") + "/"
    user = os.getenv("BUTIK_API_USER")
    password = os.getenv("BUTIK_API_PASS")
    if not user or not password:
        print("HATA: .env'de BUTIK_API_USER ve BUTIK_API_PASS tanımlı olmalı.")
        return

    try:
        import requests
    except ImportError:
        print("HATA: requests yüklü değil. pip install requests")
        return

    # Ürün kodu: Butik'te modelCode + colorCode ayrı (2209 + t1)
    endpoint = url + "product/get"
    payloads = [
        ("modelCode + colorCode", {"modelCode": "2209", "colorCode": "t1"}),
        ("modelCode", "2209-t1"),
        ("productCode", "2209-t1"),
        ("modelCode", "2209_t1"),
    ]

    print("=" * 60)
    print("Butik API product/get - HAM CEVAPLAR (JSON)")
    print("=" * 60)

    for arg_name, arg_value in payloads:
        if isinstance(arg_value, dict):
            payload = {"auth": {"userName": user, "password": password}, "arguments": arg_value}
        else:
            payload = {"auth": {"userName": user, "password": password}, "arguments": {arg_name: arg_value}}
        print(f"\n--- İstek: {arg_name} = {json.dumps(arg_value)} ---")
        try:
            r = requests.post(endpoint, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
            print(f"HTTP {r.status_code}")
            try:
                data = r.json()
                if data.get("status") and data.get("result", {}).get("data"):
                    arr = data["result"]["data"]
                    print(f"Toplam {len(arr)} ürün. İlk ürün (kısa):")
                    if arr:
                        p = arr[0]
                        print(json.dumps({"id": p.get("id"), "name": p.get("name"), "modelCode": p.get("modelCode"), "colorCode": p.get("colorCode"), "price": p.get("price"), "stock": p.get("stock")}, indent=2, ensure_ascii=False))
                else:
                    print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
            except Exception:
                print(r.text[:1500])
        except Exception as e:
            print(f"Hata: {e}")

    print("\n" + "=" * 60)
    print("Yukarıdaki JSON çıktısını kopyalayıp paylaşabilirsin.")
    print("=" * 60)

if __name__ == "__main__":
    main()
