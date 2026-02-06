import requests

user = 'fatihyapay'
passw = 'Fatihyapay321!.'
url = 'https://tm2.butiksistem.com/rest/order/get'

# Format 1: Mevcut
print("TEST 1: Mevcut format")
r1 = requests.post(url, json={
    'auth': {'username': user, 'password': passw},
    'arguments': {'limit': 1}
}, timeout=10)
print(f"Sonuc: {r1.text[:200]}")
print("---")

# Format 2: Duz auth
print("TEST 2: Duz auth")
r2 = requests.post(url, json={
    'username': user,
    'password': passw,
    'limit': 1
}, timeout=10)
print(f"Sonuc: {r2.text[:200]}")
print("---")

# Format 3: Basic Auth
print("TEST 3: Basic Auth")
r3 = requests.post(url, auth=(user, passw), json={'limit': 1}, timeout=10)
print(f"Sonuc: {r3.text[:200]}")
print("---")

# Format 4: Header token
print("TEST 4: API anahtari olarak")
r4 = requests.post(url, headers={'Authorization': f'Bearer {passw}'}, json={'limit': 1}, timeout=10)
print(f"Sonuc: {r4.text[:200]}")
