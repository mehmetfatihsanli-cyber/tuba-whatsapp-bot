import requests
import json

# Destek ekibinin kanitladigi bilgiler
url = "https://tm2.butiksistem.com/rest/order/get"
user = "fatihyapayws"
passwd = "gU6qH6oU4uB6wA9y"

print(f"🚀 FINAL FIX TESTI... Hedef: {url}\n")

# DIKKAT: "username" degil "userName" (Deve Horgucu gibi N buyuk)
payload = {
    "auth": {
        "userName": user,   # <-- ISTE BURASI!
        "password": passwd
    },
    "arguments": {
        "limit": 5
    }
}

try:
    print(f"📡 Gonderilen Paket: {json.dumps(payload, indent=2)}")
    response = requests.post(url, json=payload, timeout=10)
    data = response.json()
    
    if data.get("status") == True:
        print("\n✅✅ BINGO! BAĞLANDIK! SİSTEM ONLİNE! 🎉")
        print(f"Sipariş Sayısı: {data['result']['total']}")
        print("Adamların 'userName' takıntısını çözdük!")
    else:
        print(f"\n❌ Hata Devam Ediyor: {data}")

except Exception as e:
    print(f"⚠️ Baglanti Hatasi: {e}")
