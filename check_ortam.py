#!/usr/bin/env python3
"""
Ortam kontrolü - Eksik env ve Supabase bağlantısını kontrol eder.
Kullanım: Proje klasöründe   python3 check_ortam.py
"""
import os
import sys

# Proje kökünden .env yüklensin
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

def ok(s):
    print(f"  ✅ {s}")
def eksik(s):
    print(f"  ❌ EKSİK: {s}")
def uyari(s):
    print(f"  ⚠️  {s}")

print("\n--- Ortam Kontrolü (Tuba WhatsApp Bot) ---\n")

# 1. Supabase
print("1. Supabase")
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
if url and key and "supabase.co" in url and len(key) > 50:
    ok("SUPABASE_URL ve SUPABASE_KEY var")
    try:
        from supabase import create_client
        client = create_client(url, key)
        r = client.table("messages").select("id").limit(1).execute()
        ok("Supabase bağlantısı ve 'messages' tablosu OK")
    except Exception as e:
        uyari(f"Supabase bağlantı/tablo hatası: {e}")
        print("   → supabase_messages_table.sql dosyasını Supabase SQL Editor'da çalıştırdın mı?")
else:
    if not url:
        eksik("SUPABASE_URL (.env dosyasına ekle)")
    if not key or len(key) <= 50:
        eksik("SUPABASE_KEY (.env dosyasına ekle)")

# 2. Anthropic (Claude)
print("\n2. Claude (Anthropic)")
api_key = os.getenv("ANTHROPIC_API_KEY")
if api_key and len(api_key) > 30 and api_key.startswith("sk-ant-"):
    ok("ANTHROPIC_API_KEY var")
else:
    eksik("ANTHROPIC_API_KEY (.env dosyasına ekle)")

# 3. WhatsApp (Meta)
print("\n3. WhatsApp (Meta)")
token = os.getenv("META_ACCESS_TOKEN") or os.getenv("META_TOKEN")
phone_id = os.getenv("PHONE_ID") or os.getenv("WHATSAPP_PHONE_NUMBER_ID")
if token and len(token) > 50:
    ok("META_ACCESS_TOKEN (veya META_TOKEN) var")
else:
    eksik("META_ACCESS_TOKEN (.env dosyasına ekle)")
if phone_id and len(phone_id) > 5:
    ok("PHONE_ID veya WHATSAPP_PHONE_NUMBER_ID var")
else:
    eksik("PHONE_ID veya WHATSAPP_PHONE_NUMBER_ID (.env dosyasına ekle)")

# 4. Webhook doğrulama
verify = os.getenv("VERIFY_TOKEN")
if verify:
    ok("VERIFY_TOKEN var (webhook doğrulama için)")
else:
    uyari("VERIFY_TOKEN yok; varsayılan 'tuba123' kullanılacak")

# 5. Butik (opsiyonel)
print("\n5. Butik Sistem (opsiyonel - canlı sipariş için)")
butik_url = os.getenv("BUTIK_API_URL")
butik_user = os.getenv("BUTIK_API_USER")
butik_pass = os.getenv("BUTIK_API_PASS")
if butik_url and butik_user and butik_pass:
    ok("Butik API bilgileri var")
else:
    uyari("Butik API yok; test sipariş verisi (test_orders.json) kullanılıyor")

print("\n--- Bitti. ❌ EKSİK varsa .env dosyasını düzenle, sonra tekrar çalıştır. ---\n")
