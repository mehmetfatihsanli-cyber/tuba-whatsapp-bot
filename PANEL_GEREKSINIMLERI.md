# Panel Gereksinimleri – Projeye Göre

Bu doküman: **Tuba Hanım’a / müşteriye verilecek panel**in ne olması gerektiğini tanımlar. Şu anki panel sadece iskelet; aşağıdakiler hedeftir.

---

## 📍 Panel değişikliklerini nereden takip edeceğiz?

**Bu dosya:** `PANEL_GEREKSINIMLERI.md`

- "Şu olmadı", "bunu değiştir", "burayı ekle" dediğin her şeyi aşağıdaki **"Panel – Yapılacaklar / Değişiklik listesi"** bölümüne yazacağız.
- Cursor’a panel ile ilgili bir şey söyleyeceğin zaman: **"@PANEL_GEREKSINIMLERI.md’deki yapılacaklara bak, şunları yap"** veya **"PANEL_GEREKSINIMLERI’ye şunu ekle: …"** diyebilirsin.
- Liste güncellendikçe yapılanlar işaretlenir; böylece ne kaldığı hep buradan görülür.

---

## Panel kimin için?

- **Tuba Hanım** (veya mağaza yetkilisi): WhatsApp’a gelen mesajları görmek, gerekince cevap yazmak veya konuşmayı devralmak için.

---

## Olması gerekenler (projeye göre)

### 1. Müşteri listesi (sol taraf)
- Tüm **konuşma yapılan numaralar** (benzersiz).
- Her satırda: **numara** + (isteğe) **son mesaj özeti** veya **son mesaj tarihi**.
- En son yazan en üstte veya en altta tutarlı sıra.
- Tıklanınca o müşteriyle olan **tüm konuşma** açılsın.

### 2. Konuşma alanı (sağ taraf)
- Seçilen numaraya ait **gelen (müşteri) / giden (bot veya Tuba)** mesajlar.
- **Kronolojik** sıra (eskiden yeniye).
- Gelen/giden **görsel ayrım** (farklı renk veya hiza).
- Mümkünse **mesaj saati** görünsün.

### 3. Panelden mesaj gönderme
- Seçili numaraya **Tuba’nın yazacağı metin** + **Gönder** butonu.
- Gönderilen mesaj hem WhatsApp’a gitsin hem listede **hemen** görünsün (beklemeden).

### 4. Başlık ve bilgi
- Sayfada net **“Tuba Butik – Canlı Panel”** (veya benzeri) başlığı.
- Kısa bilgi: “Son X mesaj gösteriliyor” veya “Otomatik yenilenir”.

### 5. Yenileme
- **Yenile** butonu veya otomatik aralıklı yenileme (şu an 5 sn).
- Hata olursa kullanıcıya **sessizce yeniden dene** veya “Bağlantı hatası” gibi kısa mesaj.

### 6. (İleride) Ek özellikler
- **Sipariş bilgisi:** Numaraya tıklanınca ButikSistem’den son siparişler (varsa) kısa özet.
- **“Konuşmayı devral”:** Bu numara için bot’u sustur, sadece panelden yanıt ver (spec’te “manuel müdahale”).
- **Arama:** Numaraya veya mesaj metnine göre filtre.

---

## Şu anki panelde ne var / ne eksik?

| Özellik | Durum |
|--------|--------|
| Müşteri listesi (numara) | Var (son 50 mesajdan benzersiz) |
| Numaraya tıklayınca mesajlar | Var |
| Gelen/giden ayrımı | Var (renk) |
| Panelden mesaj gönderme | Var (altta kutu + Gönder) |
| Başlık / “Panel” hissi | Eksik (sadece “Müşteriler” yazısı) |
| Son mesaj özeti / tarih (sidebar) | Eksik |
| Mesaj saati | Eksik |
| Yenile butonu | Eksik |
| “Son 50 mesaj” bilgisi | Eksik |
| Sipariş / devralma | Yok (ileride) |

---

## Panel – Yapılacaklar / Değişiklik listesi

*(“Şunu yap, bunu değiştir” dediğin maddeler buraya eklenir; yapıldıkça [x] işaretlenir.)*

### Görünüm / metin
- [ ] Başlık veya “Panel” hissi ekle (şu an sadece “Müşteriler” var)
- [ ] “Son 50 mesaj gösteriliyor” veya benzeri bilgi metni
- [ ] Her mesajın yanında **mesaj saati** göster
- [ ] Sol listede (müşteri satırında) **son mesaj özeti** veya **son mesaj tarihi**

### İşlev
- [ ] **Yenile** butonu ekle (sayfayı yenilemeden listeyi/mesajları tazelemek için)

### İleride
- [ ] Sipariş bilgisi (numaraya tıklanınca ButikSistem’den son siparişler)
- [ ] “Konuşmayı devral” (bu numara için bot’u sustur)

---

## Sonuç

“Böyle panel mi olur?” sorusunun cevabı: **Şu anki hali sadece minimum çalışan versiyon.** Projeye göre müşteriye/Tuba’ya verilecek panel için başlık, bilgi metni, yenile butonu, mümkünse son mesaj özeti ve mesaj saati eklenmeli; ileride sipariş ve “devral” özellikleri planlanmalı.

Son güncelleme: Şubat 2026
