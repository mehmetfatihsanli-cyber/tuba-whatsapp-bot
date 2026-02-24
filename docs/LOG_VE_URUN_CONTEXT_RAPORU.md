# Log ve Ürün Context Raporu (Değişiklik Yok – Sadece Bakış)

**Tarih:** Şubat 2026  
**İstek:** (1) Satın alma / “modeller” tarzı mesajlarda token harcaması ve belirsiz müşteri riski; (2) Model şu an Tuba XML’ine bakıyor mu, müşteri ne istiyorsa ona göre cevap verebiliyor mu?

---

## 1. Loglardan Görünenler

Örnek akış (satın alma / ürün soruları):

| Müşteri mesajı | Akış | Claude çağrıldı mı? |
|----------------|------|----------------------|
| Merhaba abiye modellerimizden neler var acaba | basit → karmaşık_cevap | Evet (sabit kalıba uymadı) |
| Reklamlarda gördüğüm kırmızı abiyenizi almak istiyorum bedenler mevcut mu acaba | basit → karmaşık_cevap | Evet |
| Leda modeli | basit → karmaşık_cevap | Evet |

Yani “abiye / modeller / ürün / beden” gibi satın alma niyetli mesajların **hepsi Claude’a gidiyor**; her biri 1 API çağrısı = token maliyeti.

**Belirsiz müşteri riski:** Müşteri “bir şeyler almak istiyorum”, “neler var?”, “güzel bir şey önerir misiniz” gibi net olmayan mesajlar yazarsa, model uzun açıklamalar veya çok soru sorarak cevap verebilir. Her gelen mesaj = yeni Claude çağrısı. 5–10 tur “ne istiyorsunuz?” / “hangi kategori?” = 5–10× token. Bu da **token harcamasını ciddi artırır**.

---

## 2. Model Şu An Tuba XML’ine / Ürün Listesine Bakıyor mu?

**Hayır.** Şu anki akışta modele giden CONTEXT sadece:

- **Önceki konuşma** (son 12 mesaj)
- **Müşteri sipariş bilgisi** (varsa, en fazla 5 sipariş)

**Ürün listesi, XML veya Pinecone çıktısı CONTEXT’e eklenmiyor.**  
Kod: `_context_olustur(gecmis, siparis)` – sadece `gecmis` ve `siparis` kullanılıyor. Pinecone’daki `benzer_urunleri_bul` veya Tuba XML’i hiç çağrılmıyor; dolayısıyla modele **ürün verisi gitmiyor**.

Sistem promptunda (“CONTEXT’te ürün listesi/XML verilmişse ona göre cevapla”) ürün verisi kullanması söyleniyor ama **biz CONTEXT’e ürün/XML eklemediğimiz için** model elinde sadece:

- Genel mağaza kuralları (iade, değişim, kargo)
- Konuşma geçmişi
- Varsa sipariş listesi

ile cevap veriyor. “Leda modeli”, “kırmızı abiye”, “abiye modelleri neler var?” gibi sorularda **gerçek katalog/XML verisi yok**; model ya genel/ tahmini cevap veriyor ya da “ürün adı/kategori yazın” gibi yönlendiriyor. Yani **müşteri ne istiyorsa ona göre ürün bazlı, XML’den beslenen bir dönüş şu an yok**.

---

## 3. Token Tasarrufu ve “Ne İstediğini Bilmeyen Müşteri” İçin Modeli Hangi Yönlerde Akıllandırabiliriz?

Aynı performansı koruyup token’ı kısmak ve belirsiz müşteriyi toplamak için fikirler (sadece fikir; değişiklik yapılmadı):

**A) Prompt ile yönlendirme (kısa, tek soruda toplama)**  
- “Müşteri belirsiz veya genel soru sorduğunda (neler var, bir şeyler almak istiyorum, modeller neler): Uzun açıklama yapma. Tek cümleyle kategorileri söyle ve tek net soru sor: Hangi kategori veya ürün adı? (abiye / günlük / aksesuar vb.)”  
- Böylece 3–4 tur yerine 1–2 turda netleşir; Claude çağrı sayısı ve token azalır.

**B) Sabit cevap genişletme (Claude’a hiç düşürmeden)**  
- “Neler var?”, “Modelleriniz neler?”, “Abiye modelleri neler?” gibi kalıplar için **sabit** kısa cevap: “Abiye, günlük giyim ve aksesuar kategorilerimiz var. İlgilendiğiniz kategori veya ürün adını yazarsanız detay verebilirim.”  
- Bu mesajlar Claude’a gitmez → token sıfır; belirsiz müşteri de tek adımda yönlendirilir.

**C) CONTEXT’e ürün verisi ekleme (XML / Pinecone)**  
- **Pinecone:** Mesajda ürün/abiye/model geçiyorsa `benzer_urunleri_bul(mesaj)` ile 3–5 ürün alınıp CONTEXT’e kısa liste (isim, fiyat, stok) eklenebilir. Model “Leda modeli”, “kırmızı abiye” gibi sorularda **gerçek ürünle** cevap verir; tek cevapta bitirme şansı artar, tur sayısı ve token azalır.  
- **XML:** İsterseniz belirli kategoriler için XML’den kısa ürün özeti (isim, fiyat, stok) kesilip CONTEXT’e konabilir.  
Bu sayede “müşteri ne istiyorsa ona göre dönüş” **ürün verisiyle** mümkün olur; şu an bu yok.

**D) “Belirsiz” tespiti (ileride)**  
- Mesaj çok kısa ve genel (“neler var”, “bir şey”) ise önce sabit kısa cevap + tek soru; net ürün/kategori gelince Claude + (opsiyonel) ürün context’i çağrılabilir. Böylece belirsiz turda token harcanmaz.

---

## 4. Kısa Cevaplar

| Soru | Cevap |
|------|--------|
| Satın alma / “modeller” yazınca token gidiyor mu? | Evet. Bu mesajlar sabit kalıba uymadığı için hep Claude’a gidiyor; her biri 1 çağrı = token. |
| Ne istediğini bilmeyen müşteri çok token harcatır mı? | Evet. Uzun soru-cevap turu = her tur 1 Claude çağrısı. Modeli “kısa, tek soruda topla” ve sabit cevaplarla yönlendirirsek token düşer. |
| Model şu an Tuba’nın XML’ine bakıyor mu? | Hayır. CONTEXT’e sadece konuşma + sipariş verisi gidiyor; XML veya ürün listesi eklenmiyor. |
| Müşteri ne istiyorsa ona göre (ürün bazlı) dönüş yapılabiliyor mu? | Şu an **ürün verisi olmadan** sadece genel kurallar ve konuşma ile cevap veriliyor. XML/Pinecone CONTEXT’e eklenirse “yazan müşteri ne istiyorsa ona göre” ürün bazlı dönüş mümkün olur. |

Bu rapor sadece mevcut koda ve loglara bakarak hazırlandı; **hiçbir kod veya config değişikliği yapılmadı.**
