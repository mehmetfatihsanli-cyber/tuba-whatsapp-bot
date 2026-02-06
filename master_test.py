import requests

# Destek ekibinden gelen bilgiler (SABİT)
base_url = "https://tm2.butiksistem.com/rest/order/get"
api_pass = "gU6qH6oU4uB6wA9y"

# Denenecek Kullanıcı Adı Kombinasyonları
usernames = [
    "fatihyapayws",    # Destek ekibinin yazdığı (Küçük)
    "Fatihyapayws",    # Baş harfi büyük
    "FatihYapayws",    # Camel Case
    "fatihyapay",      # Eski kullanıcı adı
    "Fatihyapay"       # Eski kullanıcı adı büyük
]

print("🔍 MAYMUNCUK CALISIYOR... Dogru kapiyi ariyoruz...\n")

for user in usernames:
    payload = {
        "auth": {
            "username": user,
            "password": api_pass
        },
        "arguments": {
            "limit": 1
        }
    }
    
    try:
        response = requests.post(base_url, json=payload, timeout=5)
        data = response.json()
        
        if data.get("status") == True or "data" in data:
            print(f"✅ BINGO! BULDUM! İŞTE DOĞRU BİLGİLER:")
            print(f"User: {user}")
            print(f"Pass: {api_pass}")
            print(f"Sonuç: {str(data)[:100]}...")
            print("\n🚨 Hemen .env dosyasını bu USER ile güncelle!")
            break
        else:
            print(f"❌ {user} -> {data.get('error')}")
            
    except Exception as e:
        print(f"⚠️ Hata: {e}")

print("\n🏁 Tarama Bitti.")
