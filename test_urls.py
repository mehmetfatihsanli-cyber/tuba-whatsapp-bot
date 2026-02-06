import requests

urls = [
    'https://tm2.butiksistem.com/rest/order/get',
    'https://tm2.butiksistem.com/webservice/rest/order/get',
    'https://api.butiksistem.com/rest/order/get',
    'https://tm2.butiksistem.com/api/order/get'
]

payload = {
    'auth': {'username': 'fatihyapay', 'password': 'Fatihyapay321!.'},
    'arguments': {'limit': 1}
}

for url in urls:
    try:
        r = requests.post(url, json=payload, timeout=5)
        print(f'URL: {url}')
        print(f'Sonuc: {r.text[:150]}')
    except Exception as e:
        print(f'URL: {url}')
        print(f'HATA: {str(e)[:50]}')
    print('---')
