# Yol Haritası: Model (Claude) + Panel

Bu doküman: **1) Model neden standart mesaj veriyor, nasıl düzelecek** ve **2) Panel adım adım neler yapılacak** rehberi.

---

## 1. MODEL – Neden standart mesajlar gidiyor?

Kodda üç yol var; hepsi “sabit metin” dönebiliyor:

| Yol | Ne zaman? | Sonuç |
|-----|-----------|--------|
| **basit_cevap** | Mesaj “basit” sayılırsa (merhaba, selam, fiyat, stok…) | Sabit karşılama / fiyat / stok metni; **Claude çağrılmıyor**. |
| **iade/değişim sabit** | “İade” / “değişim” geçiyorsa | “Sipariş kodunuz?” benzeri sabit metin; **Claude çağrılmıyor**. |
| **Claude** | Karmaşık mesaj + iade sabiti yok | API’den cevap. **ANTHROPIC_API_KEY** yoksa veya hata olursa → “Yetkilimize yönlendiriyorum” sabiti. |

Yani model “çalışmıyor” hissi şunlardan olabilir:

- Railway’de **ANTHROPIC_API_KEY** tanımlı değil veya yanlış → Claude hiç çağrılmıyor, yönlendirme mesajı gidiyor.
- Mesajların çoğu **“basit”** sınıfında → Hep basit_cevap’taki sabit mesajlar gidiyor.
- Claude çağrılıyor ama **hata** (timeout, limit, key hatası) → Yine sabit yönlendirme mesajı.

---

## 2. MODEL – Yapılacaklar (sırayla)

### Adım 1: API key ve log kontrolü
- Railway **Variables** kısmında `ANTHROPIC_API_KEY` var mı kontrol et (gerçek key, test değil).
- Uygulama açılışında veya ilk mesajda “Claude API key yüklü mü?” log’u ekle (Railway loglarında görünsün).
- Claude’a girmeden önce / girdikten sonra / hata durumunda net log yaz (örn. `[AI] Claude çağrılıyor`, `[AI] Claude cevap verdi`, `[AI] Claude hatası: ...`).

### Adım 2: Daha fazla mesajı Claude’a göndermek (isteğe bağlı)
- Şu an: “Merhaba”, “Fiyat?”, “Stok?” → hep sabit cevap.
- İstenirse: “Fiyat” / “Stok” / “Ürün” gibi konularda da **karmaşık** sayıp Claude’a gönderebiliriz; cevaplar daha esnek olur (maliyet artar).

### Adım 3: Hata mesajını netleştirmek
- Claude hatası veya key yokken giden “Yetkilimize yönlendiriyorum” metnini aynen bırakabiliriz; sadece **log**ta sebebi yazalım (key yok / timeout / API hatası).

---

## 3. PANEL – Şu anki durum

- `/panel` açılıyor, `/api/customers` ile son 50 mesaj çekiliyor.
- **Sorun 1:** Sidebar’da müşteri listesi doğru değil (her mesajda liste tek elemana dönüyor).
- **Sorun 2:** Numaraya tıklayınca o numaranın mesajları filtrelenmiyor; tüm mesajlar tek kutuda.

---

## 4. PANEL – Yapılacaklar (adım adım)

### Aşama 1: Müşteri listesi (sidebar)
- API’den gelen 50 mesajdan **benzersiz numaraları** çıkar.
- Sidebar’da her numara tek satırda (veya “isim” yoksa “+90…”) listelensin.
- Tıklanabilir olsun (seçili numara vurgulansın).

### Aşama 2: Seçilen numaranın mesajları
- Bir numara tıklanınca sadece o numaraya ait mesajlar (inbound + outbound) gösterilsin.
- Kronolojik sıra (eskiden yeniye veya yeniden eskiye, tutarlı olsun).
- Gelen / giden ayrımı (bubble veya renk) kalsın.

### Aşama 3: Panelden mesaj gönderme
- Zaten var: `/api/send-message` (phone + text). Seçili numaraya yanıt kutusu eklenebilir: “Bu numaraya mesaj yaz” alanı + Gönder butonu.

### Aşama 4: Görünüm / kullanım
- Yenileme: Otomatik (aralıklı) veya “Yenile” butonu.
- Basit, sade arayüz; gerekirse “Tuba Butik Panel” başlığı.

---

## 5. Önerilen sıra

1. **Önce model:** API key + log düzeltmeleri → Railway’de test et → “Merhaba” dışında bir şey yaz (örn. “Siparişim nerede?”) → Claude cevabı veya en azından log’ta “Claude çağrılıyor” / “Claude hatası” görünsün.
2. **Sonra panel:** Sidebar müşteri listesi → numaraya tıklayınca mesajlar → (isteğe) panelden gönder.

Bu sırayla hem “model devreye girdi” netleşir hem panel adım adım ilerler.

Son güncelleme: Şubat 2026
