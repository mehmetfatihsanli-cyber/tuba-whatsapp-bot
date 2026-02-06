import requests
import json
from datetime import datetime, timedelta

# Destek ekibinden gelen bilgiler
url = "https://tm2.butiksistem.com/rest/order/get"
user = "fatihyapayws"
passwd = "gU6qH6oU4uB6wA9y"

# DUZELTME: Saati sildik, sadece YIL-AY-GUN formatina cevirdik
bugun = datetime.now().strftime("%Y-%m-%d")
gecen_ay = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")

print(f"🚀 FINAL FIX V3... Hedef: {url}")
print(f"📅 Tarih Aralığı: {gecen_ay} - {bugun} (Saat bilgisi temizlendi)\n")

payload = {
    "auth": {
        "userName": user,   # N harfi buyuk kaldi (Dogrusu bu)
        "password": passwd
    },
    "arguments": {
        "startTime": gecen_ay,
        "endTime": bugun,
        "limit": 5
    }
}

try:
    print(f"📡 Gonderilen Paket: {json.dumps(payload, indent=2)}")
    response = requests.post(url, json=payload, timeout=10)
    data = response.json()
    
    if data.get("status") == True:
        print("\n✅✅ BINGO! VERİLER GELDİ! 🏆")
        print(f"Toplam Sipariş Sayısı: {data['result']['total']}")
        
        if data['result']['data']:
            ilk_siparis = data['result']['data'][0]
            print(f"\n--- Örnek Sipariş Detayı ---")
            print(f"Sipariş No: {ilk_siparis.get('id')}")
            print(f"Tutar: {ilk_siparis.get('orderAmount')}")
            print(f"Tarih: {ilk_siparis.get('orderDateTime')}")
    else:
        print(f"\n❌ Hata: {data}")

except Exception as e:
    print(f"⚠️ Baglanti Hatasi: {e}")
