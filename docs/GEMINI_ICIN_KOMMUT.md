# Gemini İçin Hazır Komut – Teknik Durum Raporu

Aşağıdaki metni kopyalayıp Gemini'ye yapıştırabilirsin. Proje yapısına göre uyarlanmıştır (models.py yok, Supabase kullanılıyor).

---

Ortağım, projenin şu anki durumu hakkında detaylı bir **Teknik Durum Raporu** (Technical Status Report) istiyorum.

Lütfen tüm ilgili dosyaları tara ve aşağıdaki başlıklarla bir özet çıkar:

---

## 1. PROJE YAPISI
- Ana dosyalar ve klasörler neler? (app.py, config.py, modules/, templates/, prompts/, docs/ vb.)
- **Not:** Bu projede `models.py` yok; veritabanı **Supabase** ile yönetiliyor (supabase client, REST).

---

## 2. BACKEND VE ÖZELLİKLER (app.py)
- Hangi rotalar (Routes) aktif? (Örn: /login, /register, /dashboard, /dashboard/studio, /dashboard/ai-studio, /dashboard/messages, /dashboard/settings/whatsapp, /api/studio/extra-prompt, /api/send-message, /api/customers, /webhook, /legal/* vb.)
- Hangi kütüphaneler kullanılıyor? (Flask, Anthropic/Claude, Supabase, requests, werkzeug vb.)
- Entegrasyonlar ne durumda? (WhatsApp Webhook, Supabase, ButikSistem API, Pinecone, SMTP şifre sıfırlama vb.)

---

## 3. VERİTABANI VE MODELLER
- **Not:** `models.py` yok. Veritabanı **Supabase** (PostgreSQL). Şunları incele:
  - Hangi tablolar var? (tenants, messages, customers, conversation_state, conversations vb.)
  - Tablolar arasındaki ilişkiler neler? (tenant_id, phone vb.)
  - Yeni/önemli alanlar: tenants tablosunda `ai_extra_instruction`, `whatsapp_*`, `reset_token`, `reset_token_expires` vb. var mı?

---

## 4. FRONTEND VE SAYFALAR (templates/)
- Hangi HTML sayfaları mevcut? (base.html, landing.html, index.html, panel.html, studio.html, ai_studio.html, register.html, panel_login.html, forgot_password.html, reset_password.html, settings/whatsapp.html, legal/*.html vb.)
- Landing Page (Ana Sayfa) içeriği tam mı? (Fiyatlandırma, Özellikler var mı?)
- Dashboard (Panel) içeriği tam mı? (Genel Bakış, Mesajlar, Model Talimatı, AI Stüdyo, Ayarlar var mı?)
- "Kayıt Ol" (Register) ve "Şifremi Unuttum" sayfaları var mı?

---

## 5. EKSİKLER VE TODO'LAR
- Kod içinde `TODO`, `FIXME` veya `placeholder` etiketiyle bırakılmış notlar var mı?
- Henüz tamamlanmamış veya "boş" (placeholder) duran fonksiyonlar/sayfalar var mı? (Örn: AI Stüdyo sayfası "Çok Yakında", KPI verileri 0, last-messages 404 vb.)

---

## 6. SON DURUM ÖZETİ
- Proje şu an çalışmaya hazır mı?
- Kritik bir hata veya eksik görüyor musun?

---

Lütfen bu raporu **maddeler halinde**, **net ve anlaşılır Türkçe** ile hazırla. Proje adı: **Tuba WhatsApp Bot** (Flask + Supabase + Claude + WhatsApp).
