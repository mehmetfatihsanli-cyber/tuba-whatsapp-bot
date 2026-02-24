# Haber Bülteni – n8n Entegrasyonu (Planlama)

Bu dosya, panelde "Günlük haber bülteni" özelliği ve n8n haber otomasyonu entegrasyonu için toplanan bilgileri içerir. İleride uygulamaya geçerken buradan referans alınacak.

---

## 1. Mevcut n8n Otomasyonu

- **Ne yapıyor:** Kullanıcının belirlediği prompt’a göre her gün **saat 09:00**’da **Google** ve **LinkedIn**’den **son 24 saatte** yayınlanmış, sektörle ilgili haberleri topluyor.
- **Amaç:** Müşterilerin bu çıktıdan faydalanması; panel üzerinden abone olup her gün istedikleri haberleri (kendilerine uygun şekilde düzenleyerek) alabilmeleri.

---

## 2. Panel Tarafı – Hedef Görünüm ve Kullanım

- **Yeni bölüm:** Panelde "Haber bülteni" veya "Günlük haber" adında ayrı bir sekme/bölüm.
- **Arayüz sade olacak (n8n node ekranı gibi olmayacak):**
  - Kısa açıklama metni (örn. "Her gün saat 09:00'da sektörünüzle ilgili son haberler WhatsApp'tan size iletilecek.")
  - **Aç/Kapa:** "Günlük haber bültenini aç" toggle.
  - **İsteğe bağlı:** "Anahtar kelimeler" alanı (müşteri kendi sektörünü/ilgi alanını yazabilir).
  - **Kaydet** butonu.
- Kullanım: Haber bülteni sayfasına gir → Aç → İstersen anahtar kelimeleri yaz → Kaydet.

---

## 3. n8n ile Entegrasyon Yöntemleri

Entegrasyon HTTP üzerinden; hazır bir "n8n modülü" yok, sadece webhook/API sözleşmesi.

| Yöntem | Açıklama |
|--------|----------|
| **A) n8n bize haber veriyor** | n8n her gün 09:00’da haberi toplar, **bizim API’ye POST** atar (webhook). Biz "haber bülteni açık" olan tüm abonelere WhatsApp’tan göndeririz. Mevcut workflow’a sadece bir "HTTP Request" node eklenir. |
| **B) Biz n8n’i tetikliyoruz** | Backend 09:00’da n8n webhook’unu çağırır; n8n haberi üretir, bize döner; biz dağıtırız. Tetikleyici bizde olur. |

Başlangıç için **A** daha pratik: Zamanlama n8n’de kalır, sadece son adımda bizim webhook’a POST atılır.

---

## 4. Teknik Adımlar (Uygulama Yapılırken)

1. **Veritabanı:** Haber bülteni abonelikleri için tablo (örn. `news_subscriptions`): tenant/numara, açık/kapalı, anahtar kelimeler.
2. **Backend:**
   - Panelden ayar kaydetmek: `GET/POST /api/news-subscription` (veya benzeri).
   - n8n’in haber paketini göndermesi: `POST /api/news-digest` (webhook) → abonelere WhatsApp ile iletim.
3. **Panel:** Tek sayfa; toggle + anahtar kelimeler + Kaydet (node arayüzü yok).
4. **n8n:** Workflow sonuna "HTTP Request" node: POST `https://<bot-adresi>/api/news-digest`, body = haber listesi (format aşağıda netleştirilecek).

---

## 5. Uygulamaya Geçerken Netleştirilmesi Gerekenler

Aşağıdaki bilgiler toplandığında webhook ve panel birebir tasarlanabilir:

1. **n8n’de haber çıktısı formatı**
   - Son adımda elinde hangi JSON/yapı var? Örnek:
     - `[ { "title": "...", "url": "...", "source": "Google" } ]`
   - Buna göre `POST /api/news-digest` için beklenen request body yazılacak.

2. **Tek liste mi, kişiye özel mi?**
   - **Tek liste:** n8n bir kere çalışır, bir liste üretir, bize gönderir; tüm abonelere aynı özet WhatsApp’tan gider. (İlk aşama için en basit.)
   - **Kişiye özel:** Her abone kendi anahtar kelimelerine göre farklı haber alır; n8n’in parametreyle çalışması veya abone bazlı çağrı gerekir.

3. **n8n nerede çalışıyor?**
   - n8n Cloud / kendi sunucu. Önemli olan: n8n’in dışarıya HTTP isteği atabilmesi (bizim API’ye). Webhook URL’i (Railway vb.) belli olunca n8n’e yazılacak.

4. **Panelde “müşteri” kim?**
   - Tek kiracı (Tuba) mı, ileride çok kiracılı mı? Buna göre abonelik kaydı hangi kullanıcı/numara/tenant_id ile ilişkilendirilecek.

---

## 6. Özet

- **Özellik:** Günlük haber bülteni; panelde aç/kapa + isteğe bağlı anahtar kelimeler; teslimat WhatsApp.
- **n8n rolü:** Haberi toplamak/üretmek; teslimat ve abonelik bizim uygulama + panel.
- **Entegrasyon:** HTTP webhook (n8n → bizim API veya tersi); node’lu arayüz yok, sadece form.
- **Sonraki adım:** Yukarıdaki 4 madde (format, tek/kişiye özel, n8n yeri, müşteri modeli) netleşince DB şeması, API sözleşmesi ve panel ekranı detaylandırılacak.

---

*Son güncelleme: 2026-02-08*
