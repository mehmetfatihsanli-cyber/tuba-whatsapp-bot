# AI Asistan Yol Haritası: Model, Prompt ve Sürekli İyileştirme

Bu doküman üç hedefi tek çatıda toplar:
1. **Model + prompt'u tek yerde tanımlayıp sürekli güncelleyerek** doğru cevaplar almak  
2. **Müşteri kızdığında** botun anlayıp **Tuba Hanım'a manuel yönlendirme** yapması  
3. **Konuşmaları periyodik inceleyip** cevap veremediği durumlara göre **modeli/prompt'u akıllandırmak**

---

## Vizyon: Mağaza uzmanı, doğal ton, az yönlendirme

- **Mağaza uzmanı:** Asistan tek bir konuda uzman: Tuba Butik. Ürünler, iade/değişim, sipariş, kargo hepsini bilir; gelen her soruyu bu bilgiyle ve mantığa uygun cevaplar. İleride ürün listesi/XML context'e eklenerek model “ürünleri görerek” cevap verebilir.
- **Doğal ton:** Müşteri AI ile konuştuğunu biliyor olsa bile hissetmemeli; doğal, sıcak, insan gibi cevap.
- **Az yönlendirme:** Çok fazla müşteriyi Tuba Hanım'a yönlendirmemeliyiz; yönlendirme sadece gerçekten gerekli durumlarda (açık kızgınlık, küfür, yetkili talebi, çıkmaz).

---

## 1. Model ve Prompt Yönetimi

### Uygulandı (şu an)
- **Model:** `config.AI_MODEL` veya env `AI_MODEL` (varsayılan: `claude-3-5-sonnet-20241022`). `ai_assistant.py` bu değeri kullanıyor.
- **Prompt:** `prompts/tuba_system.txt` dosyasından okunuyor; yoksa varsayılan kısa prompt kullanılıyor. Prompt metni mağaza uzmanı + doğal ton + az yönlendirme hedeflerine göre yazıldı.

### Önceki durum (referans)
- Model: ai_assistant.py içinde sabit
- Prompt: sınıf içinde uzun string

### Hedef
- **Model seçimi:** Ortam değişkeni veya config (örn. `AI_MODEL=claude-3-5-sonnet-20241022`). İleride farklı model denemek kolay olsun.
- **Prompt tek kaynak:** Prompt'u kod dışında tutup sürekli güncelleyebileceğin bir yer:
  - **Seçenek A:** `prompts/tuba_system.txt` (veya `.md`) – dosyadan oku, deploy'da veya panelden güncelle.
  - **Seçenek B:** Supabase'de `prompts` tablosu (id, name, content, updated_at) – panelden "Tuba prompt'u" düzenle, kaydet; uygulama en günceli çeksin.
- **Sürüm / yedek:** Önemli değişikliklerde prompt'un eski halini saklamak (dosya kopyası veya DB'de version alanı). "Bu değişiklikten sonra cevaplar kötüleşti" dersen geri dönebilirsin.

### Uygulama adımları (kısa)
1. `config.py` veya `.env`: `AI_MODEL` ekle; `ai_assistant.py` modeli buradan alsın.
2. Sistem prompt'u `prompts/tuba_system.txt` (veya Supabase) taşı; uygulama başlarken/çağrı öncesi bu içeriği okuyup `system` olarak kullansın.
3. İsteğe bağlı: Panelde "Sistem prompt'u göster / düzenle" sayfası (Supabase kullanıyorsan doğrudan; dosya kullanıyorsan edit + restart veya basit bir "reload" endpoint).

---

## 2. Kızgın Müşteri → Tuba Hanım'a Yönlendirme (Manuel Geçiş)

### Amaç
Müşteri kızgın veya çok şikayetçi olduğunda bot **otomatik olarak** "Size özel yardım için yetkilimize (Tuba Hanım'a) yönlendiriyorum" deyip **manuel geçiş** yapsın; cevap vermeye çalışmasın.

### Nasıl "kızgın" anlaşılacak?

**2a) Kural tabanlı (hızlı, önce bunu ekle)**  
Mesajda aşağıdakilerden biri varsa **doğrudan yönlendir**, Claude'a sorma:

- Küfür / ağır hakaret (küfür listesi veya "***" gibi sansürlü ifadeler)
- Aşırı büyük harf (örn. mesajın çoğu BÜYÜK HARF)
- Açık kızgınlık kelimeleri: "yetkili", "müdür", "şikayet edeceğim", "tüketici hakları", "avukat", "savcılık", "çok kızdım", "rezalet", "berbat", "işe yaramaz", "talanız", "kandırdınız"
- Tekrarlayan şikayet: Son N mesajda (örn. 2–3) hep şikayet/olumsuzluk varsa (basit sayaç veya Claude'a "önceki mesajlar da şikayet mi?" diye sormak yerine kısa kurallarla)

**2b) Model tabanlı (Claude'a sormak)**  
Her mesajda Claude'a ek talimat ver:

- Sistem prompt'a ekle: "Eğer müşteri kızgın, küfür ediyor, yetkili istiyor veya hukuki tehdit ediyorsa cevap yazma; sadece şu sabit cevabı döndür: HANDOVER_MANUAL"
- Kod tarafında: Cevap `HANDOVER_MANUAL` ise sabit "Size özel yardım için yetkilimize yönlendiriyorum…" mesajını gönder ve gerekirse konuşmayı "insan devraldı" olarak işaretle (ileride panelde "Tuba'nın cevaplaması gerekenler" listesi için).

**Öneri:** Önce **2a** kurallarını ekle (hızlı ve öngörülebilir); gerekirse **2b** ile Claude'ı da devreye sok.

### Uygulandı (şu an)
- **2a kural tabanlı:** `ai_assistant.musteri_kizgin_mi(mesaj)` eklendi. Küfür/sansürlü ifade, aşırı büyük harf, açık kızgınlık kelimeleri (yetkili, müdür, şikayet edeceğim, avukat, rezalet vb.) varsa True dönüyor. `app.py` webhook'ta önce bu kontrol; True ise sabit `HANDOVER_MESAJI` gönderiliyor, Claude çağrılmıyor. Böylece yönlendirme sadece net durumlarda tetikleniyor.

### Teknik yerler
- **app.py:** Webhook'ta mesaj geldikten sonra, AI'ya göndermeden önce "kızgın mı?" kontrolü (örn. `ai_assistant.is_angry_or_escalate(mesaj, son_n_mesaj)`).
- **modules/ai_assistant.py:**  
  - `is_angry_or_escalate(...)` → True ise app.py sabit yönlendirme mesajı atar, Claude çağrılmaz.  
  - İsteğe bağlı: `karmaşık_cevap` içinde Claude cevabı `HANDOVER_MANUAL` ise aynı sabit mesaja çevir.

### İleride (opsiyonel)
- Supabase'de `conversations` veya `messages` üzerinde "handover_requested" / "answered_by_human" gibi alanlar: Tuba Hanım panelden "bunu ben cevapladım" işaretlesin; raporlarda "bot kaç konuşmada insana devretti" görünsün.

---

## 3. Sürekli İyileştirme: Konuşmaları İnceleme ve Modeli Akıllandırma

### Amaç
Periyodik (örn. 2 günde bir) konuşmalara bakıp "cevap veremedi / yanlış verdi" örneklerini toplamak ve bunlarla **prompt'u (ve gerekirse kuralları) güncellemek**.

### 3.1 Veri nerede?
- Tüm mesajlar zaten **Supabase `messages`** tablosunda: `phone`, `message_body`, `direction` (inbound/outbound), `created_at`.
- Konuşma = aynı `phone` + zaman sırasına göre mesajlar.

### 3.2 Nasıl inceleyeceksin?
- **Seçenek A – Panel genişletmesi:** Panelde "Son 7 gün konuşmaları" listesi; her satırda müşteri numarası + son mesaj özeti. Tıklayınca o numaranın tüm konuşması (müşteri / bot) kronolojik açılsın. Sen manuel "bu cevap yanlış / yetersiz" işaretle.
- **Seçenek B – Dış rapor:** Haftalık Supabase'den export (CSV/JSON) veya basit bir "konuşma listesi" script'i; sen Excel/not defterinde işaretleyip "bu örnekleri prompt'a ekleyeceğim" dersin.

### 3.3 "Cevap veremedi" örneklerini nasıl kullanacaksın?
- **Prompt'a ek kurallar:** "Şu durumda şöyle cevap ver: …" (örnek: "Müşteri 'kargo nerede' dediğinde önce sipariş kodu/sipariş listesi ver, sonra kargo takip linki söyle.")
- **Few-shot örnekler:** Sistem prompt'un sonuna "Örnek soru–cevaplar" ekle:
  - Müşteri: "Siparişim gelmedi"
  - Asistan: "Sipariş kodunuzu paylaşır mısınız? Numaranızdan siparişlerinize bakayım."  
  Böylece model benzer sorularda bu cevaba yaklaşır.
- **Kural tabanlı genişletme:** "Siparişim gelmedi" → zaten iade/değişim akışına benzer şekilde "sipariş kodu / numaradan listele" mantığını kodla; prompt'ta da "sipariş takip için önce sipariş kodu al" yaz.

### 3.4 Döngü (2 günde bir örnek)
1. Supabase'den son 2 günün konuşmalarını listele (panel veya script).
2. Oku: Hangi cevaplar yanlış/yetersiz/kaba?
3. Not al: "Şu soru → şu cevap verilmeli" veya "Bu durumda yönlendir".
4. Prompt'u güncelle: Yeni kural veya 1–2 few-shot cümle ekle; `prompts/tuba_system.txt` (veya DB) kaydet.
5. Deploy / restart; aynı senaryoyu tekrar test et.
6. Bir sonraki periyotta yeni "kötü" örnekleri aynı şekilde ekle.

### Teknik (kısa)
- Panel: `GET /api/customers` zaten var; isteğe `GET /api/conversation?phone=...` eklenebilir (o numaranın mesajlarını döner).
- İsteğe bağlı: `messages` tablosuna `feedback` alanı (örn. "bad_answer", "good", boş). Sen panelden "kötü cevap" işaretleyince ileride rapor "kötü cevap verilen konuşmalar" listesini çıkarır; prompt güncellemesi için kullanırsın.

---

## 4. Özet Yol Haritası (Sıra)

| Sıra | Ne yapılacak | Nerede |
|------|----------------|--------|
| 1 | Model adını config/env'e al (`AI_MODEL`) | config.py, ai_assistant.py |
| 2 | Sistem prompt'u dosyaya taşı (`prompts/tuba_system.txt`) | prompts/, ai_assistant.py |
| 3 | Kızgın müşteri kuralları: kelime/büyük harf kontrolü + HANDOVER | ai_assistant.py (is_angry_or_escalate), app.py |
| 4 | Claude'a "kızgınsa HANDOVER_MANUAL dön" talimatı + kodda yakala | tuba_system.txt, ai_assistant.py |
| 5 | Panel: Konuşma detayı API'si (`/api/conversation?phone=...`) | app.py |
| 6 | İsteğe: Panelde "son 2 gün konuşmalar" listesi + tıklayınca detay | app.py, panel.html |
| 7 | Periyodik inceleme notları + prompt güncelleme döngüsü (elle) | Sen; prompt dosyası / DB |

İstersen önce **1–2–3** ile model/prompt yönetimi ve kızgın müşteri yönlendirmesini uygulayalım; ardından panel/konuşma inceleme (5–6) ve iyileştirme döngüsünü (7) adım adım ekleriz.
