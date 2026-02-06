import os
import logging
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from supabase import create_client, Client
from modules.butiksistem_client import ButikSistemClient
import requests

# 1. Ayarlari Yukle
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# 2. Supabase Baglantisi
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✅ Supabase baglantisi basarili.")
    except Exception as e:
        logger.error(f"❌ Supabase hatasi: {e}")

# 3. ButikSistem Baglantisi
butik_client = ButikSistemClient()

# 4. Meta (WhatsApp) Ayarlari
META_TOKEN = os.getenv("META_TOKEN")
PHONE_ID = os.getenv("PHONE_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "tuba123")  # Webhook dogrulama sifresi

# --- SAYFALAR ---

@app.route('/')
def home():
    return "Tuba WhatsApp Botu & Paneli Aktif! 🚀"

@app.route('/panel')
def panel_view():
    """Tuba Hanim'in gorecegi paneli sunar"""
    return render_template('panel.html')

# --- API (PANEL ICIN) ---

@app.route('/api/customers', methods=['GET'])
def get_customers():
    """Panel icin konusma listesini getirir (Supabase'den)"""
    if not supabase: return jsonify([])
    
    # Mesajlari tarihe gore tersten cek, her numaradan son mesaji bul (Basit versiyon)
    try:
        response = supabase.table('messages').select("*").order('created_at', desc=True).limit(50).execute()
        # Burada veriyi isleyip tekil musteri listesi cikaracagiz (Frontend icin)
        return jsonify(response.data)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/send-message', methods=['POST'])
def send_message_api():
    """Panelden yazilan mesaji WhatsApp'a gonderir"""
    data = request.json
    phone = data.get('phone')
    text = data.get('text')
    
    if not phone or not text:
        return jsonify({"error": "Eksik bilgi"}), 400

    # 1. Meta API'ye Gonder
    success = send_whatsapp_message(phone, text)
    
    # 2. Supabase'e Kaydet (Giden Mesaj)
    if supabase:
        supabase.table('messages').insert({
            "phone": phone,
            "message_body": text,
            "direction": "outbound"
        }).execute()
        
    return jsonify({"status": success})

# --- WEBHOOK (WHATSAPP ICIN) ---

@app.route('/webhook', methods=['GET'])
def webhook_verify():
    """Meta'nin bizi dogrulamasi icin"""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            logger.info("WEBHOOK DOGRULANDI ✅")
            return challenge, 200
        else:
            return "Yasak", 403
    return "Merhaba", 200

@app.route('/webhook', methods=['POST'])
def webhook_receive():
    """WhatsApp'tan gelen mesajlari yakalar"""
    data = request.json
    logger.info(f"Gelen Veri: {data}")
    
    # Mesaji ayikla (Meta'nin karmasik JSON yapisindan)
    try:
        entry = data['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']
        
        if 'messages' in value:
            message = value['messages'][0]
            sender_phone = message['from']
            msg_body = message['text']['body'] if 'text' in message else "Medya/Diger"
            
            logger.info(f"📩 Mesaj Geldi: {sender_phone} - {msg_body}")

            # 1. Supabase'e Kaydet (Gelen Mesaj)
            if supabase:
                supabase.table('messages').insert({
                    "phone": sender_phone,
                    "message_body": msg_body,
                    "direction": "inbound"
                }).execute()

            # 2. OTOMATIK CEVAP MANTIGI (Basit Bot)
            cevap = None
            if "kargo" in msg_body.lower() or "nerede" in msg_body.lower():
                # ButikSistem'e sor
                orders = butik_client.get_orders(days=30)
                # (Burada normalde telefon eslesmesi yapacagiz, simdilik demo cevap)
                cevap = "📦 Siparişlerinizi kontrol ediyorum... (Sistem Test Aşamasında)"
            
            elif "merhaba" in msg_body.lower():
                cevap = "👋 Merhaba! Tuba Butik asistanıyım. Size nasıl yardımcı olabilirim?"

            # Eger botun cevabi varsa gonder
            if cevap:
                send_whatsapp_message(sender_phone, cevap)
                # Botun cevabini da kaydet
                if supabase:
                    supabase.table('messages').insert({
                        "phone": sender_phone,
                        "message_body": cevap,
                        "direction": "outbound"
                    }).execute()

    except Exception as e:
        logger.error(f"Webhook isleme hatasi: {e}")

    return jsonify({"status": "received"}), 200

def send_whatsapp_message(phone, text):
    """Meta API kullanarak mesaj atar"""
    url = f"https://graph.facebook.com/v17.0/{PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {META_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": text}
    }
    try:
        r = requests.post(url, headers=headers, json=payload)
        if r.status_code == 200:
            return True
        else:
            logger.error(f"Mesaj gonderilemedi: {r.text}")
            return False
    except Exception as e:
        logger.error(f"Request hatasi: {e}")
        return False

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
