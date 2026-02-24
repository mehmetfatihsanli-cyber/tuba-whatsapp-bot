import os
import re
import logging
import uuid
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from supabase import create_client, Client
from modules.butiksistem_client import ButikSistemClient
from modules.ai_assistant import TubaAIAssistant, HANDOVER_MESAJI
from modules.tuba_rules import TubaButikKurallari
from modules.cargo_parser import (
    parse_cargo_message,
    cargo_parse_sufficient,
    parse_payment_type,
    is_cargo_confirmation,
    wants_different_address,
    address_only_sufficient,
    message_looks_like_purchase_and_cargo,
)
from modules import ai_studio_provider
from modules import virtual_studio
from modules.support_chat import get_support_reply
from modules.trendyol_api import get_trendyol_orders
from modules.hepsiburada_api import get_hepsiburada_orders
from modules.n11_api import get_n11_orders
import requests
import json
import base64

try:
    from PIL import Image
except ImportError:
    Image = None

# Virtual Try-On: panelden yüklenen varsayılan manken dosya adı (3:4 kırpılarak saklanır)
DEFAULT_MANNEQUIN_FILENAME = "default_mannequin.jpg"

# Satış: müşteri sipariş verdi sayıldığında istenen kargo bilgisi metni (sadece satış tarafı; değişim ayrı)
SALES_CARGO_INFO_REQUEST = """📦 Sipariş için; isim soyisim, telefon, il-ilçe açık adres, ürün görseli, rengi ve bedenini tek mesaj halinde eksiksiz atmanız yeterlidir 🌸

ÖDEME SEÇENEKLERİ: Peşin ödeme, Kapıda nakit, Kapıda kredi kartı, Havale-EFT (+50₺ kargo). Tercihinizi yazın 💫"""
CARGO_SHIPPING_VALUE = 50.0


def _resolve_payment_type_id(butik_client, payment_slug):
    """
    Peşin / kapıda nakit / kapıda kredi / havale -> Butik orderPaymentTypeId.
    Havale ve peşin: önce para gelir, Tuba onaylar; kapıda: direkt kargo. Hepsi Butik'te sipariş oluşturulur.
    """
    types_list = butik_client.get_payment_types() or []
    name_to_id = {}
    for pt in types_list:
        name = (pt.get("name") or pt.get("paymentTypeName") or str(pt)).lower()
        pid = int(pt.get("id") or pt.get("paymentTypeId") or 0)
        if pid:
            name_to_id[name] = pid
    slug = (payment_slug or "").strip().lower()
    for pt in types_list:
        name = (pt.get("name") or pt.get("paymentTypeName") or "").lower()
        pid = int(pt.get("id") or pt.get("paymentTypeId") or 0)
        if not pid:
            continue
        if slug == "kapıda_nakit" and ("nakit" in name or "kapıda" in name and "kredi" not in name):
            return pid
        if slug == "kapıda_kredi" and ("kredi" in name or "kart" in name):
            return pid
        if slug in ("havale", "peşin") and ("havale" in name or "eft" in name or "iban" in name or "peşin" in name or "pesin" in name):
            return pid
    return types_list[0].get("id") or types_list[0].get("paymentTypeId") or 1 if types_list else 1

# 1. Ayarlari Yukle
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "tuba-panel-secret-degisitir")
CORS(app)

# Panel sifreleri (env): PANEL_PASS_TUBA, PANEL_PASS_ZAFER, PANEL_PASS_ALI
def panel_sifre_kontrol(tenant_id, password):
    key = f"PANEL_PASS_{tenant_id.upper()}"
    return os.getenv(key) and os.getenv(key) == password

# Panel girisini gecici kapat: PANEL_SKIP_LOGIN=1 → sifre istemeden panel acilir (panel sekillendirme modu)
PANEL_SKIP_LOGIN = os.getenv("PANEL_SKIP_LOGIN", "").strip().lower() in ("1", "true", "yes")

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

# 4. AI Asistan (Butik client verilir; sipariş numaradan Butik'ten veya test verisinden bulunur)
ai_assistant = TubaAIAssistant(butik_client=butik_client)

# 5. Tuba Kurallari
tuba_kurallar = TubaButikKurallari()

# 6. Meta (WhatsApp) Ayarlari
META_TOKEN = os.getenv("META_ACCESS_TOKEN") or os.getenv("META_TOKEN")
PHONE_ID = os.getenv("PHONE_ID") or os.getenv("WHATSAPP_PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "tuba123")

# 7. Model (Claude) kontrolu - baslangicta logla (Railway'de gormek icin)
if os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_API_KEY") != "sk-ant-test":
    logger.info("✅ ANTHROPIC_API_KEY ayarli - Claude modeli kullanilacak.")
else:
    logger.warning("⚠️ ANTHROPIC_API_KEY yok veya test - Claude cevap veremez, standart/yonlendirme mesajlari gidecek.")

# --- Yasal sayfalar icin sirket bilgisi (env veya placeholder; sonra doldurulacak)
def get_company_legal():
    return {
        "legal_name": os.getenv("COMPANY_LEGAL_NAME", "ŞİRKET_ADI"),
        "address": os.getenv("COMPANY_ADDRESS", "ADRES"),
        "tax_number": os.getenv("COMPANY_TAX_NUMBER", "VERGİ_NO"),
        "tax_office": os.getenv("COMPANY_TAX_OFFICE", "VERGİ_DAİRESİ"),
        "phone": os.getenv("COMPANY_PHONE", "TELEFON"),
        "email": os.getenv("COMPANY_EMAIL", "ŞİRKET_EMAIL"),
        "mersis_no": os.getenv("COMPANY_MERSIS_NO", ""),
        "updated_date": os.getenv("LEGAL_UPDATED_DATE", "2026"),
    }

# --- Tenant marka bilgisi (company_name, logo_url) - DB veya fallback
TENANT_FALLBACK = {
    "tuba": {"company_name": "Tuba Butik", "logo_url": None},
    "zafer": {"company_name": "Zafer Giyim", "logo_url": None},
    "ali": {"company_name": "Ali", "logo_url": None},
}

def get_tenant_info(tenant_id):
    """Tenant'in company_name ve logo_url bilgisini dondurur. DB yoksa fallback."""
    if not tenant_id:
        return type("User", (), {"company_name": "Panel", "logo_url": None})()
    try:
        if supabase:
            r = supabase.table("tenants").select("company_name, logo_url").eq("tenant_id", tenant_id).limit(1).execute()
            if r.data and len(r.data) > 0:
                row = r.data[0]
                return type("User", (), {"company_name": row.get("company_name") or TENANT_FALLBACK.get(tenant_id, {}).get("company_name", tenant_id), "logo_url": row.get("logo_url")})()
    except Exception as e:
        logger.warning(f"tenants tablosu okunamadi: {e}")
    info = TENANT_FALLBACK.get(tenant_id, {"company_name": tenant_id.capitalize(), "logo_url": None})
    return type("User", (), {"company_name": info["company_name"], "logo_url": info.get("logo_url")})()

def get_tenant_extra_instruction(tenant_id):
    """Tenant'in panelden kaydettiği ek AI talimatını döndürür. Yoksa None."""
    if not tenant_id or not supabase:
        return None
    try:
        r = supabase.table("tenants").select("ai_extra_instruction").eq("tenant_id", tenant_id).limit(1).execute()
        if r.data and len(r.data) > 0 and r.data[0].get("ai_extra_instruction"):
            return (r.data[0]["ai_extra_instruction"] or "").strip() or None
    except Exception as e:
        logger.warning(f"get_tenant_extra_instruction: {e}")
    return None


# Analiz raporu özeti: Dinle+Analiz döneminde toplanan verilerden kısa özet (token dostu, prompt'a eklenir)
ANALYSIS_SUMMARY_MAX_CHARS = 420


def get_analysis_summary_for_prompt(tenant_id, line, days=2):
    """
    Son N günlük message_analyses kayıtlarından (sadece bu hat: sales/exchange) kısa özet üretir.
    Satış hattı → sadece satış analizleri, değişim hattı → sadece değişim analizleri prompt'a eklenir (akıllanma).
    Özet kısa tutulur (ANALYSIS_SUMMARY_MAX_CHARS) ki token sorunu olmasın.
    """
    if not tenant_id or not supabase or line not in ("sales", "exchange"):
        return None
    days = max(1, min(14, int(days)))
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    try:
        r = supabase.table("message_analyses").select("intent, sentiment, urgency, message_body").eq("tenant_id", tenant_id).eq("line", line).gte("created_at", since).order("created_at", desc=True).limit(250).execute()
        items = r.data or []
        if not items:
            return None
        by_intent = {}
        by_sentiment = {}
        samples = []
        for row in items:
            i = (row.get("intent") or "").strip() or "—"
            by_intent[i] = by_intent.get(i, 0) + 1
            s = (row.get("sentiment") or "").strip() or "—"
            by_sentiment[s] = by_sentiment.get(s, 0) + 1
            body = (row.get("message_body") or "").strip()
            if body and len(samples) < 2 and len(body) <= 60:
                samples.append(body[:60])
        total = len(items)
        intent_parts = [f"{k}:{v}" for k, v in sorted(by_intent.items(), key=lambda x: -x[1])[:5]]
        sentiment_parts = [f"{k}:{v}" for k, v in sorted(by_sentiment.items(), key=lambda x: -x[1])[:4]]
        summary = f"Son {days} günde {total} mesaj. Niyet: {', '.join(intent_parts)}. Duygu: {', '.join(sentiment_parts)}."
        if samples:
            summary += " Örnek: " + " | ".join(samples[:2])
        if len(summary) > ANALYSIS_SUMMARY_MAX_CHARS:
            summary = summary[:ANALYSIS_SUMMARY_MAX_CHARS - 3] + "..."
        return summary
    except Exception as e:
        logger.warning(f"get_analysis_summary_for_prompt: {e}")
    return None


def get_tenant_bot_mode(tenant_id):
    """Tek mod (geriye uyumluluk): satış hattı modunu döner."""
    return get_tenant_bot_mode_for_line(tenant_id, "sales")


def get_tenant_bot_mode_for_line(tenant_id, line):
    """Hat bazlı bot modu: live, listen_analyze, off. line = sales | exchange."""
    if not tenant_id or not supabase:
        return "live"
    try:
        r = supabase.table("tenants").select("bot_mode_sales, bot_mode_exchange").eq("tenant_id", tenant_id).limit(1).execute()
        if r.data and len(r.data) > 0:
            row = r.data[0]
            col = "bot_mode_sales" if line == "sales" else "bot_mode_exchange"
            mode = (row.get(col) or "live").strip().lower()
            if mode in ("live", "listen_analyze", "off"):
                return mode
    except Exception as e:
        logger.warning(f"get_tenant_bot_mode_for_line: {e}")
    return "live"


# --- PHONE_ID -> tenant + line (satış hattı / değişim hattı)
def phone_id_to_tenant_and_line(phone_id):
    """
    Hangi numaraya mesaj geldiyse (satış / değişim) tenant_id ve line döner.
    Returns: (tenant_id, line) where line is "sales" or "exchange".
    """
    if not phone_id:
        return "tuba", "sales"
    try:
        if supabase:
            # Önce satış numarası (mevcut whatsapp_phone_number_id)
            r = supabase.table("tenants").select("tenant_id").eq("whatsapp_phone_number_id", str(phone_id)).limit(1).execute()
            if r.data and len(r.data) > 0:
                return (r.data[0].get("tenant_id") or "tuba", "sales")
            # Değişim numarası
            r2 = supabase.table("tenants").select("tenant_id").eq("whatsapp_phone_number_id_exchange", str(phone_id)).limit(1).execute()
            if r2.data and len(r2.data) > 0:
                return (r2.data[0].get("tenant_id") or "tuba", "exchange")
    except Exception as e:
        logger.warning(f"phone_id_to_tenant_and_line DB: {e}")
    tuba_phone = os.getenv("PHONE_ID") or os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    if phone_id == tuba_phone or str(phone_id) == str(tuba_phone):
        return "tuba", "sales"
    if str(phone_id) == str(os.getenv("ZAFER_PHONE_ID", "")):
        return "zafer", "sales"
    if str(phone_id) == str(os.getenv("ALI_PHONE_ID", "")):
        return "ali", "sales"
    # Değişim numarası env (opsiyonel)
    if str(phone_id) == str(os.getenv("PHONE_ID_EXCHANGE", "")):
        return "tuba", "exchange"
    return "tuba", "sales"


def phone_id_to_tenant(phone_id):
    """Mevcut kullanım için: sadece tenant_id (line = sales kabul)."""
    tenant_id, _ = phone_id_to_tenant_and_line(phone_id)
    return tenant_id


def tenant_has_exchange_number(tenant_id):
    """Bu tenant için değişim hattı numarası tanımlı mı? (Canlıda iki numara varsa True.)"""
    if not tenant_id or not supabase:
        return False
    try:
        r = supabase.table("tenants").select("whatsapp_phone_number_id_exchange").eq("tenant_id", tenant_id).limit(1).execute()
        if r.data and len(r.data) > 0 and (r.data[0].get("whatsapp_phone_number_id_exchange") or "").strip():
            return True
    except Exception:
        pass
    return bool(os.getenv("PHONE_ID_EXCHANGE", "").strip())


def message_looks_like_exchange(msg_body):
    """Mesaj iade/değişim talebi gibi mi? (Tek numara test modunda line atamak için.)"""
    if not msg_body or not isinstance(msg_body, str):
        return False
    t = msg_body.lower().strip()
    return any(k in t for k in [
        "iade", "değişim", "degisim", "değiştirmek", "degistirmek", "iade etmek",
        "değişim istiyorum", "iade istiyorum", "farklı renk", "farkli renk", "farklı beden", "farkli beden",
        "aynı ürün", "ayni urun", "renk değişimi", "renk degisimi", "beden değişimi", "beden degisimi",
        "kargo aldım", "kargo aldim", "ürünü aldım", "urunu aldim", "değiştirmek istiyorum",
    ])

def panel_tenant_required(f):
    """Panel sayfalari icin giris zorunlu. PANEL_SKIP_LOGIN=1 ise giris atlanir (panel sekillendirme modu)."""
    from functools import wraps
    @wraps(f)
    def inner(*args, **kwargs):
        if PANEL_SKIP_LOGIN:
            if not session.get("tenant_id"):
                session["tenant_id"] = "tuba"  # API'ler icin varsayilan
            return f(*args, **kwargs)
        if not session.get("tenant_id"):
            return redirect(url_for("login_view"))
        return f(*args, **kwargs)
    return inner

# --- HEALTH (Railway / izleme) ---

@app.route('/health', methods=['GET'])
def health():
    """Canlilik kontrolu - dis izleme ve Railway icin."""
    return jsonify({"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}), 200

# --- SAYFALAR ---

@app.route('/test')
def test_page():
    """Local test: sunucu calisiyor mu, linkler dogru mu - giris gerektirmez."""
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'><title>Test</title></head><body style='font-family:sans-serif;max-width:560px;margin:2rem auto;padding:1.5rem;'>"
        "<h1>Sunucu çalışıyor</h1>"
        "<p>Doğru adres: <strong>http://127.0.0.1:5000</strong> (port 5000 şart)</p>"
        "<ul style='line-height:2;'>"
        "<li><a href='/'>Ana sayfa</a></li>"
        "<li><a href='/login'>Giriş yap</a> (girişten sonra panele gidersin)</li>"
        "<li><a href='/dashboard/integrations'>Entegrasyonlar (Trendyol)</a> — giriş gerekir</li>"
        "</ul>"
        "<p style='color:#666;'>Trendyol testi: Giriş yap → Sol menüden <strong>Entegrasyonlar</strong> → Satıcı ID / API Key / API Secret gir → Kaydet.</p>"
        "</body></html>"
    ), 200


@app.route('/')
def home():
    """Ana sayfa. PANEL_SKIP_LOGIN=1 ise direkt Panele Git; degilse Giriş yap."""
    if PANEL_SKIP_LOGIN:
        return (
            "<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Panel</title></head>"
            "<body style='font-family:sans-serif;margin:0;min-height:100vh;background:#1e293b;color:#fff;display:flex;align-items:center;justify-content:center;padding:20px;'>"
            "<div style='text-align:center;'>"
            "<p style='background:#334155;color:#94a3b8;padding:8px 14px;border-radius:8px;font-size:0.9rem;margin-bottom:20px;'>Şifre kapalı – test modu. Panele tıklayın.</p>"
            "<h1 style='margin-bottom:8px;'>Panel</h1>"
            "<p style='color:#94a3b8;margin-bottom:24px;'>Sunucu çalışıyor.</p>"
            "<a href='/dashboard' style='display:inline-block;padding:14px 28px;background:#2563eb;color:#fff;text-decoration:none;font-weight:600;border-radius:10px;'>Panele git</a>"
            "</div></body></html>"
        ), 200
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Panel</title></head>"
        "<body style='font-family:sans-serif;margin:0;min-height:100vh;background:#1e293b;color:#fff;display:flex;align-items:center;justify-content:center;padding:20px;'>"
        "<div style='text-align:center;'>"
        "<h1 style='margin-bottom:8px;'>Panel</h1>"
        "<p style='color:#94a3b8;margin-bottom:24px;'>Sunucu çalışıyor. Aşağıdaki linke tıkla.</p>"
        "<a href='/login' style='display:inline-block;padding:14px 28px;background:#2563eb;color:#fff;text-decoration:none;font-weight:600;border-radius:10px;'>Giriş yap</a>"
        "<p style='margin-top:20px;'><a href='/dashboard/integrations' style='color:#94a3b8;'>Entegrasyonlar (Trendyol)</a></p>"
        "</div></body></html>"
    ), 200

# --- Yasal sayfalar (Sanal POS / Iyzico-PayTR basvurusu icin zorunlu)
@app.route('/legal/privacy')
def legal_privacy():
    return render_template('legal/privacy.html', company=get_company_legal())

@app.route('/legal/terms')
def legal_terms():
    return render_template('legal/terms.html', company=get_company_legal())

@app.route('/legal/sales-agreement')
def legal_sales_agreement():
    return render_template('legal/sales-agreement.html', company=get_company_legal())

@app.route('/legal/cancellation')
def legal_cancellation():
    return render_template('legal/cancellation.html', company=get_company_legal())

@app.route('/legal/about')
def legal_about():
    return render_template('legal/about.html', company=get_company_legal())

def _tenant_slug(name):
    """Mağaza adından tenant_id için slug: küçük harf, boşluk->alt çizgi, alfanumerik."""
    s = (name or "").strip()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"[-\s]+", "_", s).strip("_").lower()[:24] or "magaza"
    return s

@app.route('/register', methods=['GET', 'POST'])
def register_view():
    """Kayit: Ad Soyad, E-posta, Sifre, Magaza Adi -> yeni tenant olustur, otomatik giris, dashboard."""
    if session.get("tenant_id"):
        return redirect(url_for("dashboard_view"))
    if request.method == 'GET':
        return render_template("register.html")
    full_name = (request.form.get("full_name") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    store_name = (request.form.get("store_name") or "").strip()
    if not email or not password or not store_name:
        return render_template("register.html", error="Ad Soyad, E-posta, Şifre ve Mağaza Adı zorunludur.")
    if len(password) < 6:
        return render_template("register.html", error="Şifre en az 6 karakter olmalıdır.")
    if not supabase:
        return render_template("register.html", error="Kayıt şu an kullanılamıyor. Lütfen daha sonra deneyin.")
    base_slug = _tenant_slug(store_name)
    tenant_id = base_slug
    for _ in range(10):
        try:
            existing = supabase.table("tenants").select("tenant_id").eq("tenant_id", tenant_id).limit(1).execute()
            if existing.data and len(existing.data) > 0:
                tenant_id = base_slug + "_" + uuid.uuid4().hex[:6]
                continue
            break
        except Exception:
            tenant_id = base_slug + "_" + uuid.uuid4().hex[:6]
    try:
        email_check = supabase.table("tenants").select("tenant_id").eq("email", email).limit(1).execute()
        if email_check.data and len(email_check.data) > 0:
            return render_template("register.html", error="Bu e-posta adresi zaten kayıtlı.")
    except Exception as e:
        logger.warning(f"Tenant email kontrolu atlandi: {e}")
    password_hash = generate_password_hash(password, method="scrypt")
    try:
        supabase.table("tenants").insert({
            "tenant_id": tenant_id,
            "company_name": store_name,
            "email": email,
            "password_hash": password_hash,
        }).execute()
        session["tenant_id"] = tenant_id
        logger.info(f"Yeni kayit: tenant_id={tenant_id} email={email}")
        return redirect(url_for("dashboard_view"))
    except Exception as e:
        logger.exception(f"Kayit hatasi: {e}")
        return render_template("register.html", error="Kayıt sırasında bir hata oluştu. E-posta zaten kullanılıyor olabilir.")

@app.route('/login', methods=['GET', 'POST'])
def login_view():
    """Giris: magaza + sifre (eski) veya e-posta + sifre (kayitli magazalar)."""
    if session.get("tenant_id"):
        return redirect(url_for("dashboard_view"))
    # PANEL_SKIP_LOGIN: GET'te otomatik giris yapma; kullanici "Panele gir" deyince giris olsun
    if PANEL_SKIP_LOGIN and request.method == 'POST' and request.form.get("skip_login_confirm"):
        session["tenant_id"] = "tuba"
        return redirect(url_for("dashboard_view"))
    if PANEL_SKIP_LOGIN and request.method == 'GET':
        return render_template("panel_login.html", skip_login_mode=True)
    if request.method == 'POST':
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        if email and password and supabase:
            try:
                r = supabase.table("tenants").select("tenant_id, password_hash").eq("email", email).limit(1).execute()
                if r.data and len(r.data) > 0 and r.data[0].get("password_hash"):
                    if check_password_hash(r.data[0]["password_hash"], password):
                        session["tenant_id"] = r.data[0]["tenant_id"]
                        return redirect(url_for("dashboard_view"))
            except Exception as e:
                logger.warning(f"E-posta ile giris hatasi: {e}")
        tenant_id = (request.form.get("tenant") or "").strip().lower()
        if tenant_id in ("tuba", "zafer", "ali") and panel_sifre_kontrol(tenant_id, password):
            session["tenant_id"] = tenant_id
            return redirect(url_for("dashboard_view"))
        return render_template("panel_login.html", error="Mağaza/ e-posta veya şifre hatalı.", skip_login_mode=PANEL_SKIP_LOGIN)
    return render_template('panel_login.html', skip_login_mode=PANEL_SKIP_LOGIN)

@app.route('/panel/login', methods=['GET'])
def panel_login_redirect():
    """Eski panel/login adresi - /login'e yonlendir."""
    return redirect(url_for("login_view"), code=302)

# --- Sifre Sifirlama (Forgot / Reset) ---
RESET_TOKEN_EXPIRY_HOURS = 1
MAIL_SERVER = os.getenv("MAIL_SERVER")
MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "1").strip().lower() in ("1", "true", "yes")
MAIL_FROM = os.getenv("MAIL_FROM") or MAIL_USERNAME
BASE_URL = os.getenv("BASE_URL", "").rstrip("/")  # Ornek: https://tuba-whatsapp-bot-production.up.railway.app

def send_reset_email(to_email: str, reset_link: str) -> bool:
    """SMTP ile sifre sifirlama maili gonder. Basarili ise True."""
    if not MAIL_SERVER or not MAIL_USERNAME or not MAIL_PASSWORD:
        logger.warning("MAIL_SERVER / MAIL_USERNAME / MAIL_PASSWORD ayarli degil; mail gonderilmedi.")
        return False
    body = f"""Merhaba,

Şifrenizi sıfırlamak için aşağıdaki linke tıklayın:

{reset_link}

Bu link 1 saat geçerlidir. Eğer bu talebi siz yapmadıysanız bu e-postayı dikkate almayın.

— Tuba WhatsApp Bot"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Şifre Sıfırlama – Tuba WhatsApp Bot"
    msg["From"] = MAIL_FROM or MAIL_USERNAME
    msg["To"] = to_email
    msg.attach(MIMEText(body, "plain", "utf-8"))
    try:
        with smtplib.SMTP(MAIL_SERVER, MAIL_PORT) as smtp:
            if MAIL_USE_TLS:
                smtp.starttls()
            smtp.login(MAIL_USERNAME, MAIL_PASSWORD)
            smtp.sendmail(MAIL_FROM or MAIL_USERNAME, to_email, msg.as_string())
        logger.info(f"Sifre sifirlama maili gonderildi: {to_email}")
        return True
    except Exception as e:
        logger.exception(f"Mail gonderilemedi: {e}")
        return False

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password_view():
    """Sifremi unuttum: e-posta al, token uret, mail at."""
    if session.get("tenant_id"):
        return redirect(url_for("dashboard_view"))
    if request.method == 'GET':
        return render_template("forgot_password.html")
    email = (request.form.get("email") or "").strip().lower()
    if not email:
        return render_template("forgot_password.html", error="E-posta adresi girin.")
    if not supabase:
        return render_template("forgot_password.html", error="Şifre sıfırlama şu an kullanılamıyor.")
    try:
        r = supabase.table("tenants").select("tenant_id").eq("email", email).limit(1).execute()
        if not r.data or len(r.data) == 0:
            return render_template("forgot_password.html", error="Bu e-posta adresi kayıtlı değil.")
        tenant_id = r.data[0]["tenant_id"]
        token = secrets.token_urlsafe(32)
        expires = datetime.now(timezone.utc) + timedelta(hours=RESET_TOKEN_EXPIRY_HOURS)
        supabase.table("tenants").update({
            "reset_token": token,
            "reset_token_expires": expires.isoformat(),
        }).eq("tenant_id", tenant_id).execute()
        base = BASE_URL or request.url_root.rstrip("/")
        reset_link = f"{base}/reset-password/{token}"
        if send_reset_email(email, reset_link):
            return render_template("forgot_password.html", success="E-posta adresinize şifre sıfırlama linki gönderildi. Lütfen gelen kutunuzu kontrol edin.")
        return render_template("forgot_password.html", error="E-posta gönderilemedi. Lütfen daha sonra tekrar deneyin.")
    except Exception as e:
        logger.exception(f"Forgot password hatasi: {e}")
        return render_template("forgot_password.html", error="Bir hata oluştu. Lütfen daha sonra tekrar deneyin.")

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password_view(token):
    """Token ile yeni sifre al, hash'le, guncelle."""
    if session.get("tenant_id"):
        return redirect(url_for("dashboard_view"))
    if not token or not supabase:
        return render_template("reset_password.html", token="", error="Geçersiz veya süresi dolmuş link.")
    if request.method == 'GET':
        try:
            r = supabase.table("tenants").select("tenant_id, reset_token_expires").eq("reset_token", token).limit(1).execute()
            if not r.data or len(r.data) == 0:
                return render_template("reset_password.html", token=token, error="Geçersiz veya süresi dolmuş link.")
            exp = r.data[0].get("reset_token_expires")
            if exp:
                try:
                    exp_str = exp.replace("Z", "+00:00") if isinstance(exp, str) else exp.isoformat()
                    exp_dt = datetime.fromisoformat(exp_str) if isinstance(exp_str, str) else exp
                    if exp_dt.tzinfo is None:
                        exp_dt = exp_dt.replace(tzinfo=timezone.utc)
                    if datetime.now(timezone.utc) > exp_dt:
                        return render_template("reset_password.html", token=token, error="Linkin süresi dolmuş. Lütfen yeni sıfırlama talebi gönderin.")
                except Exception:
                    pass
            return render_template("reset_password.html", token=token)
        except Exception as e:
            logger.warning(f"Reset token kontrolu: {e}")
            return render_template("reset_password.html", token=token, error="Geçersiz link.")
    password = request.form.get("password") or ""
    password_confirm = request.form.get("password_confirm") or ""
    if password != password_confirm:
        return render_template("reset_password.html", token=token, error="Şifreler eşleşmiyor.")
    if len(password) < 6:
        return render_template("reset_password.html", token=token, error="Şifre en az 6 karakter olmalıdır.")
    try:
        r = supabase.table("tenants").select("tenant_id, reset_token_expires").eq("reset_token", token).limit(1).execute()
        if not r.data or len(r.data) == 0:
            return render_template("reset_password.html", token=token, error="Geçersiz veya süresi dolmuş link.")
        exp = r.data[0].get("reset_token_expires")
        if exp:
            try:
                exp_str = exp.replace("Z", "+00:00") if isinstance(exp, str) else exp.isoformat()
                exp_dt = datetime.fromisoformat(exp_str) if isinstance(exp_str, str) else exp
                if exp_dt.tzinfo is None:
                    exp_dt = exp_dt.replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) > exp_dt:
                    return render_template("reset_password.html", token=token, error="Linkin süresi dolmuş. Lütfen yeni sıfırlama talebi gönderin.")
            except Exception:
                pass
        tenant_id = r.data[0]["tenant_id"]
        password_hash = generate_password_hash(password, method="scrypt")
        supabase.table("tenants").update({
            "password_hash": password_hash,
            "reset_token": None,
            "reset_token_expires": None,
        }).eq("tenant_id", tenant_id).execute()
        logger.info(f"Sifre sifirlandi: tenant_id={tenant_id}")
        return redirect(url_for("login_view"))
    except Exception as e:
        logger.exception(f"Reset password hatasi: {e}")
        return render_template("reset_password.html", token=token, error="Şifre güncellenirken hata oluştu.")

@app.route('/panel/logout')
def panel_logout_redirect():
    return redirect(url_for("dashboard_logout"), code=302)

@app.route('/dashboard/logout')
def dashboard_logout():
    session.pop("tenant_id", None)
    # Ana sayfaya yonlendir; login'e gidersek PANEL_SKIP_LOGIN ile aninda tekrar giris oluyordu
    return redirect(url_for("home"))

@app.route('/dashboard')
@panel_tenant_required
def dashboard_view():
    """Dashboard - KPI, modul kartlari, canli akis."""
    tenant_id = session.get("tenant_id")
    current_user = get_tenant_info(tenant_id)
    return render_template('index.html', current_user=current_user, tenant_id=tenant_id, skip_login=PANEL_SKIP_LOGIN)


@app.route('/dashboard/analiz-raporu')
@panel_tenant_required
def analiz_raporu_view():
    """Dinle+Analiz döneminde toplanan analiz kayıtlarını metin rapor olarak gösterir."""
    tenant_id = session.get("tenant_id")
    current_user = get_tenant_info(tenant_id)
    return render_template('dashboard/analiz_raporu.html', current_user=current_user, tenant_id=tenant_id, skip_login=PANEL_SKIP_LOGIN)

@app.route('/dashboard/messages')
@panel_tenant_required
def messages_view():
    """Mesajlar - sohbet listesi. hat=satis veya hat=iade ile filtre (intent yoksa su an ayni veri)."""
    hat = (request.args.get("hat") or "").strip().lower()
    if hat not in ("satis", "iade"):
        return redirect(url_for("messages_view", hat="satis"), code=302)
    tenant_id = session.get("tenant_id")
    current_user = get_tenant_info(tenant_id)
    return render_template('panel.html', current_user=current_user, tenant_id=tenant_id, skip_login=PANEL_SKIP_LOGIN, hat=hat)

@app.route('/dashboard/studio')
@panel_tenant_required
def panel_studio():
    """Model Talimatı - Mağaza ek talimatı (bot karakteri) editörü."""
    tenant_id = session.get("tenant_id")
    current_user = get_tenant_info(tenant_id)
    return render_template('studio.html', current_user=current_user, tenant_id=tenant_id, skip_login=PANEL_SKIP_LOGIN)

@app.route('/dashboard/ai-studio')
@panel_tenant_required
def panel_ai_studio():
    """AI Stüdyo - Ürün görseli / 360° vb. (Çok Yakında placeholder)."""
    tenant_id = session.get("tenant_id")
    current_user = get_tenant_info(tenant_id)
    return render_template('ai_studio.html', current_user=current_user, tenant_id=tenant_id, skip_login=PANEL_SKIP_LOGIN)

@app.route('/dashboard/pipeline')
@panel_tenant_required
def pipeline_view():
    """Satış Hunisi (Kanban): müşterileri status'a göre 4 sütunda gösterir. hat=satis|iade ile satış/değişim hattı filtresi."""
    tenant_id = session.get("tenant_id")
    current_user = get_tenant_info(tenant_id)
    hat = (request.args.get("hat") or "satis").strip().lower()
    line = _hat_to_line(hat)
    customers_by_status = {"new": [], "interested": [], "negotiation": [], "won": [], "return": []}
    if not supabase:
        return render_template('dashboard/pipeline.html', current_user=current_user, tenant_id=tenant_id, skip_login=PANEL_SKIP_LOGIN, customers_by_status=customers_by_status, hat=hat)
    try:
        r = supabase.table("customers").select("id, tenant_id, phone, first_seen_at, last_message_at, status, tags").eq("tenant_id", tenant_id).eq("line", line).execute()
        customers = r.data or []
        phones = [c["phone"] for c in customers]
        last_msg = {}
        if phones:
            msg_r = supabase.table("messages").select("phone, message_body, created_at").eq("tenant_id", tenant_id).eq("line", line).order("created_at", desc=True).limit(500).execute()
            for m in (msg_r.data or []):
                p = m.get("phone")
                if p and p not in last_msg:
                    last_msg[p] = {"body": (m.get("message_body") or "").strip()[:120], "at": m.get("created_at")}
        for c in customers:
            status = (c.get("status") or "new").strip().lower()
            if status not in customers_by_status:
                customers_by_status[status] = []
            ph = c.get("phone") or ""
            disp = ph[-4:] if len(ph) >= 4 else ph
            if len(ph) > 4:
                disp = "***" + disp
            info = last_msg.get(ph) or {}
            ts = info.get("at") or c.get("last_message_at") or c.get("first_seen_at")
            customers_by_status[status].append({
                "id": c.get("id"),
                "phone": ph,
                "status": status,
                "display_phone": disp or "—",
                "last_message_body": info.get("body"),
                "time_ago": _time_ago(ts),
                "tags": c.get("tags") or [],
            })
    except Exception as e:
        logger.exception("Pipeline veri alinamadi: %s", e)
    return render_template('dashboard/pipeline.html', current_user=current_user, tenant_id=tenant_id, skip_login=PANEL_SKIP_LOGIN, customers_by_status=customers_by_status, hat=hat)

def _time_ago(ts):
    """created_at / last_message_at için '2 sa önce' benzeri metin."""
    if not ts:
        return "—"
    try:
        if isinstance(ts, str) and "Z" in ts:
            ts = ts.replace("Z", "+00:00")
        t = datetime.fromisoformat(ts) if isinstance(ts, str) else ts
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - t
        if delta.total_seconds() < 60:
            return "Az önce"
        if delta.total_seconds() < 3600:
            return f"{int(delta.total_seconds() / 60)} dk önce"
        if delta.total_seconds() < 86400:
            return f"{int(delta.total_seconds() / 3600)} sa önce"
        if delta.days < 7:
            return f"{delta.days} gün önce"
        return t.strftime("%d.%m.%Y")
    except Exception:
        return "—"

@app.route('/api/studio/extra-prompt', methods=['GET', 'POST'])
@panel_tenant_required
def api_studio_extra_prompt():
    """Panel: GET = ek talimatı döndür, POST = ek talimatı kaydet. Bir kez yazılır, değiştirene kadar kalır."""
    tenant = _panel_tenant()
    if not tenant:
        return jsonify({"error": "Oturum gerekli"}), 401
    if request.method == 'GET':
        extra = get_tenant_extra_instruction(tenant)
        return jsonify({"extra_instruction": extra or ""})
    # POST
    data = request.get_json(force=True, silent=True) or {}
    text = (data.get("extra_instruction") or "").strip()
    try:
        if supabase:
            supabase.table("tenants").update({"ai_extra_instruction": text if text else None}).eq("tenant_id", tenant).execute()
            logger.info(f"Ek talimat kaydedildi: tenant={tenant} length={len(text)}")
        return jsonify({"ok": True, "message": "Kaydedildi."})
    except Exception as e:
        logger.exception("Ek talimat kaydedilemedi: %s", e)
        return jsonify({"error": "Kayıt sırasında hata oluştu."}), 500


@app.route('/api/ai-studio/status', methods=['GET'])
@panel_tenant_required
def api_ai_studio_status():
    """AI Stüdyo: API anahtarı tanımlı mı?"""
    configured = ai_studio_provider.is_configured()
    return jsonify({"configured": configured})


@app.route('/api/ai-studio/generate', methods=['POST'])
@panel_tenant_required
def api_ai_studio_generate():
    """
    Ürün görseli + metin talimatı ile AI görsel üretir (örn. manken üzerinde göster).
    Form: images[] (veya image), prompt. Response: { success, image_url, error? }
    """
    tenant = _panel_tenant()
    if not tenant:
        return jsonify({"success": False, "error": "Giriş gerekli"}), 403

    if not ai_studio_provider.is_configured():
        return jsonify({"success": False, "error": "AI Stüdyo API anahtarı ayarlanmamış. NANO_BANANA_API_KEY ekleyin."}), 503

    prompt = (request.form.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"success": False, "error": "Talimat (prompt) yazın."}), 400

    files = request.files.getlist("images") or request.files.getlist("image") or []
    if not files and request.files.get("image"):
        files = [request.files.get("image")]
    if not files:
        return jsonify({"success": False, "error": "En az bir görsel yükleyin."}), 400

    images_b64 = []
    for f in files:
        if not f or not f.filename:
            continue
        try:
            data = f.read()
            if len(data) > 20 * 1024 * 1024:  # 20MB
                return jsonify({"success": False, "error": "Görsel 20MB'dan küçük olmalı."}), 400
            images_b64.append(base64.b64encode(data).decode("utf-8"))
        except Exception as e:
            logger.warning("AI Studio image read: %s", e)
            return jsonify({"success": False, "error": "Görsel okunamadı."}), 400
    if not images_b64:
        return jsonify({"success": False, "error": "Geçerli bir görsel yükleyin."}), 400

    success, image_url, err = ai_studio_provider.generate_from_multiple_images(images_b64, prompt)
    if not success:
        return jsonify({"success": False, "error": err or "Üretim başarısız."}), 422
    return jsonify({"success": True, "image_url": image_url})


@app.route('/api/ai-studio/refine', methods=['POST'])
@panel_tenant_required
def api_ai_studio_refine():
    """
    Önceki sonuç görseli + yeni talimat ile yeniden üretir (örn. "Manken yerine model kullan").
    Form: image (file) veya image_url (önceki sonuç), prompt.
    """
    tenant = _panel_tenant()
    if not tenant:
        return jsonify({"success": False, "error": "Giriş gerekli"}), 403
    if not ai_studio_provider.is_configured():
        return jsonify({"success": False, "error": "API anahtarı ayarlanmamış."}), 503

    prompt = (request.form.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"success": False, "error": "Yeni talimat yazın."}), 400

    image_b64 = None
    if request.files.get("image"):
        try:
            data = request.files.get("image").read()
            if len(data) > 20 * 1024 * 1024:
                return jsonify({"success": False, "error": "Görsel 20MB'dan küçük olmalı."}), 400
            image_b64 = base64.b64encode(data).decode("utf-8")
        except Exception:
            return jsonify({"success": False, "error": "Görsel okunamadı."}), 400
    else:
        image_url = (request.form.get("image_url") or "").strip()
        if not image_url:
            return jsonify({"success": False, "error": "Önceki görsel veya yeni görsel gerekli."}), 400
        try:
            r = requests.get(image_url, timeout=30)
            r.raise_for_status()
            image_b64 = base64.b64encode(r.content).decode("utf-8")
        except Exception as e:
            logger.warning("AI Studio refine fetch image: %s", e)
            return jsonify({"success": False, "error": "Önceki görsel indirilemedi."}), 400

    success, out_url, err = ai_studio_provider.generate_product_on_model(image_b64, prompt)
    if not success:
        return jsonify({"success": False, "error": err or "Yeniden üretim başarısız."}), 422
    return jsonify({"success": True, "image_url": out_url})


@app.route('/api/tryon-status', methods=['GET'])
@panel_tenant_required
def api_tryon_status():
    """Virtual Try-On: Replicate API hazır mı?"""
    return jsonify({"configured": virtual_studio.is_configured()})


@app.route('/api/tryon-image-proxy', methods=['GET'])
@panel_tenant_required
def api_tryon_image_proxy():
    """Replicate çıktı görselini proxy'leyerek tarayıcıda kesin yüklenmesini sağlar."""
    from flask import Response
    url = (request.args.get("url") or "").strip()
    content_type, body = _tryon_proxy_fetch(url)
    if not body:
        return jsonify({"error": "Geçersiz URL veya görsel yüklenemedi."}), 400
    return Response(body, status=200, mimetype=content_type)


def _tryon_proxy_fetch(url):
    """Replicate/izinli URL'den görsel indir; (content_type, bytes) veya (None, None)."""
    allowed = ("https://replicate.delivery/", "https://pb.replicate.delivery/", "https://images.unsplash.com/")
    base = (BASE_URL or request.host_url or "").rstrip("/")
    ok = url and (url.startswith(allowed[0]) or url.startswith(allowed[1]) or url.startswith(allowed[2]) or (base and url.startswith(base)))
    if not ok:
        return None, None
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return (r.headers.get("Content-Type") or "image/jpeg"), r.content
    except requests.RequestException:
        return None, None


@app.route('/api/tryon-download', methods=['GET'])
@panel_tenant_required
def api_tryon_download():
    """İndir butonu: görseli proxy'den indirir; dosya gerçek JPEG olur, açılır."""
    from flask import Response
    url = (request.args.get("url") or "").strip()
    content_type, body = _tryon_proxy_fetch(url)
    if not body:
        return jsonify({"error": "Görsel alınamadı."}), 400
    return Response(body, status=200, mimetype=content_type, headers={
        "Content-Disposition": 'attachment; filename="virtual-tryon-sonuc.jpg"'
    })


def _default_mannequin_path():
    return os.path.join(app.root_path, "static", "uploads", DEFAULT_MANNEQUIN_FILENAME)


def _crop_image_to_34(source_path, dest_path, target_w=600, target_h=800):
    """Görseli 3:4 oranında ortadan kırpar ve target_w x target_h boyutuna getirir."""
    if not Image:
        return False
    try:
        img = Image.open(source_path).convert("RGB")
        w, h = img.size
        target_ratio = target_w / target_h  # 3/4
        current_ratio = w / h
        if current_ratio > target_ratio:
            new_w = int(h * target_ratio)
            left = (w - new_w) // 2
            img = img.crop((left, 0, left + new_w, h))
        else:
            new_h = int(w / target_ratio)
            top = (h - new_h) // 2
            img = img.crop((0, top, w, top + new_h))
        img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        img.save(dest_path, "JPEG", quality=90)
        return True
    except Exception as e:
        logger.warning("3:4 crop hatası: %s", e)
        return False


@app.route('/api/ai-studio/default-mannequin', methods=['GET'])
@panel_tenant_required
def api_default_mannequin_status():
    """Panelden yüklenen varsayılan manken var mı?"""
    path = _default_mannequin_path()
    return jsonify({"set": os.path.isfile(path)})


@app.route('/api/ai-studio/default-mannequin/remove', methods=['POST', 'DELETE'])
@panel_tenant_required
def api_default_mannequin_remove():
    """Varsayılan manken görselini kaldır (dosyayı sil)."""
    path = _default_mannequin_path()
    if os.path.isfile(path):
        try:
            os.remove(path)
            logger.info("Varsayılan manken kaldırıldı: %s", path)
        except Exception as e:
            logger.warning("Varsayılan manken silinemedi: %s", e)
            return jsonify({"ok": False, "error": "Dosya silinemedi."}), 500
    return jsonify({"ok": True, "message": "Manken görseli kaldırıldı."})


@app.route('/api/ai-studio/default-mannequin', methods=['POST'])
@panel_tenant_required
def api_default_mannequin_upload():
    """Varsayılan manken görseli yükle; 3:4 oranına kırpıp kaydeder. Müşteriden URL istemeye gerek kalmaz."""
    tenant = _panel_tenant()
    if not tenant:
        return jsonify({"ok": False, "error": "Giriş gerekli"}), 403
    f = request.files.get("image") or request.files.get("file") or request.files.get("mannequin")
    if not f or not f.filename:
        return jsonify({"ok": False, "error": "Görsel dosyası seçin."}), 400
    upload_dir = os.path.join(app.root_path, "static", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    tmp_path = os.path.join(upload_dir, "tmp_mannequin_" + str(uuid.uuid4())[:8] + os.path.splitext(f.filename)[1])
    dest_path = _default_mannequin_path()
    try:
        f.save(tmp_path)
        if not _crop_image_to_34(tmp_path, dest_path):
            if os.path.isfile(tmp_path):
                os.remove(tmp_path)
            return jsonify({"ok": False, "error": "Görsel işlenemedi (3:4 kırpma). Pillow kurulu mu?"}), 500
    finally:
        if os.path.isfile(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
    logger.info("Varsayılan manken güncellendi: %s", dest_path)
    return jsonify({"ok": True, "message": "Manken görseli kaydedildi (3:4 oranına getirildi)."})


@app.route('/api/generate-tryon', methods=['POST'])
@panel_tenant_required
def api_generate_tryon():
    """
    Virtual Try-On: Kıyafet görseli yükle, Replicate IDM-VTON ile mankene giydir.
    Form: garment (file), category (elbise | ust | alt). Response: { success, output_url?, error? }
    """
    tenant = _panel_tenant()
    if not tenant:
        return jsonify({"success": False, "error": "Giriş gerekli"}), 403
    if not virtual_studio.is_configured():
        return jsonify({"success": False, "error": "REPLICATE_API_TOKEN ayarlanmamış."}), 503

    category = (request.form.get("category") or "ust").strip().lower()
    allowed_cats = ("elbise", "ust", "alt", "bluz", "gomlek", "ceket", "pantolon", "etek")
    if category not in allowed_cats:
        category = "ust"

    f = request.files.get("garment") or request.files.get("image") or request.files.get("file")
    if not f or not f.filename:
        return jsonify({"success": False, "error": "Kıyafet görseli yükleyin."}), 400

    ext = os.path.splitext(f.filename)[1] or ".jpg"
    if ext.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
        ext = ".jpg"
    name = str(uuid.uuid4()) + ext
    upload_dir = os.path.join(app.root_path, "static", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, name)
    try:
        f.save(filepath)
    except Exception as e:
        logger.warning("Try-on upload save: %s", e)
        return jsonify({"success": False, "error": "Dosya kaydedilemedi."}), 500

    base_url = (BASE_URL or request.host_url or "").rstrip("/")
    if not base_url:
        return jsonify({"success": False, "error": "BASE_URL veya public URL gerekli (Replicate görseli indirebilmeli)."}), 503
    garment_url = f"{base_url}/static/uploads/{name}"
    garment_instruction = (request.form.get("description") or request.form.get("garment_instruction") or "").strip()

    # Bu deneme için manken: formdan URL gelirse onu kullan, yoksa varsayılan (panel yüklemesi / env / sabit)
    human_img = (request.form.get("mannequin_url") or request.form.get("human_img") or "").strip()
    if not human_img:
        human_img = (virtual_studio.DEFAULT_HUMAN_IMG or "").strip()
        if not human_img and os.path.isfile(_default_mannequin_path()):
            human_img = f"{base_url}/static/uploads/{DEFAULT_MANNEQUIN_FILENAME}"

    success, output_url, err = virtual_studio.process_tryon(garment_url, category, garment_instruction, human_img=human_img or None)
    if not success:
        return jsonify({"success": False, "error": err or "Virtual try-on başarısız."}), 422
    return jsonify({"success": True, "output_url": output_url})


@app.route('/dashboard/settings/whatsapp')
@panel_tenant_required
def settings_whatsapp():
    """WhatsApp Entegrasyon Sihirbazı - VIP kurulum veya manuel bilgi girişi."""
    tenant_id = session.get("tenant_id")
    current_user = get_tenant_info(tenant_id)
    whatsapp_settings = {}
    if supabase:
        try:
            r = supabase.table("tenants").select(
                "whatsapp_phone_number_id, whatsapp_waba_id, whatsapp_phone_number_id_exchange, whatsapp_access_token_exchange, bot_mode, bot_mode_sales"
            ).eq("tenant_id", tenant_id).limit(1).execute()
            if r.data and len(r.data) > 0:
                row = r.data[0]
                sales_mode = (row.get("bot_mode_sales") or row.get("bot_mode") or "live").strip().lower()
                sales_mode = sales_mode if sales_mode in ("live", "listen", "listen_analyze", "off") else "live"
                whatsapp_settings = {
                    "phone_number_id": row.get("whatsapp_phone_number_id") or "",
                    "waba_id": row.get("whatsapp_waba_id") or "",
                    "phone_number_id_exchange": row.get("whatsapp_phone_number_id_exchange") or "",
                    "access_token_exchange": row.get("whatsapp_access_token_exchange") or "",
                    "bot_mode": sales_mode,
                }
        except Exception as e:
            logger.warning(f"Tenant WhatsApp ayarlari okunamadi: {e}")
            if "bot_mode" not in (whatsapp_settings or {}):
                whatsapp_settings = (whatsapp_settings or {}) | {"bot_mode": "live"}
    if whatsapp_settings and "bot_mode" not in whatsapp_settings:
        whatsapp_settings["bot_mode"] = "live"
    vip_whatsapp_link = os.getenv("VIP_WHATSAPP_LINK", "").strip() or None
    return render_template('settings/whatsapp.html', current_user=current_user, tenant_id=tenant_id, skip_login=PANEL_SKIP_LOGIN, whatsapp_settings=whatsapp_settings, vip_whatsapp_link=vip_whatsapp_link)


@app.route('/dashboard/integrations')
@panel_tenant_required
def dashboard_integrations():
    """Entegrasyonlar sayfası: Trendyol, Hepsiburada, N11 pazaryeri ayarları."""
    tenant_id = session.get("tenant_id")
    current_user = get_tenant_info(tenant_id)
    trendyol_settings = {"seller_id": "", "api_key_set": False}
    hepsiburada_settings = {"seller_id": "", "api_key_set": False}
    n11_settings = {"seller_id": "", "api_key_set": False}
    if supabase:
        try:
            r = supabase.table("tenants").select(
                "trendyol_seller_id, trendyol_api_key, hepsiburada_seller_id, hepsiburada_api_key, n11_seller_id, n11_api_key"
            ).eq("tenant_id", tenant_id).limit(1).execute()
            if r.data and len(r.data) > 0:
                row = r.data[0]
                trendyol_settings["seller_id"] = (row.get("trendyol_seller_id") or "").strip()
                trendyol_settings["api_key_set"] = bool((row.get("trendyol_api_key") or "").strip())
                hepsiburada_settings["seller_id"] = (row.get("hepsiburada_seller_id") or "").strip()
                hepsiburada_settings["api_key_set"] = bool((row.get("hepsiburada_api_key") or "").strip())
                n11_settings["seller_id"] = (row.get("n11_seller_id") or "").strip()
                n11_settings["api_key_set"] = bool((row.get("n11_api_key") or "").strip())
        except Exception as e:
            logger.warning(f"Pazaryeri ayarlari okunamadi: {e}")
    return render_template(
        'dashboard/integrations.html',
        current_user=current_user,
        tenant_id=tenant_id,
        skip_login=PANEL_SKIP_LOGIN,
        trendyol_settings=trendyol_settings,
        hepsiburada_settings=hepsiburada_settings,
        n11_settings=n11_settings,
    )


@app.route('/dashboard/trendyol')
@panel_tenant_required
def dashboard_trendyol():
    """Trendyol Ana Kokpiti: gerçek API ile siparişler, özet kartlar. Hata olursa çökmez."""
    tenant_id = session.get("tenant_id")
    current_user = get_tenant_info(tenant_id)
    orders = []
    trendyol_stats = None
    trendyol_api_error = None
    try:
        orders, trendyol_stats, trendyol_api_error = get_trendyol_orders(tenant_id, supabase)
    except Exception as e:
        orders = []
        trendyol_stats = None
        trendyol_api_error = "API bağlantısı kurulamadı. Lütfen API Ayarları sayfasından bilgilerinizi kontrol edin."
    return render_template(
        'dashboard/trendyol_dashboard.html',
        current_user=current_user,
        tenant_id=tenant_id,
        skip_login=PANEL_SKIP_LOGIN,
        orders=orders,
        trendyol_stats=trendyol_stats,
        trendyol_api_error=trendyol_api_error,
    )


@app.route('/dashboard/hepsiburada')
@panel_tenant_required
def dashboard_hepsiburada():
    """Hepsiburada Ana Kokpiti: siparişler, özet kartlar. Hata olursa çökmez."""
    tenant_id = session.get("tenant_id")
    current_user = get_tenant_info(tenant_id)
    orders = []
    hepsiburada_stats = None
    hepsiburada_api_error = None
    try:
        orders, hepsiburada_stats, hepsiburada_api_error = get_hepsiburada_orders(tenant_id, supabase)
    except Exception:
        orders = []
        hepsiburada_stats = None
        hepsiburada_api_error = "API bağlantısı kurulamadı. Lütfen API Ayarları sayfasından bilgilerinizi kontrol edin."
    return render_template(
        'dashboard/hepsiburada_dashboard.html',
        current_user=current_user,
        tenant_id=tenant_id,
        skip_login=PANEL_SKIP_LOGIN,
        orders=orders,
        hepsiburada_stats=hepsiburada_stats,
        hepsiburada_api_error=hepsiburada_api_error,
    )


@app.route('/dashboard/n11')
@panel_tenant_required
def dashboard_n11():
    """N11 Ana Kokpiti: siparişler, özet kartlar. Hata olursa çökmez."""
    tenant_id = session.get("tenant_id")
    current_user = get_tenant_info(tenant_id)
    orders = []
    n11_stats = None
    n11_api_error = None
    try:
        orders, n11_stats, n11_api_error = get_n11_orders(tenant_id, supabase)
    except Exception:
        orders = []
        n11_stats = None
        n11_api_error = "API bağlantısı kurulamadı. Lütfen API Ayarları sayfasından bilgilerinizi kontrol edin."
    return render_template(
        'dashboard/n11_dashboard.html',
        current_user=current_user,
        tenant_id=tenant_id,
        skip_login=PANEL_SKIP_LOGIN,
        orders=orders,
        n11_stats=n11_stats,
        n11_api_error=n11_api_error,
    )


# --- API (PANEL ICIN) ---

def _panel_tenant():
    """Panel tenant: giris varsa onu, PANEL_SKIP_LOGIN ise tuba kullan."""
    if session.get("tenant_id"):
        return session["tenant_id"]
    if PANEL_SKIP_LOGIN:
        return "tuba"
    return None

def _hat_to_line(hat):
    """Panel hat parametresi -> DB line: satis -> sales, iade -> exchange."""
    h = (hat or "").strip().lower()
    if h == "iade":
        return "exchange"
    return "sales"


@app.route('/api/customers', methods=['GET'])
def get_customers():
    """Panel: tenant'in mesajlari. hat=satis -> satış hattı, hat=iade -> değişim hattı (line ile filtre)."""
    tenant = _panel_tenant()
    if not tenant:
        return jsonify({"error": "Giriş gerekli"}), 403
    if not supabase:
        return jsonify([])
    hat = (request.args.get("hat") or "satis").strip().lower()
    line = _hat_to_line(hat)
    try:
        q = supabase.table('messages').select("*").eq('tenant_id', tenant).eq('line', line).order('created_at', desc=True).limit(50)
        response = q.execute()
        return jsonify(response.data or [])
    except Exception as e:
        logger.error(f"API hatasi: {e}")
        return jsonify({"error": str(e)})

@app.route('/api/send-message', methods=['POST'])
def send_message_api():
    """Panelden yazilan mesaji WhatsApp'a gonderir. hat ile hangi numaradan gideceği belirlenir (satış/değişim)."""
    tenant = _panel_tenant()
    if not tenant:
        return jsonify({"error": "Giriş gerekli"}), 403
    data = request.json
    phone = data.get('phone')
    text = data.get('text')
    hat = (data.get('hat') or "satis").strip().lower()
    line = _hat_to_line(hat)
    if not phone or not text:
        return jsonify({"error": "Eksik bilgi"}), 400

    success, err_msg = send_whatsapp_message(phone, text, tenant_id=tenant, line=line)
    if success and supabase:
        supabase.table('messages').insert({
            "phone": phone,
            "message_body": text,
            "direction": "outbound",
            "tenant_id": tenant,
            "line": line,
        }).execute()
        try:
            supabase.table('conversation_state').delete().eq('tenant_id', tenant).eq('phone', phone).execute()
        except Exception as e:
            logger.debug(f"conversation_state clear atlandi: {e}")
    if success:
        return jsonify({"status": True})
    return jsonify({"status": False, "error": err_msg or "Mesaj gönderilemedi."})

def _validate_whatsapp_credentials(phone_number_id: str, access_token: str):
    """Meta Graph API ile token ve phone_number_id dogrula. (success, error_message) dondurur."""
    if not phone_number_id or not access_token:
        return False, "Telefon Numarası ID ve token gerekli."
    url = f"https://graph.facebook.com/v21.0/{phone_number_id}"
    try:
        r = requests.get(url, params={"access_token": access_token}, timeout=10)
        data = r.json() if r.text else {}
        if r.status_code != 200:
            err = data.get("error", {})
            return False, err.get("message", "Token veya Phone Number ID geçersiz.")
        if not data.get("id"):
            return False, "Geçerli bir telefon numarası bilgisi alınamadı."
        return True, ""
    except Exception as e:
        logger.exception(f"WhatsApp API dogrulama hatasi: {e}")
        return False, str(e)

@app.route('/api/save-whatsapp-settings', methods=['POST'])
def api_save_whatsapp_settings():
    """WhatsApp bilgilerini test et ve tenants tablosuna kaydet."""
    tenant = _panel_tenant()
    if not tenant:
        return jsonify({"error": "Giriş gerekli"}), 403
    data = request.json or {}
    phone_number_id = (data.get("phone_number_id") or "").strip()
    waba_id = (data.get("waba_id") or "").strip() or None
    access_token = (data.get("access_token") or "").strip()
    phone_number_id_exchange = (data.get("phone_number_id_exchange") or "").strip() or None
    access_token_exchange = (data.get("access_token_exchange") or "").strip() or None
    if not phone_number_id or not access_token:
        return jsonify({"error": "Telefon Numarası ID ve Kalıcı Erişim Jetonu zorunludur."}), 400
    ok, err_msg = _validate_whatsapp_credentials(phone_number_id, access_token)
    if not ok:
        return jsonify({"error": err_msg}), 400
    if phone_number_id_exchange and access_token_exchange:
        ok_ex, err_ex = _validate_whatsapp_credentials(phone_number_id_exchange, access_token_exchange)
        if not ok_ex:
            return jsonify({"error": "Değişim hattı: " + err_ex}), 400
    if supabase:
        try:
            update_payload = {
                "whatsapp_phone_number_id": phone_number_id,
                "whatsapp_waba_id": waba_id,
                "whatsapp_access_token": access_token,
            }
            if "phone_number_id_exchange" in data:
                update_payload["whatsapp_phone_number_id_exchange"] = phone_number_id_exchange
            if "access_token_exchange" in data:
                update_payload["whatsapp_access_token_exchange"] = access_token_exchange
            if "bot_mode" in data:
                bm = (data.get("bot_mode") or "live").strip().lower()
                if bm in ("live", "listen", "listen_analyze"):
                    update_payload["bot_mode"] = bm
            supabase.table("tenants").update(update_payload).eq("tenant_id", tenant).execute()
            logger.info(f"WhatsApp ayarlari kaydedildi: tenant={tenant}")
        except Exception as e:
            logger.exception(f"Tenants guncelleme hatasi: {e}")
            return jsonify({"error": "Kayıt sırasında hata oluştu."}), 500
    return jsonify({"success": True, "message": "Bağlantı doğrulandı ve kaydedildi."})


@app.route('/api/save-trendyol-keys', methods=['POST'])
def api_save_trendyol_keys():
    """Trendyol Satıcı ID, API Key ve API Secret bilgilerini tenants tablosuna kaydeder."""
    tenant = _panel_tenant()
    if not tenant:
        return jsonify({"error": "Giriş gerekli"}), 403
    data = request.json or {}
    seller_id = (data.get("trendyol_seller_id") or "").strip() or None
    api_key = (data.get("trendyol_api_key") or "").strip() or None
    api_secret = (data.get("trendyol_api_secret") or "").strip() or None
    if supabase:
        try:
            update_payload = {
                "trendyol_seller_id": seller_id,
                "trendyol_api_key": api_key,
                "trendyol_api_secret": api_secret,
            }
            supabase.table("tenants").update(update_payload).eq("tenant_id", tenant).execute()
            logger.info(f"Trendyol ayarlari kaydedildi: tenant={tenant}")
        except Exception as e:
            logger.exception(f"Trendyol tenants guncelleme hatasi: {e}")
            return jsonify({"success": False, "error": "Kayıt sırasında hata oluştu."}), 500
    return jsonify({"success": True, "message": "Trendyol bilgileri kaydedildi."})


@app.route('/api/save-hepsiburada-keys', methods=['POST'])
def api_save_hepsiburada_keys():
    """Hepsiburada Satıcı ID, API Key ve API Secret bilgilerini tenants tablosuna kaydeder."""
    tenant = _panel_tenant()
    if not tenant:
        return jsonify({"error": "Giriş gerekli"}), 403
    data = request.json or {}
    seller_id = (data.get("hepsiburada_seller_id") or "").strip() or None
    api_key = (data.get("hepsiburada_api_key") or "").strip() or None
    api_secret = (data.get("hepsiburada_api_secret") or "").strip() or None
    if supabase:
        try:
            update_payload = {
                "hepsiburada_seller_id": seller_id,
                "hepsiburada_api_key": api_key,
                "hepsiburada_api_secret": api_secret,
            }
            supabase.table("tenants").update(update_payload).eq("tenant_id", tenant).execute()
            logger.info(f"Hepsiburada ayarlari kaydedildi: tenant={tenant}")
        except Exception as e:
            logger.exception(f"Hepsiburada tenants guncelleme hatasi: {e}")
            return jsonify({"success": False, "error": "Kayıt sırasında hata oluştu."}), 500
    return jsonify({"success": True, "message": "Hepsiburada bilgileri kaydedildi."})


@app.route('/api/save-n11-keys', methods=['POST'])
def api_save_n11_keys():
    """N11 Satıcı ID, API Key ve API Secret bilgilerini tenants tablosuna kaydeder."""
    tenant = _panel_tenant()
    if not tenant:
        return jsonify({"error": "Giriş gerekli"}), 403
    data = request.json or {}
    seller_id = (data.get("n11_seller_id") or "").strip() or None
    api_key = (data.get("n11_api_key") or "").strip() or None
    api_secret = (data.get("n11_api_secret") or "").strip() or None
    if supabase:
        try:
            update_payload = {
                "n11_seller_id": seller_id,
                "n11_api_key": api_key,
                "n11_api_secret": api_secret,
            }
            supabase.table("tenants").update(update_payload).eq("tenant_id", tenant).execute()
            logger.info(f"N11 ayarlari kaydedildi: tenant={tenant}")
        except Exception as e:
            logger.exception(f"N11 tenants guncelleme hatasi: {e}")
            return jsonify({"success": False, "error": "Kayıt sırasında hata oluştu."}), 500
    return jsonify({"success": True, "message": "N11 bilgileri kaydedildi."})


@app.route('/api/bot-mode', methods=['GET'])
def api_get_bot_mode():
    """Hat bazlı bot modlarını döner: { sales: 'live'|'listen_analyze'|'off', exchange: ... }."""
    tenant = _panel_tenant()
    if not tenant:
        return jsonify({"error": "Giriş gerekli"}), 403
    sales = get_tenant_bot_mode_for_line(tenant, "sales")
    exchange = get_tenant_bot_mode_for_line(tenant, "exchange")
    return jsonify({"sales": sales, "exchange": exchange})


@app.route('/api/bot-mode', methods=['POST'])
def api_set_bot_mode():
    """Hat bazlı bot modunu günceller. Body: { line: 'sales'|'exchange', mode: 'live'|'listen_analyze'|'off' }."""
    tenant = _panel_tenant()
    if not tenant:
        return jsonify({"error": "Giriş gerekli"}), 403
    data = request.json or {}
    line = (data.get("line") or "").strip().lower()
    mode = (data.get("mode") or "live").strip().lower()
    if line not in ("sales", "exchange"):
        return jsonify({"error": "line: sales veya exchange olmalı."}), 400
    if mode not in ("live", "listen_analyze", "off"):
        return jsonify({"error": "mode: live, listen_analyze veya off olmalı."}), 400
    col = "bot_mode_sales" if line == "sales" else "bot_mode_exchange"
    if supabase:
        try:
            supabase.table("tenants").update({col: mode}).eq("tenant_id", tenant).execute()
            logger.info(f"Bot modu güncellendi: tenant={tenant} line={line} mode={mode}")
        except Exception as e:
            err = str(e).lower()
            logger.exception(f"Bot mode güncelleme: {e}")
            if "column" in err and ("does not exist" in err or "mevcut değil" in err):
                return jsonify({"success": False, "error": "Veritabanı güncellemesi gerekli. Supabase SQL Editor'da supabase_bot_mode_per_line.sql dosyasını çalıştırın."}), 400
            return jsonify({"success": False, "error": "Kayıt sırasında hata oluştu."}), 500
    return jsonify({"success": True, "line": line, "mode": mode})


@app.route('/api/save-bot-mode', methods=['POST'])
def api_save_bot_mode():
    """Geriye uyumluluk: tek mod (sales). Body: { bot_mode } veya { line, mode }."""
    tenant = _panel_tenant()
    if not tenant:
        return jsonify({"error": "Giriş gerekli"}), 403
    data = request.json or {}
    if "line" in data and "mode" in data:
        return api_set_bot_mode()
    bm = (data.get("bot_mode") or "live").strip().lower()
    if bm not in ("live", "listen", "listen_analyze", "off"):
        bm = "live"
    if bm == "listen":
        bm = "listen_analyze"
    if supabase:
        try:
            supabase.table("tenants").update({"bot_mode_sales": bm}).eq("tenant_id", tenant).execute()
            logger.info(f"Bot modu (sales) güncellendi: tenant={tenant} mode={bm}")
        except Exception as e:
            logger.exception(f"Bot mode güncelleme: {e}")
            return jsonify({"error": "Kayıt sırasında hata oluştu."}), 500
    return jsonify({"success": True, "message": "Bot modu kaydedildi."})


@app.route('/api/analiz-raporu', methods=['GET'])
def api_analiz_raporu():
    """Dinle+Analiz döneminde kaydedilen analizleri döner (son N gün). Rapor sayfasında kullanılır."""
    tenant = _panel_tenant()
    if not tenant:
        return jsonify({"error": "Giriş gerekli"}), 403
    days = int(request.args.get("days") or "2")
    days = max(1, min(30, days))
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    if not supabase:
        return jsonify({"items": [], "summary": {"total": 0, "by_line": {}, "by_intent": {}, "by_sentiment": {}}})
    try:
        r = supabase.table("message_analyses").select("*").eq("tenant_id", tenant).gte("created_at", since).order("created_at", desc=True).limit(500).execute()
        items = r.data or []
        by_line = {"sales": 0, "exchange": 0}
        by_intent = {}
        by_sentiment = {}
        for row in items:
            ln = (row.get("line") or "sales").strip().lower()
            if ln in by_line:
                by_line[ln] += 1
            intent = (row.get("intent") or "—").strip() or "—"
            by_intent[intent] = by_intent.get(intent, 0) + 1
            sent = (row.get("sentiment") or "—").strip() or "—"
            by_sentiment[sent] = by_sentiment.get(sent, 0) + 1
        summary = {"total": len(items), "by_line": by_line, "by_intent": by_intent, "by_sentiment": by_sentiment}
        return jsonify({"items": items, "summary": summary})
    except Exception as e:
        logger.warning(f"analiz-raporu: {e}")
        return jsonify({"items": [], "summary": {"total": 0, "by_line": {}, "by_intent": {}, "by_sentiment": {}}})


@app.route('/api/handoffs', methods=['GET'])
def api_handoffs():
    """Panel: Bu tenant için 'bot yetkiliye yönlendirdi' işaretli numaralar (manuel geçiş uyarısı)."""
    tenant = _panel_tenant()
    if not tenant:
        return jsonify({"error": "Giriş gerekli"}), 403
    if not supabase:
        return jsonify({"handoff_phones": []})
    try:
        r = supabase.table('conversation_state').select('phone').eq('tenant_id', tenant).execute()
        phones = [row.get('phone') for row in (r.data or []) if row.get('phone')]
        return jsonify({"handoff_phones": phones})
    except Exception as e:
        logger.warning(f"handoffs API: {e}")
        return jsonify({"handoff_phones": []})

@app.route('/api/update-customer-status', methods=['POST'])
@panel_tenant_required
def api_update_customer_status():
    """Satış panosu: sürükle-bırak ile müşteri aşaması güncelle (new, interested, negotiation, won)."""
    tenant = _panel_tenant()
    if not tenant:
        return jsonify({"error": "Giriş gerekli"}), 403
    data = request.get_json(force=True, silent=True) or {}
    customer_id = data.get("customer_id")
    status = (data.get("status") or "").strip().lower()
    if status not in ("new", "interested", "negotiation", "won", "return"):
        return jsonify({"error": "Geçersiz status"}), 400
    if not customer_id and not data.get("phone"):
        return jsonify({"error": "customer_id veya phone gerekli"}), 400
    if not supabase:
        return jsonify({"error": "Veritabanı kullanılamıyor"}), 503
    try:
        if customer_id:
            check = supabase.table("customers").select("id, tenant_id").eq("id", int(customer_id)).limit(1).execute()
            if not check.data or len(check.data) == 0 or check.data[0].get("tenant_id") != tenant:
                return jsonify({"error": "Müşteri bulunamadı veya yetkisiz"}), 404
            supabase.table("customers").update({"status": status}).eq("id", int(customer_id)).eq("tenant_id", tenant).execute()
        else:
            phone = (data.get("phone") or "").strip()
            if not phone:
                return jsonify({"error": "phone gerekli"}), 400
            supabase.table("customers").update({"status": status}).eq("tenant_id", tenant).eq("phone", phone).execute()
        return jsonify({"ok": True, "status": status})
    except Exception as e:
        logger.exception("update-customer-status: %s", e)
        return jsonify({"error": "Güncelleme yapılamadı"}), 500

@app.route('/api/dashboard/last-messages', methods=['GET'])
def api_last_messages():
    """Dashboard canli akis: son 5 mesaj (tenant'a gore)."""
    tenant = _panel_tenant()
    if not tenant:
        return jsonify({"error": "Giriş gerekli"}), 403
    if not supabase:
        return jsonify([])
    try:
        q = supabase.table('messages').select("phone, message_body, direction, created_at").eq('tenant_id', tenant).order('created_at', desc=True).limit(5)
        r = q.execute()
        return jsonify(r.data or [])
    except Exception as e:
        logger.error(f"Dashboard last-messages: {e}")
        return jsonify([])

@app.route('/api/dashboard/kpis', methods=['GET'])
def api_kpis():
    """Dashboard KPI: toplam ciro, aktif sohbet, bekleyen iade, AI maliyeti. Ilk asama mock/hesapli."""
    tenant = _panel_tenant()
    if not tenant:
        return jsonify({"error": "Giriş gerekli"}), 403
    try:
        # Aktif sohbet: son 50 mesajdaki benzersiz numara sayisi
        active_chats = 0
        if supabase:
            r = supabase.table('messages').select('phone').eq('tenant_id', tenant).order('created_at', desc=True).limit(50).execute()
            phones = set((m.get('phone') for m in (r.data or [])))
            active_chats = len(phones)
        return jsonify({
            "toplam_ciro": 0,       # Ileride ButikSistem veya baska kaynak
            "aktif_sohbetler": active_chats,
            "bekleyen_iadeler": 0, # Ileride iade takibi
            "ai_maliyeti": 0       # Ileride token/session maliyeti
        })
    except Exception as e:
        logger.error(f"Dashboard KPIs: {e}")
        return jsonify({"toplam_ciro": 0, "aktif_sohbetler": 0, "bekleyen_iadeler": 0, "ai_maliyeti": 0})

@app.route('/api/check-model', methods=['GET'])
def api_check_model():
    """Claude modelinin kullanilabilir olup olmadigini kontrol et. Key gosterilmez; sadece configured true/false."""
    key = os.getenv("ANTHROPIC_API_KEY") or ""
    configured = bool(key.strip() and key.strip() != "sk-ant-test")
    return jsonify({
        "claude_configured": configured,
        "message": "Claude kullanilabilir." if configured else "ANTHROPIC_API_KEY eksik veya test. Railway -> Variables -> ANTHROPIC_API_KEY ekle."
    })


@app.route('/api/support-chat', methods=['POST'])
def api_support_chat():
    """Web sitesi (ziyaretçi) ve panel (teknik destek) chatbot cevabı. Aynı Claude modeli, context'e göre farklı prompt."""
    try:
        data = request.get_json() or {}
        message = (data.get("message") or "").strip()
        context = (data.get("context") or "website").lower()
        if context not in ("website", "panel"):
            context = "website"
        if not message:
            return jsonify({"ok": False, "reply": "Lütfen bir mesaj yazın."}), 400

        session_key = "support_chat_website" if context == "website" else "support_chat_panel"
        history = list(session.get(session_key) or [])
        history.append({"role": "user", "content": message})
        if len(history) > 11:
            history = history[-11:]

        reply = get_support_reply(message, context, history[:-1], supabase=supabase)

        history.append({"role": "assistant", "content": reply})
        if len(history) > 11:
            history = history[-11:]
        session[session_key] = history
        session.modified = True

        return jsonify({"ok": True, "reply": reply})
    except Exception as e:
        logger.exception("support-chat: %s", e)
        return jsonify({"ok": False, "reply": "Bir hata oluştu. Lütfen tekrar deneyin."}), 500


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
    
    try:
        entry = data['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']
        
        if 'messages' not in value:
            return jsonify({"status": "ok"}), 200
        
        message = value['messages'][0]
        sender_phone = message['from']
        msg_body = message['text']['body'] if 'text' in message else "Medya/Diger"
        metadata = value.get('metadata', {})
        phone_number_id = metadata.get('phone_number_id') or PHONE_ID
        tenant_id, line = phone_id_to_tenant_and_line(phone_number_id)
        # Tek numara test modu: Değişim hattı numarası yoksa, mesaj iade/değişim gibi görünüyorsa exchange say (canlıda iki numara olunca numaraya göre belirlenir)
        if line == "sales" and not tenant_has_exchange_number(tenant_id) and message_looks_like_exchange(msg_body):
            line = "exchange"
            logger.info(f"📩 [Tek numara test] Mesaj iade/değişim gibi → line=exchange (tenant={tenant_id})")

        logger.info(f"📩 Mesaj Geldi: {sender_phone} - {msg_body} (tenant={tenant_id} hat={line})")

        # 1. Supabase'e Kaydet (Gelen Mesaj, tenant_id + line ile; satış/değişim hattı ayrımı)
        if supabase:
            supabase.table('messages').insert({
                "phone": sender_phone,
                "message_body": msg_body,
                "direction": "inbound",
                "tenant_id": tenant_id,
                "line": line,
            }).execute()
            # Yeni müşteri: bu tenant + telefon + line ilk kez geliyorsa customers'a ekle
            try:
                existing = supabase.table('customers').select('id').eq('tenant_id', tenant_id).eq('phone', sender_phone).eq('line', line).limit(1).execute()
                if not (existing.data and len(existing.data) > 0):
                    supabase.table('customers').insert({
                        "tenant_id": tenant_id,
                        "phone": sender_phone,
                        "line": line,
                        "status": "new",
                    }).execute()
                    logger.info(f"[Yeni müşteri] tenant={tenant_id} phone={sender_phone} line={line}")
            except Exception as e:
                logger.warning(f"customers insert atlandi: {e}")

        # Hat bazlı bot modu: off = sadece kaydet, listen_analyze = analiz et cevap yok, live = cevap ver
        bot_mode = get_tenant_bot_mode_for_line(tenant_id, line)
        send_replies = (bot_mode == "live")
        if bot_mode == "off":
            logger.info(f"[Webhook] Bot modu=off (hat={line}): mesaj kaydedildi, cevap gönderilmiyor (tenant={tenant_id})")
            return jsonify({"status": "received"}), 200

        # 1a0. Satış hattı: Mesaj net "ürün almak istiyorum + kargo/kapıda" ise AI beklemeden hemen kargo bilgisi iste ve pending'e al (satış zaten belli, kargolama aşamasına geç).
        if line == "sales" and supabase and msg_body:
            try:
                already_pending = False
                r_check = supabase.table("sales_cargo_pending").select("tenant_id").eq("tenant_id", tenant_id).eq("phone", sender_phone).limit(1).execute()
                if r_check.data and len(r_check.data) > 0:
                    already_pending = True
                if not already_pending and message_looks_like_purchase_and_cargo(msg_body):
                    if send_replies:
                        send_whatsapp_message(sender_phone, SALES_CARGO_INFO_REQUEST, tenant_id=tenant_id, line=line)
                        supabase.table("messages").insert({
                            "phone": sender_phone, "message_body": SALES_CARGO_INFO_REQUEST,
                            "direction": "outbound", "tenant_id": tenant_id, "line": line,
                        }).execute()
                    supabase.table("sales_cargo_pending").upsert(
                        [{"tenant_id": tenant_id, "phone": sender_phone}],
                        on_conflict="tenant_id,phone"
                    ).execute()
                    logger.info(f"[Satış kargo] Erken tetik: satış+kargo niyeti algılandı" + (" kargo bilgisi istendi" if send_replies else " (cevap gönderilmedi)") + f": tenant={tenant_id} phone={sender_phone}")
                    return jsonify({"status": "received"}), 200
            except Exception as e:
                logger.warning(f"sales_cargo erken tetik atlandi: {e}")

        # 1a. Değişim kargo: sadece değişim hattından gelen mesajlarda (adres son siparişten; onayda Butik'e sipariş).
        if line == "exchange" and supabase and msg_body:
            try:
                r_ex = supabase.table("exchange_cargo_pending").select("tenant_id, phone, parsed_data").eq("tenant_id", tenant_id).eq("phone", sender_phone).limit(1).execute()
                if r_ex.data and len(r_ex.data) > 0:
                    row_ex = r_ex.data[0]
                    parsed_ex = row_ex.get("parsed_data")

                    if parsed_ex is None:
                        # Son adres kullanılacak; onay veya yeni adres bekleniyor
                        if is_cargo_confirmation(msg_body):
                            last = butik_client.get_last_order_delivery_and_variant(sender_phone) if butik_client else None
                            if not last or not last.get("delivery"):
                                cevap_ex = "❌ Son sipariş adresiniz bulunamadı. Lütfen yetkilimizle iletişime geçin."
                            elif not last.get("variant_id"):
                                cevap_ex = "❌ Sipariş detayı alınamadı. Lütfen yetkilimizle iletişime geçin."
                            else:
                                d = last["delivery"]
                                billing = {**d}
                                custom_id = f"WA-EX-{tenant_id}-{sender_phone[-6:]}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}"
                                pay_id = _resolve_payment_type_id(butik_client, "kapıda_nakit")
                                result = butik_client.create_order(
                                    custom_order_id=custom_id,
                                    delivery=d,
                                    billing=billing,
                                    items=[{"variantId": last["variant_id"], "quantity": 1}],
                                    order_payment_type_id=pay_id,
                                    order_shipping_value=CARGO_SHIPPING_VALUE,
                                    order_products_value=0,
                                    description=f"WhatsApp değişim {sender_phone}",
                                    who_pays_shipping="recipient",
                                )
                                if result.get("ok"):
                                    supabase.table("exchange_cargo_pending").delete().eq("tenant_id", tenant_id).eq("phone", sender_phone).execute()
                                    cevap_ex = f"✅ Kargonuz oluşturuldu (Sipariş no: {result.get('custom_order_id', '')}). Kargo ücreti teslimatta alınacaktır. En kısa sürede kargoya verilecektir. 🌸"
                                    logger.info(f"[Değişim kargo] Butik sipariş: {result.get('order_id')} tenant={tenant_id} phone={sender_phone}")
                                else:
                                    cevap_ex = "❌ Kargo oluşturulurken hata. Lütfen yetkilimizle iletişime geçin."
                                    logger.warning(f"[Değişim kargo] order/add: {result.get('error')}")
                            if send_replies:
                                send_whatsapp_message(sender_phone, cevap_ex, tenant_id=tenant_id, line=line)
                                supabase.table("messages").insert({"phone": sender_phone, "message_body": cevap_ex, "direction": "outbound", "tenant_id": tenant_id, "line": line}).execute()
                            return jsonify({"status": "received"}), 200
                        if wants_different_address(msg_body):
                            cevap_ex = "📋 Yeni adresinizi yazın: İl, İlçe, Açık adres (örn: Ankara Çankaya ... Mah. No: X)"
                            if send_replies:
                                send_whatsapp_message(sender_phone, cevap_ex, tenant_id=tenant_id, line=line)
                                supabase.table("messages").insert({"phone": sender_phone, "message_body": cevap_ex, "direction": "outbound", "tenant_id": tenant_id, "line": line}).execute()
                            return jsonify({"status": "received"}), 200
                        parsed_addr = parse_cargo_message(msg_body)
                        if address_only_sufficient(parsed_addr):
                            last = butik_client.get_last_order_delivery_and_variant(sender_phone) if butik_client else None
                            d = last.get("delivery") if last else {}
                            delivery_save = {
                                "name": (parsed_addr.get("name") or d.get("name") or "Müşteri").strip(),
                                "surname": (parsed_addr.get("surname") or d.get("surName") or "").strip(),
                                "phone": (parsed_addr.get("phone") or sender_phone or "").strip(),
                                "city": (parsed_addr.get("city") or "").strip(),
                                "district": (parsed_addr.get("district") or "").strip(),
                                "address": (parsed_addr.get("address") or f"{parsed_addr.get('city') or ''} {parsed_addr.get('district') or ''}").strip(),
                            }
                            supabase.table("exchange_cargo_pending").update({"parsed_data": delivery_save}).eq("tenant_id", tenant_id).eq("phone", sender_phone).execute()
                            adres_ozet = f"{delivery_save.get('city') or ''} {delivery_save.get('district') or ''} {delivery_save.get('address') or ''}".strip()
                            cevap_ex = f"📋 Bu adrese gönderilecek:\n{adres_ozet}\n\nOnaylıyor musunuz? 'Tamam' veya 'Gönderin' yazın. 🌸"
                            if send_replies:
                                send_whatsapp_message(sender_phone, cevap_ex, tenant_id=tenant_id, line=line)
                                supabase.table("messages").insert({"phone": sender_phone, "message_body": cevap_ex, "direction": "outbound", "tenant_id": tenant_id, "line": line}).execute()
                            return jsonify({"status": "received"}), 200
                        cevap_ex = "Kargonuz son sipariş adresinize gönderilecek. Onaylıyor musunuz? 'Tamam' veya 'Gönderin' yazın. Farklı adrese göndermek isterseniz yeni adresinizi yazın. 🌸"
                        if send_replies:
                            send_whatsapp_message(sender_phone, cevap_ex, tenant_id=tenant_id, line=line)
                            supabase.table("messages").insert({"phone": sender_phone, "message_body": cevap_ex, "direction": "outbound", "tenant_id": tenant_id, "line": line}).execute()
                        return jsonify({"status": "received"}), 200

                    # parsed_data dolu: yeni adres kaydedilmiş, onay bekleniyor
                    if is_cargo_confirmation(msg_body):
                        delivery_ex = parsed_ex if isinstance(parsed_ex, dict) else (json.loads(parsed_ex) if isinstance(parsed_ex, str) else {})
                        if not delivery_ex:
                            cevap_ex = "❌ Adres bilgisi alınamadı. Lütfen adresinizi tekrar yazın."
                        else:
                            last = butik_client.get_last_order_delivery_and_variant(sender_phone) if butik_client else None
                            variant_id = last.get("variant_id") if last else None
                            if not variant_id:
                                cevap_ex = "❌ Sipariş detayı alınamadı. Lütfen yetkilimizle iletişime geçin."
                            else:
                                d = {
                                    "name": (delivery_ex.get("name") or "Müşteri").strip(),
                                    "surName": (delivery_ex.get("surname") or delivery_ex.get("surName") or "").strip(),
                                    "phone": (delivery_ex.get("phone") or sender_phone or "").strip(),
                                    "city": (delivery_ex.get("city") or "").strip(),
                                    "district": (delivery_ex.get("district") or "").strip(),
                                    "address": (delivery_ex.get("address") or "").strip(),
                                }
                                billing = {**d}
                                custom_id = f"WA-EX-{tenant_id}-{sender_phone[-6:]}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}"
                                pay_id = _resolve_payment_type_id(butik_client, "kapıda_nakit")
                                result = butik_client.create_order(
                                    custom_order_id=custom_id,
                                    delivery=d,
                                    billing=billing,
                                    items=[{"variantId": variant_id, "quantity": 1}],
                                    order_payment_type_id=pay_id,
                                    order_shipping_value=CARGO_SHIPPING_VALUE,
                                    order_products_value=0,
                                    description=f"WhatsApp değişim {sender_phone}",
                                    who_pays_shipping="recipient",
                                )
                                if result.get("ok"):
                                    supabase.table("exchange_cargo_pending").delete().eq("tenant_id", tenant_id).eq("phone", sender_phone).execute()
                                    cevap_ex = f"✅ Kargonuz oluşturuldu (Sipariş no: {result.get('custom_order_id', '')}). Kargo ücreti teslimatta alınacaktır. En kısa sürede kargoya verilecektir. 🌸"
                                    logger.info(f"[Değişim kargo] Butik sipariş (yeni adres): {result.get('order_id')} tenant={tenant_id} phone={sender_phone}")
                                else:
                                    cevap_ex = "❌ Kargo oluşturulurken hata. Lütfen yetkilimizle iletişime geçin."
                                    logger.warning(f"[Değişim kargo] order/add: {result.get('error')}")
                        if send_replies:
                            send_whatsapp_message(sender_phone, cevap_ex, tenant_id=tenant_id, line=line)
                            supabase.table("messages").insert({"phone": sender_phone, "message_body": cevap_ex, "direction": "outbound", "tenant_id": tenant_id, "line": line}).execute()
                        return jsonify({"status": "received"}), 200
                    cevap_ex = "Siparişi onaylamak için 'Tamam' veya 'Gönderin' yazın. 🌸"
                    if send_replies:
                        send_whatsapp_message(sender_phone, cevap_ex, tenant_id=tenant_id, line=line)
                        supabase.table("messages").insert({"phone": sender_phone, "message_body": cevap_ex, "direction": "outbound", "tenant_id": tenant_id, "line": line}).execute()
                    return jsonify({"status": "received"}), 200
            except Exception as e:
                logger.warning(f"exchange_cargo_pending isleme atlandi: {e}")

        # 1b. Satış kargo: sadece satış hattından gelen mesajlarda (peşin/kapıda/havale; onayda Butik'e sipariş).
        if line == "sales" and supabase and msg_body:
            try:
                r = supabase.table("sales_cargo_pending").select("tenant_id, phone, parsed_data, payment_type").eq("tenant_id", tenant_id).eq("phone", sender_phone).limit(1).execute()
                if r.data and len(r.data) > 0:
                    row = r.data[0]
                    parsed_data = row.get("parsed_data")
                    payment_type_saved = (row.get("payment_type") or "").strip() or None

                    if parsed_data is None:
                        # Aşama 1: Bilgi bekleniyor
                        parsed = parse_cargo_message(msg_body)
                        if cargo_parse_sufficient(parsed):
                            pay_slug = parse_payment_type(msg_body) or "kapıda_nakit"
                            pay_label = {"kapıda_nakit": "Kapıda nakit", "kapıda_kredi": "Kapıda kredi kartı", "havale": "Havale-EFT", "peşin": "Peşin"}.get(pay_slug, "Kapıda nakit")
                            supabase.table("sales_cargo_pending").update({"parsed_data": parsed, "payment_type": pay_slug}).eq("tenant_id", tenant_id).eq("phone", sender_phone).execute()
                            adres_ozet = f"{parsed.get('city') or ''} {parsed.get('district') or ''} {parsed.get('address') or ''}".strip() or "—"
                            cevap_cargo = f"📋 Sipariş özeti:\n• {parsed.get('name')} {parsed.get('surname') or ''}\n• {parsed.get('phone')}\n• {adres_ozet}\n• Ürün: {parsed.get('product_code')} / {parsed.get('color')} / {parsed.get('size')}\n• Ödeme: {pay_label} (+50₺ kargo)\n\nOnaylıyor musunuz? 'Tamam' veya 'Gönderin' yazın; kargonuz oluşturulacak. 🌸"
                            send_whatsapp_message(sender_phone, cevap_cargo, tenant_id=tenant_id, line=line)
                            supabase.table("messages").insert({"phone": sender_phone, "message_body": cevap_cargo, "direction": "outbound", "tenant_id": tenant_id, "line": line}).execute()
                            return jsonify({"status": "received"}), 200
                        cevap_cargo = "📋 Eksik bilgi. Lütfen: Ad Soyad, Telefon, İl İlçe Açık Adres, Ürün Kodu, Renk, Beden (+ ödeme: Kapıda nakit / Kapıda kredi / Havale-EFT / Peşin)"
                        send_whatsapp_message(sender_phone, cevap_cargo, tenant_id=tenant_id, line=line)
                        supabase.table("messages").insert({"phone": sender_phone, "message_body": cevap_cargo, "direction": "outbound", "tenant_id": tenant_id, "line": line}).execute()
                        return jsonify({"status": "received"}), 200

                    # Aşama 2: Onay bekleniyor (parsed_data dolu)
                    if is_cargo_confirmation(msg_body):
                        parsed = parsed_data if isinstance(parsed_data, dict) else (json.loads(parsed_data) if isinstance(parsed_data, str) else {})
                        if not parsed:
                            cevap_cargo = "❌ Sipariş bilgisi alınamadı. Lütfen bilgilerinizi tekrar gönderin."
                        else:
                            product = butik_client.get_product_with_variants(parsed.get("product_code"))
                            if not product or not product.get("variants"):
                                cevap_cargo = "❌ Bu ürün kodu sistemde bulunamadı. Yetkilimizle görüşün."
                            else:
                                variants = product.get("variants") or []
                                size_asked = (parsed.get("size") or "").strip().upper()
                                variant_id = None
                                for v in variants:
                                    if (v.get("name") or "").strip().upper() == size_asked or (v.get("name") or "").strip().upper() == size_asked.replace(" ", ""):
                                        variant_id = v.get("id")
                                        break
                                if not variant_id and variants:
                                    variant_id = variants[0].get("id")
                                if not variant_id:
                                    cevap_cargo = "❌ Bu beden bulunamadı. Yetkilimizle görüşün."
                                else:
                                    pay_slug = payment_type_saved or parse_payment_type(msg_body) or "kapıda_nakit"
                                    pay_id = _resolve_payment_type_id(butik_client, pay_slug)
                                    product_value = product.get("sale_price") or 0
                                    delivery = {
                                        "name": (parsed.get("name") or "").strip(),
                                        "surName": (parsed.get("surname") or "").strip() or (parsed.get("name") or "").strip(),
                                        "phone": (parsed.get("phone") or sender_phone or ""),
                                        "address": (parsed.get("address") or f"{parsed.get('city') or ''} {parsed.get('district') or ''}").strip(),
                                        "city": (parsed.get("city") or "").strip(),
                                        "district": (parsed.get("district") or "").strip(),
                                    }
                                    billing = {**delivery}
                                    custom_id = f"WA-{tenant_id}-{sender_phone[-6:]}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}"
                                    result = butik_client.create_order(
                                        custom_order_id=custom_id,
                                        delivery=delivery,
                                        billing=billing,
                                        items=[{"variantId": variant_id, "quantity": 1}],
                                        order_payment_type_id=pay_id,
                                        order_shipping_value=CARGO_SHIPPING_VALUE,
                                        order_products_value=product_value,
                                        description=f"WhatsApp satış {sender_phone}",
                                    )
                                    if result.get("ok"):
                                        supabase.table("sales_cargo_pending").delete().eq("tenant_id", tenant_id).eq("phone", sender_phone).execute()
                                        cevap_cargo = f"✅ Kargonuz oluşturuldu (Sipariş no: {result.get('custom_order_id', '')}). +50₺ kargo. En kısa sürede kargoya verilecektir. 🌸"
                                        logger.info(f"[Satış kargo] Butik sipariş oluşturuldu: {result.get('order_id')} tenant={tenant_id} phone={sender_phone} ödeme={pay_slug}")
                                    else:
                                        cevap_cargo = "❌ Sipariş oluşturulurken hata. Lütfen yetkilimizle iletişime geçin."
                                        logger.warning(f"[Satış kargo] Butik order/add: {result.get('error')}")
                        if send_replies:
                            send_whatsapp_message(sender_phone, cevap_cargo, tenant_id=tenant_id, line=line)
                            supabase.table("messages").insert({"phone": sender_phone, "message_body": cevap_cargo, "direction": "outbound", "tenant_id": tenant_id, "line": line}).execute()
                        return jsonify({"status": "received"}), 200
                    cevap_cargo = "Siparişi onaylamak için 'Tamam' veya 'Gönderin' yazın. 🌸"
                    if send_replies:
                        send_whatsapp_message(sender_phone, cevap_cargo, tenant_id=tenant_id, line=line)
                        supabase.table("messages").insert({"phone": sender_phone, "message_body": cevap_cargo, "direction": "outbound", "tenant_id": tenant_id, "line": line}).execute()
                    return jsonify({"status": "received"}), 200
            except Exception as e:
                logger.warning(f"sales_cargo_pending isleme atlandi: {e}")

        # 2. Geçmiş konuşma (aynı hattan; satış/değişim ayrı). HISTORY_MESSAGE_LIMIT ile token kullanımı azaltılabilir (varsayılan 10).
        _history_limit = int(os.getenv("HISTORY_MESSAGE_LIMIT", "10"))
        gecmis_konusma = get_gecmis_konusma(sender_phone, tenant_id, limit=_history_limit, company_name=get_tenant_info(tenant_id).company_name, line=line) if supabase else None

        # 3. Kızgın müşteri mi? → yönlendir, analiz olarak angry kabul et
        if ai_assistant.musteri_kizgin_mi(msg_body):
            cevap = HANDOVER_MESAJI
            analysis = {"sentiment": "angry", "intent": None, "urgency": "high"}
            logger.info("[Webhook] Kızgın müşteri → yönlendirme (analiz: angry)")
        else:
            # 4. AI'dan cevap + duygusal zeka analizi (sentiment, intent, urgency, reply)
            extra_instruction = get_tenant_extra_instruction(tenant_id)
            # Akıllanma: bu hat için son analiz özeti (sadece bu hattın verisi) prompt'a eklenir; satış→satış, değişim→değişim
            analysis_summary = get_analysis_summary_for_prompt(tenant_id, line, days=2)
            logger.info("[Webhook] AI cevap üretiliyor...")
            result = ai_assistant.mesaj_olustur(
                musteri_mesaji=msg_body,
                musteri_telefon=sender_phone,
                gecmis_konusma=gecmis_konusma,
                tenant_id=tenant_id,
                tenant_extra_instruction=extra_instruction,
                line=line,
                analysis_summary_for_prompt=analysis_summary,
            )
            if isinstance(result, tuple):
                cevap, analysis = result[0], result[1]
            else:
                cevap, analysis = result, None
            if cevap and "yonlendiriyorum" in cevap and "yetkil" in cevap and not analysis:
                logger.warning("[Webhook] Cevap = yönlendirme (model/API key kontrol et).")
            elif analysis:
                logger.info("[Webhook] Cevap üretildi (sentiment=%s intent=%s).", analysis.get("sentiment"), analysis.get("intent"))

        # 4b. Duygusal zeka: analiz varsa müşteri kaydını güncelle (last_sentiment, tags, status)
        if supabase and analysis:
            try:
                r = supabase.table("customers").select("status, tags").eq("tenant_id", tenant_id).eq("phone", sender_phone).eq("line", line).limit(1).execute()
                current = (r.data or [{}])[0] if r.data else {}
                cur_status = (current.get("status") or "new").strip().lower()
                cur_tags = list(current.get("tags") or []) if isinstance(current.get("tags"), list) else []
                new_status = cur_status
                intent = (analysis.get("intent") or "").strip().lower()
                sentiment = (analysis.get("sentiment") or "").strip().lower()
                if intent == "purchase_signal" and cur_status != "won":
                    new_status = "negotiation"
                elif intent == "question" and cur_status == "new":
                    new_status = "interested"
                elif intent == "return_request":
                    new_status = "return"
                if sentiment == "angry" and "🔴 DİKKAT" not in cur_tags:
                    cur_tags = cur_tags + ["🔴 DİKKAT"]
                update_payload = {
                    "last_sentiment": sentiment or None,
                    "status": new_status,
                }
                if cur_tags:
                    update_payload["tags"] = cur_tags
                supabase.table("customers").update(update_payload).eq("tenant_id", tenant_id).eq("phone", sender_phone).eq("line", line).execute()
                if new_status != cur_status or cur_tags:
                    logger.info(f"[Pipeline/Sentiment] tenant={tenant_id} phone={sender_phone} status={new_status} sentiment={sentiment} tags={cur_tags}")
            except Exception as e:
                logger.warning(f"Pipeline/Sentiment guncelleme atlandi: {e}")
            # Dinle+Analiz: AI analiz döndüyse rapor için message_analyses'e yaz
            if bot_mode == "listen_analyze":
                try:
                    supabase.table("message_analyses").insert({
                        "tenant_id": tenant_id,
                        "phone": sender_phone,
                        "line": line,
                        "message_body": (msg_body or "")[:2000],
                        "sentiment": (analysis.get("sentiment") or "").strip() or None,
                        "intent": (analysis.get("intent") or "").strip() or None,
                        "urgency": (analysis.get("urgency") or "").strip() or None,
                    }).execute()
                except Exception as e2:
                    logger.warning(f"message_analyses insert (with analysis) atlandi: {e2}")
        elif supabase and not analysis:
            # Fallback: Claude JSON dönmediyse keyword ile status (eski davranış)
            try:
                suggested = ai_assistant.detect_sales_intent(msg_body)
                if suggested:
                    supabase.table('customers').update({"status": suggested}).eq('tenant_id', tenant_id).eq('phone', sender_phone).eq('line', line).execute()
                    logger.info(f"[Pipeline fallback] tenant={tenant_id} phone={sender_phone} status={suggested}")
            except Exception as e:
                logger.warning(f"Pipeline fallback atlandi: {e}")
            # Dinle+Analiz modunda analiz yoksa da mesajı rapora kaydet (sentiment/intent/urgency boş)
            if bot_mode == "listen_analyze":
                try:
                    a = analysis or {}
                    supabase.table("message_analyses").insert({
                        "tenant_id": tenant_id,
                        "phone": sender_phone,
                        "line": line,
                        "message_body": (msg_body or "")[:2000],
                        "sentiment": (a.get("sentiment") or "").strip() or None,
                        "intent": (a.get("intent") or "").strip() or None,
                        "urgency": (a.get("urgency") or "").strip() or None,
                    }).execute()
                except Exception as e2:
                    logger.warning(f"message_analyses insert atlandi: {e2}")

        # 5. Cevap gönder (gelen mesajın hattından cevap; satış numarası / değişim numarası) — listen_analyze'da göndermiyoruz
        if cevap and send_replies:
            send_whatsapp_message(sender_phone, cevap, tenant_id=tenant_id, line=line)
        is_handover = cevap and ((cevap.strip() == HANDOVER_MESAJI.strip()) or ("yönlendiriyorum" in cevap and "yetkil" in cevap))

        if cevap and supabase and send_replies:
            supabase.table('messages').insert({
                "phone": sender_phone,
                "message_body": cevap,
                "direction": "outbound",
                "tenant_id": tenant_id,
                "line": line,
            }).execute()
            # Satış hattı: purchase_signal ise kargo bilgisi isteği
            if line == "sales" and analysis and (analysis.get("intent") or "").strip().lower() == "purchase_signal":
                try:
                    send_whatsapp_message(sender_phone, SALES_CARGO_INFO_REQUEST, tenant_id=tenant_id, line=line)
                    supabase.table("messages").insert({
                        "phone": sender_phone,
                        "message_body": SALES_CARGO_INFO_REQUEST,
                        "direction": "outbound",
                        "tenant_id": tenant_id,
                        "line": line,
                    }).execute()
                    supabase.table("sales_cargo_pending").upsert(
                        [{"tenant_id": tenant_id, "phone": sender_phone}],
                        on_conflict="tenant_id,phone"
                    ).execute()
                    logger.info(f"[Satış kargo] Kargo bilgisi istendi, bekleniyor: tenant={tenant_id} phone={sender_phone}")
                except Exception as e2:
                    logger.warning(f"sales_cargo_pending upsert atlandi: {e2}")
            # Değişim hattı: return_request ise kargo onayı beklemeye al
            if line == "exchange" and analysis and (analysis.get("intent") or "").strip().lower() == "return_request":
                try:
                    EXCHANGE_CARGO_MSG = "📦 Kargonuz son sipariş adresinize gönderilecek. Onaylıyor musunuz? 'Tamam' veya 'Gönderin' yazın. Farklı bir adrese göndermek isterseniz yeni adresinizi yazın. 🌸"
                    send_whatsapp_message(sender_phone, EXCHANGE_CARGO_MSG, tenant_id=tenant_id, line=line)
                    supabase.table("messages").insert({
                        "phone": sender_phone,
                        "message_body": EXCHANGE_CARGO_MSG,
                        "direction": "outbound",
                        "tenant_id": tenant_id,
                        "line": line,
                    }).execute()
                    supabase.table("exchange_cargo_pending").upsert(
                        [{"tenant_id": tenant_id, "phone": sender_phone}],
                        on_conflict="tenant_id,phone"
                    ).execute()
                    logger.info(f"[Değişim kargo] Onay bekleniyor: tenant={tenant_id} phone={sender_phone}")
                except Exception as e2:
                    logger.warning(f"exchange_cargo_pending upsert atlandi: {e2}")
        # Manuel geçiş: panelde "Bot yetkiliye yönlendirdi" uyarısı (cevap gönderilse de gönderilmese de)
        if is_handover and supabase:
            try:
                supabase.table('conversation_state').upsert(
                    [{"tenant_id": tenant_id, "phone": sender_phone, "handoff_requested_at": datetime.utcnow().isoformat() + "Z"}],
                    on_conflict="tenant_id,phone"
                ).execute()
                logger.info(f"[Handoff] tenant={tenant_id} phone={sender_phone} panelde gosterilecek.")
            except Exception as e2:
                logger.warning(f"conversation_state upsert atlandi: {e2}")

    except Exception as e:
        logger.error(f"Webhook isleme hatasi: {e}")

    return jsonify({"status": "received"}), 200

def get_gecmis_konusma(phone, tenant_id="tuba", limit=12, company_name=None, line=None):
    """Supabase'den bu numaranin (ve tenant + line) onceki mesajlarini alir (AI context icin). line=sales|exchange ile aynı hattan geçmiş."""
    if not supabase:
        return None
    asistan_adi = company_name or "Tuba Butik"
    try:
        q = supabase.table("messages").select("direction, message_body, created_at").eq("phone", phone).eq("tenant_id", tenant_id)
        if line:
            q = q.eq("line", line)
        q = q.order("created_at", desc=True).limit(limit + 1)
        response = q.execute()
        if not response.data or len(response.data) < 2:
            return None
        # Ilk kayit su anki mesaj; oncekileri kronolojik siraya cevir
        oncekiler = response.data[1 : limit + 1]
        oncekiler.reverse()
        lines = []
        for m in oncekiler:
            yon = "Müşteri" if m.get("direction") == "inbound" else asistan_adi
            body = (m.get("message_body") or "").strip()
            if body:
                lines.append(f"{yon}: {body}")
        return "\n".join(lines) if lines else None
    except Exception as e:
        logger.warning(f"Gecmis konusma alinamadi: {e}")
        return None


def send_whatsapp_message(phone, text, tenant_id=None, line=None):
    """Meta API ile mesaj atar. tenant_id + line: line=exchange ise değişim hattı numarası ve token kullanılır."""
    use_phone_id = PHONE_ID
    use_token = META_TOKEN
    if tenant_id and supabase:
        try:
            r = supabase.table("tenants").select(
                "whatsapp_phone_number_id, whatsapp_access_token, whatsapp_phone_number_id_exchange, whatsapp_access_token_exchange"
            ).eq("tenant_id", tenant_id).limit(1).execute()
            if r.data and len(r.data) > 0:
                row = r.data[0]
                if line == "exchange" and row.get("whatsapp_phone_number_id_exchange") and row.get("whatsapp_access_token_exchange"):
                    use_phone_id = row.get("whatsapp_phone_number_id_exchange")
                    use_token = row.get("whatsapp_access_token_exchange")
                else:
                    tid = row.get("whatsapp_phone_number_id")
                    tok = row.get("whatsapp_access_token")
                    if tid and tok:
                        use_phone_id = tid
                        use_token = tok
        except Exception as e:
            logger.warning(f"Tenant WhatsApp credentials: {e}")
    if not use_token or not use_phone_id:
        return False, "WhatsApp bağlantısı ayarlı değil (token veya telefon ID eksik)."
    url = f"https://graph.facebook.com/v17.0/{use_phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {use_token}",
        "Content-Type": "application/json"
    }
    to = "".join(c for c in str(phone) if c.isdigit())
    if not to:
        return False, "Geçersiz telefon numarası."
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        if r.status_code == 200:
            logger.info(f"✅ Mesaj gonderildi: {to}")
            return True, None
        data = r.json() if r.text else {}
        err = data.get("error", {})
        api_msg = err.get("message", r.text or "WhatsApp API hatası.")
        if r.status_code in (401, 403):
            msg = "Meta token geçersiz veya süresi dolmuş. Test ortamındaysanız yalnızca test numaralarına mesaj gidebilir. Meta Business Suite'ten erişim token'ını kontrol edin."
        else:
            msg = api_msg
        logger.error(f"❌ Mesaj gonderilemedi: {api_msg}")
        return False, msg
    except Exception as e:
        logger.error(f"❌ Request hatasi: {e}")
        return False, str(e)

def notify_deploy_finished():
    """Deploy bittiğinde admin numarasına WhatsApp ile bilgi mesajı atar."""
    admin_phone = os.getenv("ADMIN_PHONE", "").strip()
    if not admin_phone or not META_TOKEN or not PHONE_ID:
        return
    to = "".join(c for c in admin_phone if c.isdigit())
    if not to:
        return
    try:
        ok, _ = send_whatsapp_message(to, "✅ Deploy bitti. Tuba WhatsApp Bot çalışıyor.")
        if ok:
            logger.info("Deploy bildirimi admin'e gonderildi.")
    except Exception as e:
        logger.warning(f"Deploy bildirimi atilamadi: {e}")


# 404: Bilinmeyen path'leri ana sayfaya yonlendir (panel/landing acilir)
@app.errorhandler(404)
def not_found(e):
    if request.method == "GET":
        return redirect(url_for("home"))
    return jsonify({"error": "Not Found"}), 404

if __name__ == '__main__':
    # macOS'ta 5000 genelde AirPlay'de kullanildigi icin varsayilan 5001
    port = int(os.environ.get("PORT", 5001))
    notify_deploy_finished()
    url = f"http://127.0.0.1:{port}"
    print("\n" + "=" * 50)
    print(f"  Tarayicida ac: {url}")
    print(f"  Test sayfasi:  {url}/test")
    print("=" * 50 + "\n")
    app.run(host='0.0.0.0', port=port)
