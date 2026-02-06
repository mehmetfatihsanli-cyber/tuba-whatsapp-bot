import requests
import json
from datetime import datetime, timedelta

# Destek ekibinden gelen bilgiler
url = "https://tm2.butiksistem.com/rest/order/get"
user = "fatihyapayws"
passwd = "gU6qH6oU4uB6wA9y"

# DUZELTME: 60 gun degil, 7 gun isteyelim (Limit 30 gunmus)
bugun = datetime.now().strftime("%Y-%m-%d")
gecen_hafta = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

print(f"🚀 FINAL FIX V4... Hedef: {url}")
print(f"📅 Tarih Aralığı: {gecen_hafta} - {bugun} (7 Günlük)\n")

payload = {
    "auth": {
        "userName": user,   # N harfi buyuk
        "password": passwd
    },
    "arguments": {
        "startTime": gecen_hafta,
        "endTime": bugun,
        "limit": 5
    }
}

try:
    print(f"📡 Gonderilen Paket: {json.dumps(payload, indent=2)}")
    response = requests.post(url, json=payload, timeout=10)
    data = response.json()
    
    if data.get("status") == True:
        print("\n✅✅ BINGO! İŞTE BU KADAR! 🎉")
        print(f"Toplam Sipariş Sayısı (Son 7 Gün): {data['result']['total']}")
        
        if data['result']['data']:
            ilk = data['result']['data'][0]
            print(f"\n📦 ÖRNEK SİPARİŞ:")
            print(f"Sipariş No: {ilk.get('id')}")
            print(f"Müşteri: {ilk.get('orderBillingName')} {ilk.get('orderBillingSurname')}")
            print(f"Tutar: {ilk.get('orderAmount')} TL")
            print(f"Durum: {ilk.get('orderStatusName')}")
    else:
        print(f"\n❌ Hata: {data}")

except Exception as e:
    print(f"⚠️ Baglanti Hatasi: {e}")
