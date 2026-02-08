# Geçmiş Logları ve Konuşma Geçmişi

Bu doküman, Tuba WhatsApp Bot'ta mesaj loglarının nerede tutulduğunu, nasıl kullanıldığını ve konuşma geçmişinin AI'ya nasıl verildiğini açıklar.

---

## 1. Logların Saklandığı Yer

### Supabase tablosu: `messages`

Tüm WhatsApp mesajları (gelen ve giden) Supabase'deki **`messages`** tablosunda tutulur.

| Alan           | Açıklama                          |
|----------------|-----------------------------------|
| `phone`        | Müşteri telefon numarası          |
| `message_body` | Mesaj metni                       |
| `direction`    | `inbound` (gelen) / `outbound` (giden) |
| `created_at`   | Kayıt zamanı (Supabase otomatik)  |

**Kayıt noktaları:**
- **app.py** – Webhook'ta gelen mesaj alındığında → `direction: inbound`
- **app.py** – Bot cevabı WhatsApp'a gönderildikten sonra → `direction: outbound`
- **app.py** – Panelden manuel mesaj gönderildiğinde → `direction: outbound`

---

## 2. Geçmişi Kullanan Yerler

### Panel (`/panel`)

- **API:** `GET /api/customers`
- Son 50 mesajı `created_at` azalan sırada çeker.
- Panel bu listeyi kullanarak mesaj kutusunda gösterir (şu an müşteri bazlı ayrım yok).

### AI Asistan (`modules/ai_assistant.py`)

- **Parametre:** `mesaj_olustur(..., gecmis_konusma=None, ...)`
- `gecmis_konusma` doluysa `_context_olustur()` ile Claude'a "Önceki Konuşma: ..." olarak eklenir.
- Böylece bot aynı müşteriyle daha önce ne konuşulduğunu bilerek cevap verebilir.

---

## 3. Mevcut Durum

| Özellik                    | Durum |
|----------------------------|--------|
| Mesajların DB'ye yazılması | ✅ Yapılıyor (`messages` tablosu) |
| Panelde mesaj listesi      | ✅ Son 50 mesaj gösteriliyor |
| AI'ya geçmiş konuşma verilmesi | ✅ Kodda parametre var; **app.py** geçmişi çekip geçirmiyordu → **düzeltildi** (aşağıda) |

---

## 4. Geçmiş Konuşmanın AI'ya Verilmesi

**app.py** içinde her mesajda:

1. `sender_phone` ile ilgili son **N** mesaj (örn. son 10 veya 20) Supabase'den alınır.
2. Bunlar kronolojik sırada metin olarak birleştirilir.
3. `ai_assistant.mesaj_olustur(..., gecmis_konusma=bu_metin)` ile AI'ya verilir.

Böylece "Siparişim nerede?", "İade nasıl yapacağım?" gibi sorularda önceki mesajlar dikkate alınır.

---

## 5. PROJECT_SPEC ile Fark

**PROJECT_SPEC.md** içinde `conversations` tablosu tanımlı (tenant_id, module_used, processing_time_ms vb.).  
Uygulama şu an **`messages`** tablosunu kullanıyor; tenant/modül bilgisi bu tabloda yok. İleride `conversations` tablosu eklenirse loglama oraya da yazılabilir.

---

## 6. Özet

- **Loglar:** Supabase `messages` tablosunda (phone, message_body, direction, created_at).
- **Panel:** `/api/customers` ile son 50 mesajı gösterir.
- **AI:** `gecmis_konusma` ile önceki konuşma context'i alır; app.py bu geçmişi DB'den çekip asistanına verir.

Son güncelleme: Şubat 2026
