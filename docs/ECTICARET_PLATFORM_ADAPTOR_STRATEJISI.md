# E-ticaret Platform Adaptör Stratejisi: Ortak Yapı + Manuel Kurulum

**Fikir:** İkas, Butik Sistem, Tiximax vb. mevcut entegrasyonları kullanan firmalar için resmi API dokümantasyonlarını alıp **platform bazlı adaptörler** yazalım. **API bilgilerini müşteri panele girmesin;** biz müşteriden alıp **manuel olarak** sisteme işleyelim. Her müşteri için **sil baştan ayar/cod yazmayalım** – **ortak bir durum**: Butik Sistem’i referans alan aynı işleyiş, yeni platformlara (İkas, Tiximax) aynı arayüzle adaptör ekleyerek uygulanır; her yeni müşteri için sadece o tenant’ın platformu + API bilgileri (bizim girdiğimiz) değişir.

---

## 1. Model Özeti

| Şu an | Hedef |
|-------|--------|
| Tek backend (Butik Sistem), env'den global BUTIK_* | Her platform için **tek** adaptör (Butik, İkas, Tiximax, …); **biz** müşteriden API bilgilerini alıp **manuel** tenant ayarına yazıyoruz. Müşteri panele API girmiyor. |

**Bizim taraf:** Yeni müşteri gelir → Hangi e-ticaret sistemi? (Butik / İkas / Tiximax) → Müşteriden API URL, API key veya kullanıcı/şifre **biz alırız** (mail, güvenli kanal) → **Biz** bu bilgileri ilgili tenant için sisteme giriyoruz (admin panel veya DB). Kod ve işleyiş ortak; sadece tenant bazlı konfigürasyon değişir. **Sil baştan** yok.

---

## 2. Teknik Çerçeve

### 2.1 Ortak arayüz (AI asistanın beklediği)

Asistan şu an Butik client üzerinden iki şey kullanıyor:

- **Sipariş:** Telefona göre sipariş listesi (iade/değişim, takip).
- **Ürün/stok:** Model kodu (örn. 2209_t1) ile ürün bilgisi, fiyat, stok, link.

Tüm platform adaptörleri **aynı contract**'ı uygular; asistan hangi platform olduğunu bilmez.

Örnek soyut arayüz:

- `check_order_by_phone(phone, days=30)` → `{ "found": bool, "orders": [...] }`
- `get_product_by_model_code(model_code)` → `{ "ad", "fiyat", "stok", "product_url", ... }` veya `None`

(Butik’teki mevcut metod isimleri ve dönüş formatı referans alınabilir; İkas/Tiximax için aynı formata map edilir.)

### 2.2 Platform adaptörleri (dokümantasyondan)

| Platform | Kaynak | Ne yapılacak |
|----------|--------|----------------|
| **Butik Sistem** | Mevcut kod + resmi doküman | Zaten var; constructor’ı **tenant’a özel URL/user/pass** alacak şekilde evrilir (env yerine parametre). |
| **İkas** | İkas API dokümantasyonu | Sipariş + ürün/stok endpoint’leri dokümana göre yazılır; aynı arayüzü implement eder. |
| **Tiximax** | Tiximax API dokümantasyonu | Aynı mantık. |
| **Diğerleri** | İlgili platformun resmi REST/API dokümanı | Aynı arayüz; yeni dosya: `modules/ikas_client.py`, `modules/tiximax_client.py` vb. |

Her adaptör **sadece resmi dokümantasyondaki** endpoint’leri ve auth yöntemini kullanır; müşteriye özel “özel entegrasyon” yazılmaz.

### 2.3 Tenant konfigürasyonu (bizim doldurduğumuz)

Veritabanında tenant başı e-ticaret ayarı tutulur. Örnek kolonlar:

- `ecommerce_backend`: `butik` | `ikas` | `tiximax` | `none`
- `ecommerce_api_url`: REST base URL
- `ecommerce_api_key`: API key (İkas/Tiximax vb. için)
- `ecommerce_api_user`, `ecommerce_api_pass`: Butik gibi kullanıcı/şifre kullananlar için

**Kim doldurur?** **Biz (operatör).** Müşteri panele API bilgisi girmiyor. İki seçenek:

- **Admin panel (sadece sizin erişiminiz):** Tenant seç → E-ticaret: platform + URL + key/user-pass → Test et → Kaydet. Müşteri panelinde bu ekran ya yok ya da sadece “Entegrasyon aktif” bilgisi gösterilir.
- **Doğrudan DB / migration:** Yeni müşteri için tenant kaydı oluşturulurken veya sonra bu alanlar (güvenli şekilde) doldurulur.

Webhook’ta mesaj gelince: `tenant_id` ile tenant’ın `ecommerce_backend` + credential’ları okunur → o platformun adaptörü aynı arayüzle oluşturulur (tenant’a özel URL/key) → asistan bu client’ı kullanır. **Ortak kod, tenant bazlı sadece config;** sil baştan yazım yok.

---

## 3. İş Akışı (Yeni müşteri)

1. Müşteri kayıt olur, panele girer.
2. **Biz:** Müşteriyle "Hangi e-ticaret sistemi?" (Butik/İkas/Tiximax) netleştirilir; API bilgileri **müşteriden biz alırız**. **Biz** sisteme manuel gireriz (admin/DB); Test et → Kaydet. Müşteri panele API girmez.
3. **Biz tarafında:** İlgili platform adaptörü + bu tenant credential'ları kullanılır; sil baştan kod yazılmaz. (Butik/Tiximax için de aynı mantık; sadece config farklı.)

---

## 4. Avantajlar

- **Müşteri başı özel entegrasyon yok:** Sadece dokümantasyona göre yazılmış, platform bazlı adaptörler.
- **Onboarding:** API bilgilerini biz alıp manuel giriyoruz; müşteri panele API girmiyor; siz “hangi platform?” + “API bilgileri” ile çalışırsınız.
- **Ölçeklenebilir:** Yeni platform eklemek = yeni adaptör (aynı arayüz) + panelde seçenek; tenant tablosunda yeni `ecommerce_backend` değeri.
- **Güvenlik:** API key/şifre tenant bazlı DB’de (veya şifreli) tutulur; env’de global key birikmez.

---

## 5. Adım Adım Yapılacaklar

1. **Ortak arayüzü netleştir:** `check_order_by_phone`, `get_product_by_model_code` imza ve dönüş formatını tek yerde (interface/protocol) tanımla; Butik client’ı buna uydur.
2. **Tenants tablosu:** `ecommerce_backend`, `ecommerce_api_url`, `ecommerce_api_key` (ve gerekiyorsa user/pass) kolonlarını ekle.
3. **Admin panel (sadece sizin):** E-ticaret ayar sayfası; tenant seçimi + platform + API alanları + test butonu. Müşteri panelinde bu ekran yok veya sadece "Entegrasyon aktif" bilgisi.
4. **Adaptör fabrikası:** `tenant_id` → tenant ayarları oku → ilgili adaptörü (İkas/Butik/Tiximax) tenant credential’ları ile oluştur → asistan bu client’ı kullansın.
5. **Platform dokümantasyonlarını işle:** İkas, Tiximax (ve varsa diğerleri) resmi REST API dokümanlarına göre sipariş + ürün/stok çağrılarını yaz; aynı arayüzü implement et.
6. **Butik’i tenant bazlı yap:** Constructor’da env yerine URL/user/pass parametre al; webhook’ta tenant’ın credential’ları ile oluştur.

Bu strateji ile mevcut entegrasyonları (İkas, Butik Sistem, Tiximax vb.) kullanan firmalar için sadece **dokümantasyonu işleyip adaptör yazmak** ve **API bilgilerini bizim manuel girmemiz** yeterli olur; her müşteri için ayrı proje veya sil baştan ayar yazmaya gerek kalmaz.

---

## 6. Manuel Kurulum + Ortak Yapı: Sorun Çıkar mı?

**Kısa cevap:** Teknik olarak **sorun çıkmaz**; ortak arayüz + tenant config tam da bunu sağlar. Operasyonel birkaç noktaya dikkat etmek yeterli.

**Olası noktalar (sorun değil, yönetilmesi gerekenler):**

| Konu | Açıklama |
|------|----------|
| **Bilgi toplama** | Müşteriden API URL/key’i almak için net bir süreç (hangi bilgiler, nereye gönderecek, güvenli kanal). Checklist veya kısa form işinizi kolaylaştırır. |
| **Şifre / key değişimi** | Müşteri API şifresini veya key’i değiştirirse sizin güncellemeniz gerekir. Müşteriye “Değiştirdiğinizde bize iletin” demek ve tek taraflı güncelleme yeterli. |
| **Ölçek (manuel giriş)** | Müşteri sayısı arttıkça her biri için bir kez manuel config girişi olur; kod değişmez, sadece iş yükü. İleride isterseniz “müşteri kendi API bilgisini girsin” opsiyonu eklenebilir. |
| **Güvenlik** | Tüm API key’ler sizde; DB’de erişimi kısıtlı tutun, hassas alanları (key/pass) isteğe bağlı şifreleyin. Müşteri panelinde bu alanlar gösterilmez. |

**Neden teknik sorun çıkmaz?**

- **Ortak durum:** Butik’teki `check_order_by_phone` / `get_product_by_model_code` aynı contract; İkas/Tiximax aynı arayüzü uygular. Yeni müşteri = aynı kod, sadece `ecommerce_backend` + credential farkı. Sil baştan yazım yok.
- **Referans:** Şu anki Butik işleyişi referans; yeni platformlar bu işleyişe adaptörle bağlanır. Mevcut akış bozulmaz, sadece client tenant’a göre seçilir.

**Özet:** Müşteriden API bilgisini manuel alıp sizin işlemeniz ve ortak yapıyı (Butik referans, platform adaptörleri) kullanmanız **sorun çıkarmaz**; sadece operasyonel süreci (bilgi toplama, key güncelleme, güvenlik) net tanımlamanız yeterli.

---

*Son güncelleme: 2026-02-08*
