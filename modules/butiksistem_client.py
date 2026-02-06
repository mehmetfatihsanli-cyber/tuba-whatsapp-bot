import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class ButikSistemClient:
    def __init__(self):
        self.base_url = os.getenv("BUTIK_API_URL", "https://tm2.butiksistem.com/rest/")
        self.username = os.getenv("BUTIK_API_USER")
        self.password = os.getenv("BUTIK_API_PASS")
        
        if self.base_url and not self.base_url.endswith('/'):
            self.base_url += '/'

    def get_headers(self):
        return {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def get_auth_payload(self):
        # KRITIK DUZELTME: "userName" (N buyuk)
        return {
            "userName": self.username,
            "password": self.password
        }

    def get_orders(self, days=7, limit=10):
        if not self.username or not self.password:
            print("❌ HATA: Kullanıcı bilgileri eksik!")
            return None

        endpoint = f"{self.base_url}order/get"
        
        # Tarih formati: Sadece YYYY-MM-DD
        bugun = datetime.now()
        baslangic = bugun - timedelta(days=days)
        str_start = baslangic.strftime("%Y-%m-%d")
        str_end = bugun.strftime("%Y-%m-%d")

        print(f"📡 ButikSistem Bağlanıyor... ({str_start} - {str_end})")

        payload = {
            "auth": self.get_auth_payload(),
            "arguments": {
                "startTime": str_start,
                "endTime": str_end,
                "limit": limit
            }
        }

        try:
            response = requests.post(endpoint, json=payload, headers=self.get_headers(), timeout=15)
            data = response.json()
            
            if data.get("status") is True:
                print(f"✅ BAŞARILI! Toplam Sipariş: {data['result']['total']}")
                return data['result']['data']
            else:
                print(f"❌ API Hatası: {data.get('error')}")
                return None
        except Exception as e:
            print(f"⚠️ Bağlantı Hatası: {e}")
            return None

    def check_order_by_phone(self, phone, days=30):
        """
        Telefon numarasına göre sipariş sorgula
        """
        # Telefon numarasını temizle (sadece rakamlar)
        clean_phone = ''.join(filter(str.isdigit, str(phone)))
        
        # Son X günün siparişlerini al
        orders = self.get_orders(days=days, limit=100)
        
        if not orders:
            return {
                "found": False,
                "message": "Sipariş bulunamadı",
                "orders": []
            }
        
        # Telefon numarasına göre filtrele
        matching_orders = []
        for order in orders:
            order_phone = order.get('orderPhone', '') or ''
            order_phone_clean = ''.join(filter(str.isdigit, str(order_phone)))
            
            if clean_phone in order_phone_clean or order_phone_clean in clean_phone:
                matching_orders.append(order)
        
        if matching_orders:
            return {
                "found": True,
                "message": f"{len(matching_orders)} sipariş bulundu",
                "orders": matching_orders
            }
        else:
            return {
                "found": False,
                "message": "Bu telefon numarasına ait sipariş bulunamadı",
                "orders": []
            }
