import requests
import base64

# Destek ekibinin verdigi net bilgiler
url = "https://tm2.butiksistem.com/rest/order/get"
user = "fatihyapayws"
passwd = "gU6qH6oU4uB6wA9y"

print(f"🚀 FINAL TEST BASLIYOR... Hedef: {url}\n")

# YONTEM 1: Standart JSON Auth (Denedigimiz ama hata veren)
print("--- YONTEM 1: JSON Body Auth ---")
try:
    r1 = requests.post(url, json={'auth': {'username': user, 'password': passwd}, 'limit': 1}, timeout=10)
    print(f"Sonuc: {r1.text[:100]}")
except Exception as e: print(e)

# YONTEM 2: Basic Auth (Header'da gonderim)
print("\n--- YONTEM 2: HTTP Basic Auth ---")
try:
    r2 = requests.post(url, auth=(user, passwd), json={'limit': 1}, timeout=10)
    print(f"Sonuc: {r2.text[:100]}")
except Exception as e: print(e)

# YONTEM 3: URL Parametresi Olarak
print("\n--- YONTEM 3: URL Parametresi ---")
try:
    # Bazen username URL'de istenir
    test_url = f"{url}?username={user}&password={passwd}"
    r3 = requests.post(test_url, json={'limit': 1}, timeout=10)
    print(f"Sonuc: {r3.text[:100]}")
except Exception as e: print(e)

print("\n🏁 TEST BITTI.")
