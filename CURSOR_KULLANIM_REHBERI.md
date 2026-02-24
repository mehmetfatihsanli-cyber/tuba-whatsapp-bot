# Cursor Kullanım Rehberi — Yazılım Bilmeyenler İçin

Bu rehber, **yazılım bilmeyen**, **sadece Türkçe komut veren** ve **kopyala-yapıştır** ile çalışan biri için hazırlandı. Cursor’u projenizi tamamlamak ve en iyi şekilde kullanmak için adım adım rehber.

---

## 1. Cursor Nedir, Ne İşe Yarar?

- **Cursor** = Kod yazan bir program (editör) ama içinde **yapay zeka asistanı** var.
- Siz **Türkçe ne istediğinizi yazarsınız**, o **kodu kendisi yazar veya değiştirir**.
- Sizin kod bilmeniz gerekmez; “şunu yap”, “bunu düzelt”, “şu sayfaya şu metni ekle” demeniz yeterli.

**Sizin için anlamı:** Projeyi tamamlamak için kod yazmak zorunda değilsiniz; Cursor’a Türkçe talimat verirsiniz, o gereken dosyaları düzenler.

---

## 2. Sohbet (Chat) Nasıl Kullanılır?

- Sağ tarafta **Chat** (Sohbet) paneli açık olur.
- Aşağıdaki kutuya **tamamen Türkçe** yazın. Örnekler:
  - “Panelde giriş sayfasına ‘Şifremi unuttum’ linki ekle.”
  - “WhatsApp’tan gelen mesajlara otomatik cevap veren kısmı güçlendir.”
  - “Bu hatayı düzelt: [hatanın metnini kopyala yapıştır].”
- **Enter**’a basın. Cursor düşünür ve ya kodu değiştirir ya da size adım adım ne yapmanız gerektiğini söyler.

**İpucu:** İstediğiniz şeyi **net ve cümleyle** yazın. “Şunu yap” yerine “Kayıt sayfasında e-posta kutusunun altına ‘Zaten üye misin? Giriş yap’ yazısı ekle” gibi.

---

## 3. @ ile Dosya veya Bağlam Vermek

Cursor’a “hangi dosyada / hangi konuda” çalışması gerektiğini söyleyebilirsiniz:

- Sohbet kutusuna **@** yazın.
- Açılan listeden:
  - **@DosyaAdı** — Örneğin `@app.py` veya `@panel.html` (ilgili dosyayı seçin).
  - **@BAGLAM_OZETI.md** — Proje özeti, nerede kaldığınız.
  - **@TODO.md** — Yapılacaklar listesi.

**Pratik kullanım:**  
Yeni sohbet açtığınızda veya ertesi gün devam ettiğinizde şunu yazın:

```
@BAGLAM_OZETI.md @TODO.md oku, son duruma göre devam edelim.
```

Böylece Cursor projenin nerede kaldığını bilir.

---

## 4. Kopyala-Yapıştır ile Çalışmak

- **Hata mesajı** alıyorsanız: Mesajın tamamını kopyalayıp sohbet kutusuna yapıştırın ve “Bu hatayı düzelt” veya “Bu ne anlama geliyor?” deyin.
- **Bir sayfanın veya kodun ekran görüntüsü** varsa: Görseli sohbet kutusuna sürükleyip bırakabilirsiniz; “Buna göre düzelt” diyebilirsiniz.
- **Başka birinden gelen talimat** (örn. “Şu özellik eklenmeli”): Metni olduğu gibi yapıştırıp “Bunu projeye uygula” diyebilirsiniz.

---

## 5. Cursor’u “En İyi Şekilde” Öğrenmek — 5 Alışkanlık

| # | Alışkanlık | Açıklama |
|---|------------|----------|
| 1 | **Her zaman Türkçe yazın** | Komutlarınızı Türkçe verin; bu projede Cursor size Türkçe cevap verecek şekilde ayarlı. |
| 2 | **Tek iş, tek mesaj** | Bir mesajda tek bir iş isteyin (örn. “Şu sayfaya buton ekle”). İş bitince sıradakini yazın. |
| 3 | **@ ile bağlam verin** | Özellikle yeni sohbet açtığınızda `@BAGLAM_OZETI.md @TODO.md` ile başlayın. |
| 4 | **Bitince TODO’yu güncelleyin** | Bir iş bittiğinde `TODO.md` dosyasındaki ilgili maddeyi “yapıldı” yapın veya Cursor’a “TODO.md’de şu maddeyi yapıldı işaretle” deyin. |
| 5 | **Hata / ekran görüntüsü paylaşın** | Bir şey çalışmıyorsa hatayı veya ekran görüntüsünü paylaşın; “buna göre düzelt” deyin. |

---

## 6. Sık Kullanabileceğiniz Cümleler

- “@BAGLAM_OZETI.md @TODO.md oku, son duruma göre devam edelim.”
- “Panel giriş sayfasında [şunu] değiştir.”
- “Şu hatayı düzelt: [hatayı yapıştır].”
- “Bu özelliği ekle: [özelliği kısaca anlat].”
- “Bunu basit Türkçe ile açıkla, kod bilmiyorum.”
- “Yaptığın değişikliği adım adım anlat.”
- “TODO.md’yi güncelle, şu madde yapıldı.”

---

## 7. Benim Size Nasıl Yardım Edebilirim?

- **Talimatları Türkçe ve adım adım** veriyorum; “şu dosyayı aç, şu satıra git” gibi.
- **Kod yazmanızı beklemiyorum**; “şunu kopyala şuraya yapıştır” derseniz tam olarak nereye yapıştıracağınızı söylerim.
- **Terim kullanırsam** kısa Türkçe açıklama da eklerim.
- **Proje dosyalarını** (BAGLAM_OZETI, TODO, panel, WhatsApp botu) biliyorum; “devam edelim” dediğinizde bu bağlama göre ilerlerim.

**Özet:** Cursor’u “en iyi şekilde” kullanmak için: Türkçe yazın, tek iş isteyin, @ ile bağlam verin, hata veya ekran paylaşın, TODO’yu güncel tutun. Geri kalanını Cursor halleder.

---

Son güncelleme: Şubat 2026
