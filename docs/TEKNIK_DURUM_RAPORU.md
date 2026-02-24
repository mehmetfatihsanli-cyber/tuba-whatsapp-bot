# Teknik Durum Raporu – Tuba WhatsApp Bot

**Tarih:** Şubat 2026  
**Amaç:** Projenin mevcut durumunun detaylı özeti (Technical Status Report).

---

## 1. PROJE GENEL YAPISI

### Ana dosyalar

| Dosya / Klasör | Açıklama |
|----------------|----------|
| **app.py** | Ana Flask uygulaması: webhook, panel, API, auth, WhatsApp mesaj gönderimi. |
| **config.py** | Ortam değişkenleri (Anthropic, Supabase, Meta, AI model). |
| **claude_client.py** | Claude API çağrı wrapper’ı. |
| **whatsapp_client.py** | Meta WhatsApp API ile mesaj gönderme. |
| **database.py** | Log / mock (ana veri Supabase üzerinden). |
| **modules/** | `ai_assistant.py` (Claude, prompt, Pinecone), `butiksistem_client.py`, `pinecone_manager.py`, `tuba_rules.py`, `return_exchange.py`, `sales_assistant.py`, `sync_products.py`. |
| **prompts/** | `tuba_system.txt` – Tuba için sistem promptu; tenant’a göre `{tenant_id}_system.txt` okunabilir. |
| **templates/** | Jinja2 şablonları (base, panel, studio, landing, legal, auth sayfaları). |
| **docs/** | Dokümantasyon (çoklu kiracı, maliyet, log, API stratejileri vb.). |
| **sync_products.py** | Ürünleri Butik/XML’den alıp Pinecone’a yükler. |

### Veritabanı yapısı

- **`models.py` yok.** Projede ORM kullanılmıyor.
- **Harici yapı: Supabase** (PostgreSQL). Bağlantı `app.py` içinde `create_client(SUPABASE_URL, SUPABASE_KEY)` ile kuruluyor.
- Veri erişimi: `supabase.table("tenants")`, `supabase.table("messages")` vb. REST/PostgREST üzerinden.
- Tablolar: **tenants**, **messages**, **customers**, **conversation_state**, **conversations** (Supabase Dashboard / SQL migration dosyaları ile yönetiliyor).

### Kritik kütüphaneler

| Kütüphane | Kullanım |
|-----------|----------|
| **Flask** | Web uygulaması, rotalar, session. |
| **flask-cors** | CORS. |
| **Werkzeug** | `generate_password_hash`, `check_password_hash` (auth). |
| **anthropic** | Claude API (AI cevap). |
| **supabase** | Veritabanı (tenants, messages, customers, conversation_state). |
| **requests** | HTTP (ButikSistem API, Meta WhatsApp). |
| **python-dotenv** | Ortam değişkenleri. |
| **pinecone-client** | Ürün araması (vektör). |
| **sentence-transformers** | Embedding (Pinecone için). |

**Yok:** SQLAlchemy, OpenAI (Claude kullanılıyor), **Stripe/Iyzico** (ödeme entegrasyonu yok; landing’de Iyzico metni görsel olarak var).

---

## 2. BACKEND VE ROTALAR (app.py Analizi)

### Aktif sayfalar (Routes)

| Rota | Metod | Açıklama |
|------|--------|----------|
| **/** | GET | Ana sayfa (landing); `logged_in` session’a göre. |
| **/health** | GET | Health check. |
| **/login** | GET, POST | Giriş (e-posta+şifre veya tenant+şifre). |
| **/register** | GET, POST | Kayıt ol (tenants tablosuna yeni mağaza). |
| **/panel/login** | GET | `/login`’e yönlendirme. |
| **/forgot-password** | GET, POST | Şifremi unuttum (e-posta, token, mail). |
| **/reset-password/<token>** | GET, POST | Token ile yeni şifre. |
| **/panel/logout**, **/dashboard/logout** | GET | Çıkış; session temizlenir. |
| **/dashboard** | GET | Panel ana sayfa (Genel Bakış). |
| **/dashboard/messages** | GET | Mesajlar (hat=satis veya hat=iade). |
| **/dashboard/studio** | GET | Model Talimatı (ek talimat). |
| **/dashboard/ai-studio** | GET | AI Stüdyo (placeholder: Çok Yakında). |
| **/dashboard/settings/whatsapp** | GET | WhatsApp bağlantı ayarları. |
| **/api/studio/extra-prompt** | GET, POST | Ek talimat oku/kaydet. |
| **/api/customers** | GET | Müşteri listesi. |
| **/api/send-message** | POST | Panelden WhatsApp mesajı gönder. |
| **/api/save-whatsapp-settings** | POST | WhatsApp Phone ID / token kaydet. |
| **/api/handoffs** | GET | Yetkiliye yönlendirme listesi. |
| **/api/dashboard/last-messages** | GET | Son 5 mesaj (canlı akış). |
| **/api/dashboard/kpis** | GET | KPI (ciro, sohbet, iade, AI maliyeti). |
| **/api/check-model** | GET | Claude API key durumu. |
| **/webhook** | GET | Meta doğrulama (verify_token). |
| **/webhook** | POST | WhatsApp gelen mesaj. |
| **/legal/privacy**, **terms**, **sales-agreement**, **cancellation**, **about** | GET | Yasal sayfalar. |

### Kimlik doğrulama (Auth)

- **Session tabanlı.** Flask `session`; ana anahtar: `session["tenant_id"]`.
- **Giriş:**  
  - E-posta + şifre → Supabase `tenants` tablosunda `email` + `password_hash` (Werkzeug `check_password_hash`).  
  - Alternatif: `tenant_id` (tuba, zafer, ali) + env’deki `PANEL_PASS_*` şifresi.
- **Koruma:** `@panel_tenant_required` decorator’ı panel rotalarında kullanılıyor; `session.get("tenant_id")` yoksa `/login` veya API’de 403.
- **Şifre sıfırlama:** `forgot-password` → token üretilir, `tenants.reset_token` / `reset_token_expires` güncellenir, SMTP ile mail (MAIL_* env’leri gerekli). `reset-password/<token>` ile yeni şifre hash’lenip kaydedilir.
- **Token tabanlı API yok** (JWT/OAuth yok); sadece panel için session.

### Entegrasyonlar

| Entegrasyon | Durum |
|-------------|--------|
| **WhatsApp API (Meta)** | Aktif. Webhook GET doğrulama, POST ile gelen mesaj alınıyor; cevap `whatsapp_client` ile gönderiliyor; tenant’a göre `tenants.whatsapp_phone_number_id` / `whatsapp_access_token` kullanılıyor. |
| **Mail gönderme (SMTP)** | Kod hazır (`send_reset_email`). `MAIL_SERVER`, `MAIL_USERNAME`, `MAIL_PASSWORD` (ve isteğe bağlı `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_FROM`, `BASE_URL`) tanımlı değilse mail gitmez. |
| **Ödeme sistemi (Stripe/Iyzico)** | Bağlı değil. Landing’de Iyzico/Mastercard görsel metin var; gerçek ödeme akışı yok. |

---

## 3. FRONTEND VE SAYFALAR (templates/ Analizi)

### Landing Page (landing.html)

- **İçerik:** Hero, “Biz Kimiz”, **Özellikler** (7/24 Temsilci, Otomatik Satış, Kombin Önerisi), **Blog & Haberler**, **Fiyatlandırma**, İletişim/CTA, Footer, Canlı Destek widget (placeholder).
- **Fiyatlandırma:** Görünüyor. 3 paket: Başlangıç 990₺/ay, PRO 1.990₺/ay (Önerilen), Enterprise “Teklif”. “Başla” / “İletişime Geç” butonları `/register`’a gidiyor.
- **Özellikler:** 3 kart (7/24 Müşteri Temsilcisi, Otomatik Satış, Kombin Önerisi) mevcut.
- **Durum:** İçerik tam; `logged_in` ile Giriş Yap / Panele Git ayrımı yapılıyor.

### Dashboard

- **Dashboard ana sayfa:** `index.html` (base.html’i extend eder). Başlık: “Genel Bakış”.
- **Modüller:**  
  - KPI kartları: Toplam Ciro, Aktif Sohbetler, Bekleyen İadeler, AI Maliyeti (API’den dolduruluyor; ciro/iade/AI maliyeti şu an 0).  
  - Satış & Kombin Uzmanı / Akıllı Değişim-İade (toggle; sadece UI).  
  - AI Stüdyo (Beta): “Görsel Yükle” butonu → `alert('Yakında! Bu özellik çok yakında eklenecek.')`.  
  - Entegrasyonlar: “Ödeme: Bağlı”, “Kargo: Bağlı” (sabit metin).  
  - Canlı Akış: Son mesajlar `/api/dashboard/last-messages` ile yükleniyor.
- **Ayarlar:** Sol menüden “Ayarlar” → WhatsApp (`/dashboard/settings/whatsapp`).
- **AI Stüdyo (ayrı sayfa):** `/dashboard/ai-studio` → `ai_studio.html`; “Çok Yakında”, devre dışı “Demo Yükle” (placeholder).
- **Model Talimatı:** `/dashboard/studio` → `studio.html`; ek talimat textarea + Kaydet (çalışıyor).
- **Mesajlaşma alanı:** `/dashboard/messages` → `panel.html`; müşteri listesi, sohbet, panelden mesaj gönderme.

### Kritik akış sayfaları

| Sayfa | Dosya | Durum |
|-------|--------|--------|
| **Kayıt Ol** | `register.html` | Mevcut. Ad, e-posta, şifre, mağaza adı; POST ile tenants’a kayıt. |
| **Şifremi Unuttum** | `forgot_password.html` | Mevcut. E-posta alır; token + mail (SMTP env gerekli). |
| **Yeni Şifre (Token)** | `reset_password.html` | Mevcut. Token ile yeni şifre + tekrar; hash’lenip tenants’ta güncellenir. |
| **Giriş** | `panel_login.html` | Mevcut. E-posta+şifre veya tenant+şifre. |

**Not:** Projede `static/` klasörü yok; CSS/JS CDN (Tailwind) ve inline script kullanılıyor.

---

## 4. AI VE BOT YETENEKLERİ

### Prompt yapısı nerede tutuluyor?

- **Sabit / dosya tabanlı:** `prompts/tuba_system.txt` (varsayılan sistem promptu).  
- **Tenant’a özel dosya:** `prompts/{tenant_id}_system.txt` (varsa önce o okunur).  
- **Dinamik (veritabanı):** `tenants.ai_extra_instruction`. Panelden “Model Talimatı” sayfasında kaydedilen ek talimat; her AI cevabında base prompt’a ekleniyor.

### Her mağaza (Tenant) için özelleştirme

- **Evet.**  
  - Her tenant için ayrı sistem prompt dosyası (`prompts/{tenant_id}_system.txt`) destekleniyor.  
  - `ai_extra_instruction` ile panelden metin ekleniyor; `modules/ai_assistant.py` içinde `mesaj_olustur(..., tenant_id=..., tenant_extra_instruction=...)` ile base + ek birleştiriliyor.  
  - WhatsApp tarafında tenant, `phone_id_to_tenant(phone_id)` ile belirleniyor (Supabase `tenants.whatsapp_phone_number_id` veya env fallback).  
  - Panel ve API’ler `session["tenant_id"]` ile tenant’a göre veri gösteriyor / kaydediyor.

---

## 5. EKSİKLER VE "TODO" LİSTESİ

### Kod içi TODO / FIXME

- **app.py:** `# --- Yasal sayfalar icin sirket bilgisi (env veya placeholder; sonra doldurulacak)` → Yasal sayfalarda şirket adı, adres, vergi no vb. `get_company_legal()` ile env’den okunuyor; env yoksa placeholder metin (“ŞİRKET_ADI”, “ADRES” vb.) kullanılıyor.

### Görünürde olup çalışmayan (placeholder) öğeler

| Öğe | Konum | Davranış |
|-----|--------|----------|
| **AI Stüdyo sayfası** | `/dashboard/ai-studio`, `ai_studio.html` | “Çok Yakında” metni; “Demo Yükle” butonu devre dışı / işlevsiz. |
| **Dashboard “Görsel Yükle”** | `index.html` | Tıklanınca `alert('Yakında! Bu özellik çok yakında eklenecek.')`. |
| **KPI: Ciro, İade, AI maliyeti** | `api/dashboard/kpis` | Şu an 0; gerçek veri kaynağı (Butik, maliyet takibi) bağlı değil. |
| **Entegrasyonlar: Ödeme/Kargo** | `index.html` | “Bağlı” sabit metin; gerçek entegrasyon yok. |
| **Canlı Destek widget** | `landing.html` | Açılır kutu var; mesaj gönderme/backend yok. |

### TODO.md’den öne çıkanlar

- E-posta (şifre sıfırlama) kurulumu: MAIL_* ve BASE_URL env’leri; Supabase’te `reset_token`, `reset_token_expires` kolonları.
- Model (Claude): Railway’de `ANTHROPIC_API_KEY` gerçek key olmalı; `/api/check-model` ile doğrulanıyor.

---

## 6. SONUÇ

### Proje şu an "Canlıya Alınabilir" (Production Ready) mi?

- **Evet, koşullu.** WhatsApp webhook, AI cevap (Claude), panel (giriş, mesajlar, Model Talimatı, ayarlar), çoklu tenant, kayıt ve şifre sıfırlama akışı mevcut.  
- **Gerekli koşullar:** Railway (veya host) ortamında `ANTHROPIC_API_KEY`, `META_ACCESS_TOKEN` (veya tenant bazlı token), `SUPABASE_URL`, `SUPABASE_KEY`, `FLASK_SECRET_KEY` tanımlı olmalı. Şifre sıfırlama maili için MAIL_* ve BASE_URL isteğe bağlı ama önerilir.

### En acil yapılması gereken teknik düzeltme

1. **E-posta (şifre sıfırlama):** MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD (ve gerekirse MAIL_FROM, BASE_URL) tanımlanmazsa “Şifremi unuttum” maili gitmez; kullanıcıya “E-posta gönderilemedi” mesajı çıkar.  
2. **Yasal sayfalar:** `COMPANY_LEGAL_NAME`, `COMPANY_ADDRESS`, `COMPANY_TAX_NUMBER` vb. env’leri doldurmak; aksi halde placeholder metinler kalır.  
3. **AI Stüdyo:** Şu an sadece placeholder; “Görsel Yükle” / 360° özelliği ileride eklenecekse roadmap’te netleştirilebilir.

---

**Rapor sonu.**  
Özet: **Flask + Supabase + Claude + WhatsApp** mimarisi; **models.py yok**, veri **Supabase** ile; **static/** yok; ödeme (Stripe/Iyzico) entegre değil.

**Şubat 2026 ekleri:** Satış kargo iki aşama (onayda Butik sipariş); değişim kargo (son adres / farklı adres, whoPaysShipping recipient); satış/değişim **hat ayrımı** (messages.line, customers.line, iki numara veya tek numara test modu); exchange_cargo_pending tablosu; panel Satış Hattı / Değişim İade Hattı sekmeleri. Detay: `docs/SATIS_DEGISIM_HATLARI.md`, `docs/GUN_SONU_OZET.md`.
