from flask import Flask, request, jsonify
from modules.butiksistem_client import ButikSistemClient
import os
from dotenv import load_dotenv

# Ortam degiskenlerini yukle
load_dotenv()

app = Flask(__name__)

# API Baglantisini Baslat
butik_api = ButikSistemClient()

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "active", "message": "Tuba WhatsApp Bot API Calisiyor! 🚀"})

@app.route('/api/check-order', methods=['POST'])
def check_order():
    """
    n8n'den gelen istegi karsilar.
    Gelen JSON: {"phone": "5321234567"}
    """
    data = request.json
    phone = data.get('phone')

    if not phone:
        return jsonify({"status": False, "message": "Telefon numarasi eksik!"}), 400

    print(f"📡 SORGULANIYOR: {phone}")
    
    # Bizim yazdigimiz modulu kullanarak sorgula (Son 30 gun)
    result = butik_api.check_order_by_phone(phone, days=30)
    
    return jsonify(result)

if __name__ == '__main__':
    # Sunucuyu baslat
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
