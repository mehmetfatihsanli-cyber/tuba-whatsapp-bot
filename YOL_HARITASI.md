# Tuba WhatsApp Bot – Proje Mantığı ve Yol Haritası

Bu doküman: projenin **ne yaptığını**, **şu ana kadar nelerin bittiğini** ve **nereden başlayıp nasıl ilerleyeceğini** tek yerde toplar.

---

## 1. Proje Mantığı (Kısaca)

**Amaç:** Tuba Butik’in WhatsApp’ına gelen müşteri mesajlarına, kurallara uygun ve bağlama duyarlı (geçmiş konuşmayı bilen) bir AI asistanın otomatik cevap vermesi.

**Akış:**

```
WhatsApp (müşteri mesajı) → Meta webhook → Bizim sunucu (app.py)
       → Mesaj DB'ye yazılır (Supabase: messages)
       → Bu numaranın geçmiş mesajları alınır
       → AI (Claude) cevap üretir (sipariş/iade/ürün kuralları + geçmiş)
       → Cevap WhatsApp’a gönderilir → Cevap da DB'ye yazılır
```

**Kullanılan parçalar:**

| Parça | Görevi |
|--------|--------|
| **app.py** | Webhook, panel API’leri, mesaj kaydetme, geçmiş çekme, AI’ya sorma, WhatsApp’a gönderme |
| **modules/ai_assistant.py** | Tuba Butik karakteri, basit/karmaşık ayrımı, Claude çağrısı, iade/değişim kuralları, sipariş bilgisi (test_orders) |
| **Supabase** | Mesajlar `messages` tablosunda (phone, message_body, direction, created_at) |
| **Panel** | `/panel` → Son mesajlar listesi, (isteğe bağlı) manuel mesaj gönderme |

Spec’teki **multi-tenant** (birden fazla mağaza) ve **modül bazlı yönlendirme** (sales_assistant / return_exchange ayrı modüller) tasarımı var; şu an uygulama **tek mağaza (Tuba Butik)** ve **tek AI asistan** ile çalışıyor. İleride tenant ve modül mantığı açılabilir.

---

## 2. Şimdiye Kadar Yapılanlar

### Tamamlanan

- **Flask uygulaması:** Webhook (GET doğrulama, POST mesaj alma), ana sayfa, panel sayfası.
- **WhatsApp bağlantısı:** Gelen mesaj alınıyor, cevap Meta API ile gönderiliyor.
- **Supabase:** `messages` tablosuna gelen/giden mesajlar yazılıyor.
- **AI asistan (Tuba):** Claude ile cevap; basit selam/fiyat vs. karmaşık iade/sipariş ayrımı; Tuba kuralları (iade 14 gün, değişim 2 hak, vb.).
- **Geçmiş konuşma:** Müşteri numarasına göre son mesajlar DB’den alınıp AI’ya “önceki konuşma” olarak veriliyor.
- **Test sipariş verisi:** `test_orders.json` ile belirli numaralar için sipariş bilgisi AI’ya veriliyor.
- **Panel:** Mesaj listesi (`/api/customers`), panelden mesaj gönderme (`/api/send-message`).
- **Pinecone:** Ürün index’i (tuba-products) ve ilgili modül hazır; isteğe bağlı ürün araması için kullanılabilir.
- **ButikSistem client:** Kodda var; canlı entegrasyon açılınca sipariş/ürün çekmek için kullanılacak.
- **Dokümantasyon:** PROJECT_SPEC, PROJECT_SUMMARY, GECMIS_LOGLARI, TODO.

### Kısmen / Farklı Kullanılan

- **database.py:** `get_tenant_by_phone_id` ve `log_conversation` şu an **mock** (test modu); gerçek Supabase `tenants` / `conversations` tabloları app.py akışında kullanılmıyor. Asıl loglama `messages` tablosu üzerinden.
- **sales_assistant.py / return_exchange.py:** Modül fonksiyonları var; app.py doğrudan `TubaAIAssistant` kullandığı için bu modüllere **yönlendirme yok**. İstenirse ileride tenant + modül seçimi ile bağlanabilir.

### Henüz Yapılmayan (TODO’dan)

- **Railway’e deploy:** Kodun canlı sunucuda çalışması.
- **WhatsApp’tan gerçek test:** “iade yapmak istiyorum” vb. ile uçtan uca test.
- **Görsel mesaj:** Fotoğraf (iade/defo) alıp Claude Vision ile analiz (spec’te var, akışa tam bağlı değil).

---

## 3. Nereden Başlamalı?

Öncelik sırası önerisi:

### Adım 1: Yerel ortamın çalıştığından emin ol

- `.env` dosyasında: `SUPABASE_URL`, `SUPABASE_KEY`, `ANTHROPIC_API_KEY`, `META_ACCESS_TOKEN`, `PHONE_ID`, `VERIFY_TOKEN` dolu mu kontrol et.
- Proje klasöründe:
  ```bash
  cd ~/tuba-whatsapp-bot
  python3 app.py
  ```
- Tarayıcıda: `http://localhost:5000` → “Tuba WhatsApp Botu & Paneli Aktif!” görünmeli.
- `http://localhost:5000/panel` → Panel açılıyor mu bak.

### Adım 2: Webhook’u canlıya bağla (deploy)

- Kodu **Railway** (veya kullandığın platform) üzerine deploy et.
- Meta geliştirici panelinde webhook URL’i: `https://<senin-domain>/webhook`, verify token: `.env`’deki `VERIFY_TOKEN`.
- GET ile doğrulama yeşil olmalı; sonra WhatsApp’tan bir mesaj atıp POST’un çalıştığını kontrol et.

### Adım 3: Uçtan uca WhatsApp testi

- Kayıtlı numaradan Tuba’nın WhatsApp’ına mesaj at: “Merhaba”, “iade yapmak istiyorum” vb.
- Cevap gelmeli; Supabase `messages` tablosunda gelen + giden iki satır görünmeli.
- Panelde bu mesajlar listelenebilmeli.

### Adım 4: Hata / eksik varsa loglardan ilerle

- Railway (veya sunucu) loglarına bak.
- Gerekirse `app.py` içinde kritik yerlere `logger.info(...)` ekleyerek “mesaj alındı / geçmiş çekildi / AI cevap verdi / WhatsApp’a gönderildi” adımlarını takip et.

Bu sırayla ilerlemek: önce “çalışan tek mağaza botu”, sonra özellik ekleme ve (istersen) tenant/modül mimarisi için sağlam zemin olur.

---

## 4. Yol Haritası (Kısa / Orta / Uzun)

### Kısa vade (hemen)

1. **Deploy:** Railway’e deploy, webhook URL ve env değişkenleri doğru.
2. **Test:** En az bir gerçek WhatsApp mesajı ile cevap alındığını doğrula.
3. **Panel:** Müşteri bazlı konuşma görünümü (numaraya tıklayınca o numaranın mesajları) – şu an sadece “son 50 mesaj” var.

### Orta vade

4. **Görsel (resim) desteği:** Webhook’ta `image` tipi mesajı yakala, indir, Claude Vision’a ver; iade/defo analizi (return_exchange mantığı) akışa bağlanabilir.
5. **Ses mesajı:** “Ses mesajı desteklenmiyor, lütfen yazın” gibi net cevap (spec’te metin var, kodda tek tip “Medya/Diger” olabilir; ayrıştırılabilir).
6. **Gerçek sipariş verisi:** ButikSistem (veya başka API) açıldığında test_orders yerine canlı sipariş bilgisini AI’ya vermek.
7. **conversations / log_conversation:** İstersen spec’e uygun `conversations` tablosu + `log_conversation` ile analitik loglama.

### Uzun vade (spec’e tam uyum / SaaS)

8. **Tenant yönetimi:** Supabase’de `tenants` tablosu, `whatsapp_phone_id` ile tenant bulma, app.py’de her istekte tenant’a göre davranma.
9. **Modül aç/kapa:** Tenant’a göre `sales_assistant`, `return_exchange` vb. açıp ilgili modül fonksiyonlarına yönlendirme.
10. **Sistem prompt / kurallar:** Tenant’a özel `system_prompt_rules` (ve varsa politika dosyaları) kullanımı.
11. **Order approval / cancel_return / voice:** Spec’teki ileri modüller için aynı webhook + tenant + modül yapısı üzerinden genişleme.

---

## 5. Özet Tablo

| Konu | Durum | Sonraki adım |
|------|--------|--------------|
| Webhook (al + gönder) | ✅ | Deploy + canlı test |
| Mesaj DB (messages) | ✅ | - |
| Geçmiş konuşma → AI | ✅ | - |
| Panel (mesaj listesi) | ✅ | Müşteriye göre filtreleme |
| Tuba AI kuralları | ✅ | - |
| Test sipariş (test_orders) | ✅ | Canlı API’ye geçiş |
| Görsel (foto) analizi | Kısmen | Webhook + Vision akışı |
| Tenant / modül routing | Kod var, akışta yok | İleride tenant + modül açma |
| Deploy (Railway) | Beklemede | Deploy + env + webhook URL |

---

**Son güncelleme:** Şubat 2026  
**Kullanım:** Bu dosya “proje mantığı + nereden başlamalı + yol haritası” için tek referans olarak kullanılabilir. Adım adım ilerlerken TODO.md ve GECMIS_LOGLARI.md ile birlikte güncel tutulabilir.
