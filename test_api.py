import requests
import os
from dotenv import load_dotenv

load_dotenv()

URL = os.getenv('BUTIK_API_URL', 'https://tm2.butiksistem.com/rest/')
USER = os.getenv('BUTIK_API_USER')
PASS = os.getenv('BUTIK_API_PASS')

print("="*50)
print("BUTIKSISTEM API TEST")
print("="*50)
print(f"URL: {URL}")
print(f"User: {USER}")
print(f"Pass: {PASS[:3]}***")
print("="*50)

def test_api(endpoint, args={}):
    payload = {
        "auth": {"username": USER, "password": PASS},
        "arguments": args
    }
    try:
        r = requests.post(URL + endpoint, json=payload, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

print("\n1. AUTH TEST - order/get (limit 1)")
result = test_api("order/get", {"limit": 1})
print(f"Sonuc: {result}")

print("\n2. ODEME TIPLERI - order/getPaymentType")
result2 = test_api("order/getPaymentType", {})
print(f"Sonuc: {result2}")

print("\n" + "="*50)
print("TEST TAMAMLANDI")

