# Butik Panel ve Sipariş Verisi – Nasıl Görürüz / Kontrol Ederiz?

**Durum:** Tuba’nın siparişleri gördüğü yer **Butik panel** (tm2.butiksistem.com – Sipariş yönetimi). Bu bir **web arayüzü**; veri arka planda Butik’in sunucusunda. Aynı sipariş verisine **REST API** (order/get vb.) ile de erişilebiliyor; bot zaten müşteri yazdığında bu API ile sipariş çekiyor.

---

## 1. Ben (asistan) bu veriyi nasıl “görebilirim”?

Ben **canlı olarak** Butik panele veya Butik API’ye bağlanıp sipariş listesini çekemiyorum. Şu seçenekler var:

| Yöntem | Açıklama |
|--------|----------|
| **Siz veriyi paylaşırsınız** | Ekran görüntüsü (bu ekran gibi) veya “şu an listede 25 sipariş var, 10’u kargoda, 15’i bekliyor” gibi özeti yazarsanız, buna göre yorum yaparım. |
| **Panelde “Sipariş özeti” sayfası** | Projeye (bizim panelde) bir sayfa veya API eklenir: Butik API’den son N siparişi çeker, tablo/özet gösterir. Siz o sayfaya bakarsınız; isterseniz çıktıyı kopyalayıp bana yapıştırırsınız, ben yorumlarım. |
| **Railway’de Butik bilgileri** | BUTIK_API_URL, BUTIK_API_USER, BUTIK_API_PASS zaten Railway’de (veya .env’de) tanımlıysa **bot** canlıda Butik’ten sipariş çekebiliyor. Bu, “benim görmem” için değil; müşteri yazınca botun sipariş göstermesi için. |

Yani: **“Sana bir şey söylediğimde sen kontrol edip bana bilgi ver”** için şu an tek yol, **sizin bana veri vermeniz** (ekran / özet / API çıktısı). Ben tarafında otomatik “Butik’e bağlanıp listeyi çek” özelliği yok; isterseniz projeye “Sipariş özeti” sayfası ekleyip siz oradan bakıp bana yapıştırırsınız.

---

## 2. Railway’e “bu kısım” için ne eklenebilir?

- **Butik API bilgileri (zaten olmalı):**  
  `BUTIK_API_URL`, `BUTIK_API_USER`, `BUTIK_API_PASS` – Botun sipariş sorgulaması için. Bunlar Tuba’nın panele giriş yaptığı Butik hesabıyla aynı sisteme gider; panel = arayüz, API = aynı veri.

- **Ek olarak (isterseniz):**  
  - Bizim panelde **“Sipariş özeti”** sayfası: Butik `order/get` (veya ilgili endpoint) ile son X siparişi çeker; durum (Sipariş alındı / Kargoya verildi), takip no vb. listelenir. Böylece Tuba hem Butik panelinde hem de bizim panelde (tek yerden) özet görebilir; siz de bu sayfanın çıktısını bana yapıştırarak “kontrol et” diyebilirsiniz.  
  - Bu sayfa için ek Railway değişkeni gerekmez; mevcut Butik credential’lar kullanılır.

---

## 3. Özet

- **Butik panel** = Tuba’nın gelen siparişleri, kargoya verilenleri ve bekleyenleri gördüğü arayüz (REST API değil, web UI).
- **Bana bu veriyi göstermenin yolu:** Siz ekran/özet/çıktı paylaşırsınız; veya projeye “Sipariş özeti” sayfası eklenir, siz oraya bakıp bana yapıştırırsınız.
- **Railway:** Butik API bilgileri tanımlı olsun (bot için). Ekstra “bu kısımı gör” için Railway’e yeni bir şey eklemek gerekmez; istenirse **uygulama tarafında** Sipariş özeti sayfası eklenir, veri yine aynı Butik API’den gelir.

İsterseniz bir sonraki adımda “Sipariş özeti” sayfasının nerede açılacağını (örn. panel menüsü) ve hangi alanları (sipariş no, müşteri, durum, takip no) göstereceğimizi netleştirip koda dökebiliriz.
