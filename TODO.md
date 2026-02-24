## Yeni sohbette başlarken

Cursor'a yaz: **@BAGLAM_OZETI.md @TODO.md oku, son duruma göre devam edelim.**  
(Ayrıntı: `CURSOR_BASLARKEN.md`)

---

## Güncel durum (Şubat 2026)

### ✅ Tamamlananlar

- [x] Flask + webhook (GET doğrulama, POST mesaj alma)
- [x] Meta WhatsApp (mesaj alınıyor, cevap gidiyor)
- [x] Supabase `messages` (kayıt + geçmiş konuşma AI'ya veriliyor)
- [x] AI asistan (Claude, Tuba kuralları, iade/değişim, kızgın müşteri → yönlendir)
- [x] ButikSistem client bağlı (sipariş: önce Butik API, yoksa test_orders)
- [x] Panel (/panel, son 50 mesaj, panelden mesaj gönder)
- [x] Pinecone index + modül (tuba-products; cevap akışında henüz kullanılmıyor)
- [x] Anthropic API key, AI prompt güncellendi (iade/değişim kuralları)
- [x] test_orders.json (TEST001, TEST002 – 905367817705)
- [x] GitHub repo bağlı
- [x] Railway deploy yapıldı (railway up)
- [x] Meta 404 hatası – çözüm uygulandı (loglar incelendi)
- [x] Bağlam/TODO yapısı: BAGLAM_OZETI.md, CURSOR_BASLARKEN.md
- [x] Şifre sıfırlama (Şifremi unuttum → e-posta ile link, /forgot-password, /reset-password)

### 🔴 Mutlaka yapılacaklar (Kurulum)

- [ ] **E-posta (şifre sıfırlama) kurulumu**  
  Müşteriler "Şifremi unuttum" dediğinde maillerinin kutusuna sıfırlama linki gidebilsin diye:
  1. **Proje adı netleşince** o isimle bir Gmail hesabı aç (örn. `tubaai@gmail.com`). Müşteriye giden maillerde "Kimden" bu adres görünecek; şahsi mail kullanmak yerine proje adına mail daha profesyonel olur.
  2. Bu Gmail için **2 adımlı doğrulama** aç, ardından **Uygulama şifresi** oluştur (Google Hesap → Güvenlik → Uygulama şifreleri).
  3. **Railway → Variables** bölümüne ekle:
     - `MAIL_SERVER` = `smtp.gmail.com`
     - `MAIL_PORT` = `587`
     - `MAIL_USERNAME` = proje Gmail adresi
     - `MAIL_PASSWORD` = oluşturduğun uygulama şifresi (16 karakter)
     - `MAIL_USE_TLS` = `1`
     - `MAIL_FROM` = aynı proje Gmail (isteğe bağlı)
     - `BASE_URL` = canlı site adresi (örn. `https://tuba-whatsapp-bot-production.up.railway.app`)
  4. Supabase’de `supabase_tenants_reset_password_columns.sql` bir kez çalıştırıldı mı kontrol et (`reset_token`, `reset_token_expires` sütunları).

### ⏳ Yapılacaklar / Devam eden

- [ ] **Model devreye girsin (Claude):** Yol haritası → `YOL_HARITASI_MODEL_TAM_COZUM.md`
  1. Railway Variables’da `ANTHROPIC_API_KEY` gerçek key (sk-ant-api03-...) olsun.
  2. Canlıda `https://.../api/check-model` aç → `claude_configured: true` görünsün.
  3. WhatsApp’tan **"Ürün önerir misin?"** ile test et (merhaba/iade değil); log’ta "Claude'dan geldi" görünsün.
- [ ] WhatsApp'tan uçtan uca test (yukarıdaki adımlar tamamlandıktan sonra tekrar doğrula).
- [x] Pinecone'u cevap akışına bağla (ürün sorusunda arama) — _satis_urun_context, satış kelimeleri ile bağlı.

### ✅ Tamamlananlar (Satış/Değişim hatları + kargo – Şubat 2026)

- [x] **Satış kargo iki aşama:** Bilgi gelir → özet + onay iste → "Tamam/Gönderin" → Butik sipariş. Ödeme: peşin / kapıda nakit / kapıda kredi / havale. Mesaj: "Kargonuz oluşturuldu".
- [x] **Değişim kargo:** Son sipariş adresi veya "farklı adres" → yeni adres al → onayda Butik sipariş (müşteri kargo öder). Tablo: `exchange_cargo_pending`; Butik: `get_last_order_delivery_and_variant`, `create_order(..., who_pays_shipping="recipient")`.
- [x] **Satış / Değişim hatları:** Numaraya göre `line` (sales/exchange). `messages.line`, `customers.line`; panel Satış Hattı / Değişim İade Hattı; model hatta göre davranır. Tek numara test: mesajda iade/değişim varsa exchange sayılır.
- [x] **Supabase:** Migration MCP ile uygulandı (add_line_sales_exchange, add_exchange_cargo_pending). Tenants: whatsapp_phone_number_id_exchange, whatsapp_access_token_exchange. Ayarlar sayfasında Değişim hattı alanları.
- [x] **Railway deploy** tetiklendi (MCP).

### ✅ Tamamlananlar (AI Stüdyo – 8 Şubat 2026)

- [x] **Kategoriler genişletildi:** Bluz/Gömlek/Ceket, Pantolon, Etek, Elbise (backend CATEGORY_MAP + form kabulü).
- [x] **Varsayılan manken Kaldır:** API `/api/ai-studio/default-mannequin/remove` (POST/DELETE) + panelde "Kaldır" butonu.
- [x] **Metin prompt açıklaması:** "Bu metin AI'a kıyafet açıklaması olarak gönderilir" notu + kategori alanına kısa açıklama.
- [x] **Railway deploy** (railway up) – AI Stüdyo güncellemeleri canlıda.

### ✅ Önceki (Şubat) yapılanlar

- [x] Model: API key log; ai_assistant Claude/hata/sabit cevap log'ları
- [x] Panel: Müşteri listesi, sohbet, panelden mesaj gönder
- [x] Webhook KeyError 'orderId' düzeltmesi; Satış tetikleyicileri (Pinecone); Tuba prompt (site linkleri, Gemini kuralları)
- [x] Panel Model Talimatı (ai_extra_instruction); menü "Model Talimatı"

### 📝 Notlar

- Test modu: WhatsApp numarası ButikSistem'de kayıtlı olmayabilir; canlıda Butik API tam kullanılacak.
- Test sipariş: 905367817705 için TEST001, TEST002.
- Satış/değişim: Canlıda Tuba (Zafer, Ali) iki numara tanımlayacak; panel Ayarlar > WhatsApp > Değişim hattı. Tek numara ile testte mesajda "iade"/"değişim" yazınca otomatik değişim hattı davranır.
- Gün sonu: `docs/GUN_SONU_OZET.md` ve `BAGLAM_OZETI.md` güncellenir; TODO’da o gün yapılanlar “Tamamlananlar”a taşınır; Cursor güncellemesi sonrası `@BAGLAM_OZETI.md @TODO.md oku` ile devam.

---

## ⚠️ Kullanıcı bilgisi

- Terminal/kod komutları bilinmiyor; sadece kopyala-yapıştır.
- Hazır, bağımsız komutlar ver; adım adım basit anlat.
