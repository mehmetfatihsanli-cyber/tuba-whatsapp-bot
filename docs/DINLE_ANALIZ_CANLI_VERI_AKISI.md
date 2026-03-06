# Dinle + Analiz → Canlı Geçiş: Veri Nasıl İşleniyor, Model Nasıl Kullanıyor?

Bu dokümanda: **Dinle + Analiz** modunda biriken verilerin **Canlı** moda geçildiğinde sisteme ve modele **nasıl taşındığı**, hangi kurallarla kullanıldığı anlatılıyor.

---

## 1. Kısa cevap

- **Dinle + Analiz’te biriken veriler** veritabanında (Supabase) saklanıyor; mod değişince silinmiyor.
- **Canlı’ya geçtiğinde** her gelen mesajda model, **son N günün** (panelde seçilen 2/7/14 gün) analiz özetini prompt’a ekli olarak çağrılıyor. Yani “bir haftalık Dinle + Analiz” verisi **dolaylı** olarak Canlı’da kullanılıyor: seçilen dönem (2, 7 veya 14 gün) özetlenip modele veriliyor; paneldeki seçim tenant başına kaydedilir.
- Özet: **niyet dağılımı** (question, purchase_signal, return_request vb.), **duygu dağılımı** (positive, neutral, angry vb.) ve **örnek mesaj metinleri**; model bunu “bağlam” olarak görüyor, kuralları gevşetmeden müşteri eğilimine uyum sağlıyor.

**Netleştirme :**  
“7 gün analiz edilip en önemli kısımlar alınarak son 2 güne göre kullanılıyor” **değil**. Panelde "Son X gün" seçimi hem rapor hem modele giden özet penceresini belirler; 7 veya 14 gün seçilirse o dönem özetlenir.

---

## 2. Dinle + Analiz’te veri nereye yazılıyor?

**Tablo: `message_analyses`**

- Her mesaj (metin veya görsel) AI’dan geçtiğinde şu alanlar kaydedilir:
  - `tenant_id`, `phone`, `line` (sales / exchange)
  - `message_body` (mesaj metni, kısa tutulabilir)
  - `sentiment` (positive, neutral, negative, angry)
  - `intent` (question, purchase_signal, complaint, return_request, greeting)
  - `urgency` (low, medium, high)
  - `created_at`

Yani **7 gün Dinle + Analiz** çalışırsa, o 7 günün tüm analiz kayıtları bu tabloda durur. Mod **Canlı**’ya alındığında bu kayıtlar **silinmez**; sadece artık yeni gelen mesajlara **cevap da gönderilir**.

---

## 3. Canlı’ya geçildiğinde bu veri “alınıyor” mu?

**Evet, ama “son N gün” özeti olarak.**

- Canlı’da da her mesajda AI çağrılırken **aynı mekanizma** kullanılır: `get_analysis_summary_for_prompt(tenant_id, line, days=get_analysis_summary_days(tenant_id))`; **days** paneldeki seçim veya env ile belirlenir.
- Yani **Dinle + Analiz’e özel** bir “şimdi 7 günlük veriyi yükle” adımı yok; her zaman **son 2 gün** (kodda `days=2` sabit) için özet üretilir ve prompt’a eklenir.
- Sonuç:
  - 7 gün Dinle + Analiz çalıştıysan, **tüm 7 gün** `message_analyses`’te durur.
  - Canlı’ya geçtiğin ilk günlerde modele giden özet, **son 2 gün** = büyük ihtimalle hâlâ Dinle + Analiz dönemine ait kayıtları içerir.
  - Zaman geçip Canlı’da da mesajlar birikince, özet giderek “son 2 günün” hem Dinle hem Canlı dönemini karışık gösterir (çünkü Canlı’da da her cevap sonrası analiz `message_analyses`’e yazılmıyor gibi görünüyor – kontrol ettim, sadece Dinle + Analiz’de insert var. Yani Canlı’da gelen mesajlar analiz edilir, cevap gider; ama analiz sonucu message_analyses’e yazılıyor mu? Evet – aynı blokta analysis varsa message_analyses’e insert yapılıyor, bot_mode’a bakılmıyor orada. So in live mode we also insert into message_analyses when we have analysis. So the table keeps growing with both listen_analyze and live messages. And get_analysis_summary_for_prompt just takes last 2 days of that table. So when they switch to live, the "last 2 days" might still be mostly listen_analyze data, then over time it becomes a mix. Good.)

---

## 4. “Bir haftalık veri” nasıl işleniyor? (Özet nasıl üretiliyor?)

**Fonksiyon: `get_analysis_summary_for_prompt(tenant_id, line, days=2)`**

- **Kaynak:** `message_analyses` tablosu; filtre: `tenant_id`, `line` (sales veya exchange), `created_at >= son N gün`. N, panelde seçilen **analiz özeti penceresi** (2, 7 veya 14 gün; tenant ayarı `analysis_summary_days` veya env `ANALYSIS_SUMMARY_DAYS`, varsayılan 2).
- **İşleniş:**
  1. Son N gündeki kayıtlar (en fazla 250) çekilir.
  2. **Niyet (intent)** ve **duygu (sentiment)** için adet sayılır (örn. question:20, purchase_signal:15; neutral:30, positive:10).
  3. En fazla 2 tane kısa **örnek mesaj metni** (message_body, 60 karakter) alınır.
  4. Tek bir kısa cümle üretilir, örn.  
     *“Son 2 günde 45 mesaj. Niyet: question:20, purchase_signal:15, return_request:5. Duygu: neutral:30, positive:10, negative:5. Örnek: merhaba bu ürün var mı | beden değişimi istiyorum.”*
  5. Bu metin **en fazla 420 karakter** (ANALYSIS_SUMMARY_MAX_CHARS) ile sınırlanır; token tasarrufu için.

Yani “bir haftalık veri” **doğrudan** modele gitmiyor; sadece **son 2 gün** bu şekilde özetlenip gidiyor. Panelde 7 veya 14 gün seçilirse o dönemin tamamı özetlenip modele gider.

---

## 5. Bu özet modele nasıl veriliyor? Hangi kurallar geçerli?

**Prompt’a ekleme (ai_assistant.py)**

- Özet metni, sistem prompt’unun **sonuna** şu blokla eklenir:  
  **"--- Son analiz özeti (Dinle+Analiz, bu hat) ---"** + özet metni.
- Üstte bir **öncelik metni** var (_PROMPT_HIERARCHY):
  - (1) Temel kurallar ve mağaza bilgisi **her zaman geçerli**; ihlal etme.
  - (2) Panelden gelen ek talimatlar bunları tamamlar; çakışırsa **temel kural öncelikli**.
  - (3) **Son analiz özeti sadece bilgi/bağlam**; müşteri eğilimlerine uyum sağla **ama kuralları gevşetme**.

Yani model:
- Son 2 günde ne tür niyetler/duygular geldiğini ve 1–2 örnek mesajı **bağlam** olarak görüyor.
- Buna göre daha uyumlu cevap verebilir (örn. çok “return_request” varsa iade/değişim tonuna daha hazırlıklı).
- Ama **iade süresi, kargo ücreti, yönlendirme** gibi kurallar özet yüzünden değişmez; öncelik hep temel kurallarda.

---

## 6. Özet tablo

| Soru | Cevap |
|------|--------|
| Dinle + Analiz’te biriken veriler Canlı’ya taşınıyor mu? | Veritabanında kalıyor; Canlı’da da **aynı tablo** kullanılıyor. Taşıma “yeni tabloya” değil, **özetin prompt’a eklenmesi** şeklinde. |
| Bir haftalık veri tek seferde modele veriliyor mu? | Evet (seçime göre). **Seçilen dönem** (panelde seçilen 2/7/14 gün) özetlenip prompt’a ekleniyor. Seçim tenant başına kaydedilir. |
| Özet nasıl işleniyor? | Niyet/duygu sayıları + en fazla 2 örnek mesaj; tek paragraf, max 420 karakter. |
| Canlı’da model bu veriyi nasıl kullanıyor? | “Son analiz özeti” olarak sistem prompt’una ekleniyor; model bunu **bağlam** kabul ediyor, kuralları gevşetmeden müşteri eğilimine uyum sağlıyor. |
| 7 günü modele yansıtmak istersek? | Panel → Dinleme Analiz Raporu → "Son X gün" seçin; 7 veya 14 seçilirse webhook bu pencereyi kullanır. |

---

## 7. Akış özeti (7 gün Dinle + Analiz, sonra Canlı)

1. **1–7. gün (Dinle + Analiz):** Gelen her mesaj AI’dan geçiyor, sentiment/intent/urgency + message_body `message_analyses`’e yazılıyor; müşteriye cevap gitmiyor.
2. **8. gün (Canlı’ya alındı):** Panelden ilgili hat “Canlı” yapılıyor. Yeni gelen mesajda:
   - `get_analysis_summary_for_prompt(tenant_id, line, days=get_analysis_summary_days(tenant_id))` çağrılıyor → **panelde seçilen gün** (örn. 7) için son 7 gün özetleniyor.
   - Bu özet + satış/değişim prompt’u + diğer context’ler modele veriliyor; model cevap üretiyor ve cevap müşteriye gidiyor.
3. **Sonraki günler:** Canlı modda **yeni analizler `message_analyses` tablosuna yazılmıyor** (sadece Dinle + Analiz modunda yazılıyor). Bu yüzden Canlı’ya geçtikten sonra modele giden özet **hep aynı kalır**: Dinle + Analiz’in **son 2 günü**ne ait özet. Model, Canlı’da da bu “son 2 günlük Dinle verisi”ni bağlam olarak kullanır; Canlı’daki yeni mesajlar bu tabloya eklenmediği için özete yansımaz.

Bu doküman, “Dinle + Analiz bir hafta çalıştı, sonra Canlı’ya aldık; bu bir haftalık veri modele nasıl gidiyor?” sorusunun cevabını toplar.
