import requests
import json
from datetime import datetime, timedelta

# Destek ekibinin kanitladigi bilgiler
url = "https://tm2.butiksistem.com/rest/order/get"
user = "fatihyapayws"
passwd = "gU6qH6oU4uB6wA9y"

# Tarih Hesaplama (Son 60 gunu cekelim garanti olsun)
bugun = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
gecen_ay = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d %H:%M:%S")

print(f"🚀 FINAL FIX V2... Hedef: {url}")
print(f"📅 Tarih Aralığı: {gecen_ay} - {bugun}\n")

payload = {
    "auth": {
        "userName": user,   # <-- Kilit nokta burasiydi (N buyuk)
        "password": passwd
    },
    "arguments": {
        "startTime": gecen_ay, # <-- Artik bunu istiyor
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
        print(f"Toplam Sipariş: {data['result']['total']}")
        # İlk siparişi ekrana basalım ki veriyi gorelim
        if data['result']['data']:
            print(f"Örnek Sipariş No: {data['result']['data'][0]['id']}")
    else:
        print(f"\n❌ Hata: {data}")

except Exception as e:
    print(f"⚠️ Baglanti Hatasi: {e}")
