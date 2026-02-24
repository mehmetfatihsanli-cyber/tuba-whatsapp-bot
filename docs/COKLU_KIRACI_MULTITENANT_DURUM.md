# Çoklu Kiracı (Multi-Tenant) Durum ve Zafer Örneği

Proje **tek kişiye değil, çoklu müşteriye (Tuba, Zafer, Ali, …) hizmet verecek** şekilde tasarlandı. "Tuba" örnek tenant olarak kullanılıyor; yapı zaten çoklu kiracıyı destekliyor. Bu dosyada mevcut durum, eksikler ve "Zafer bu hizmeti almak istiyor" için gerekli aksiyonlar özetleniyor.

---

## 1. Proje Çok Kişiye Hizmet Edecek – İmaj

- Kodda ve veritabanında **tenant_id** ile ayrım var; panel, mesajlar ve ayarlar kiracı bazlı.
- Tuba sadece **ilk / örnek tenant**; yeni müşteriler (Zafer vb.) aynı yapıyla eklenebilir.
- Hedef: Her müşteri kendi WhatsApp numarası, kendi sistem prompt’u ve kendi sohbetleriyle çalışsın.

---

## 2. Şu An Hazır Olanlar

| Bileşen | Durum | Açıklama |
|--------|--------|----------|
| **Tenants tablosu** | Var | `tenant_id`, `company_name`, `logo_url`, `email`, `password_hash`, `whatsapp_phone_number_id`, `whatsapp_waba_id`, `whatsapp_access_token` |
| **Kayıt (üyelik)** | Var | Landing’den Ad, E-posta, Şifre, Mağaza Adı → yeni tenant oluşturuluyor |
| **Giriş** | Var | E-posta + şifre veya tenant_id + şifre (tuba, zafer, ali fallback) |
| **Panel** | Var | Tüm veriler `tenant_id` ile filtreleniyor; her kiracı sadece kendi mesajlarını/ayarlarını görüyor |
| **Mesajlar / müşteriler** | Var | `messages`, `customers`, `conversation_state` hepsi `tenant_id` ile ayrılmış |
| **WhatsApp Ayarları (panel)** | Var | Ayarlar → WhatsApp: Phone Number ID, WABA ID, Token kaydediliyor (tenants tablosuna) |
| **Webhook’ta tenant eşlemesi** | Kısmen | Gelen mesajda `phone_number_id` → tenant; şu an **sadece env** ile (PHONE_ID→tuba, ZAFER_PHONE_ID→zafer) |
| **Gönderim (cevap atma)** | Kısmen | Cevap atarken **tek global** PHONE_ID ve META_TOKEN kullanılıyor; tenant’a özel numara/token yok |
| **Sistem prompt’u** | Tek | Sadece `prompts/tuba_system.txt`; **kiracıya göre farklı prompt yok** |

Özet: **Üyelik, panel, veri ayrımı hazır.** Eksik olan: tenant’a göre **WhatsApp eşlemesi (DB’den)**, tenant’a göre **gönderim (token/phone)** ve tenant’a göre **sistem prompt’u**.

---

## 3. Zafer (veya Yeni Müşteri) İçin Eksikler

Zafer’in “kendi numarası + kendi prompt’u” ile çalışması için aşağıdakiler gerekli:

### 3.1 Webhook: Hangi numara hangi tenant?

- **Şu an:** `phone_id_to_tenant(phone_id)` sadece env’e bakıyor: `PHONE_ID`→tuba, `ZAFER_PHONE_ID`→zafer.
- **Olması gereken:** `tenants` tablosundan `whatsapp_phone_number_id = phone_id` olan satırın `tenant_id` değeri kullanılsın. Böylece panelden WhatsApp numarasını kaydeden her tenant otomatik eşlenir; env’e yeni tenant eklemek gerekmez.

### 3.2 Mesaj gönderirken tenant’a özel numara ve token

- **Şu an:** `send_whatsapp_message(phone, text)` her zaman global `PHONE_ID` ve `META_TOKEN` kullanıyor.
- **Olması gereken:** Webhook’tan veya panelden cevap gönderirken `tenant_id` verilsin; bu tenant’ın `whatsapp_phone_number_id` ve `whatsapp_access_token` (veya env’deki token) kullanılsın. Böylece Zafer’in numarasına gelen mesaja Zafer’in numarasından cevap gider.

### 3.3 Kiracıya özel sistem prompt’u

- **Şu an:** `TubaAIAssistant` tek instance, tek prompt: `prompts/tuba_system.txt`.
- **Olması gereken:** Her tenant için ayrı prompt:
  - **Seçenek A:** Dosya: `prompts/{tenant_id}_system.txt` (örn. `prompts/zafer_system.txt`). Yoksa `prompts/tuba_system.txt` veya varsayılan.
  - **Seçenek B:** `tenants` tablosuna `system_prompt` (veya `system_prompt_path`) kolonu; panelden veya DB’den metin/path girilir.

Böylece Zafer farklı bir prompt ile (örn. farklı ürünler, farklı dil) çalışabilir.

---

## 4. “Zafer Bu Hizmeti Almak İstiyor” – Aksiyon Akışı

### 4.1 Şu anki akış (eksiklerle)

1. Zafer **kayıt olur** (landing → Kayıt ol: ad, e-posta, şifre, mağaza adı).
2. Otomatik giriş yapar; **panelde sadece kendi tenant’ı** görünür (henüz mesaj yok).
3. **Ayarlar → WhatsApp**’tan kendi Phone Number ID ve token’ını girebilir (DB’e yazılır).
4. **Sorun:**
   - Gelen mesajlar Meta’da **hangi numaraya gelirse** o numara için env’de `ZAFER_PHONE_ID` tanımlı değilse webhook yine “tuba” sayıyor; mesajlar Tuba’ya gider.
   - Cevap her zaman **Tuba numarası ve Tuba token’ı** ile gidiyor.
   - AI cevabı **Tuba’nın prompt’u** ile üretiliyor.

Yani: **Kayıt ve panel hazır; WhatsApp ve prompt tarafı henüz kiracıya özel değil.**

### 4.2 Eksikler tamamlandıktan sonra akış

1. Zafer **kayıt olur** → panele girer.
2. **Ayarlar → WhatsApp**: Kendi WhatsApp Business Phone Number ID ve (gerekirse) Access Token’ı girer → Kaydet.
3. (İsteğe bağlı) **Prompt:**
   - Dosya kullanılıyorsa: sunucuya `prompts/zafer_system.txt` eklenir.
   - Veya ileride panelde “Sistem metni / Bot kişiliği” alanı açılırsa oradan doldurulur.
4. Zafer’in WhatsApp numarasına gelen mesaj → webhook’ta `phone_number_id` DB’den Zafer’e eşlenir → **Zafer’in tenant’ı** kullanılır.
5. AI cevap **Zafer’in prompt’u** ile üretilir; cevap **Zafer’in numarası ve token’ı** ile gönderilir.
6. Zafer panelde sadece kendi sohbetlerini görür; kendi ayarlarını yapar.

**Yani:** Üyelik alıp WhatsApp’ı (ve istenirse prompt’u) ayarlaması yeterli; ekstra “sizin eklemeniz” gerekmez (teknik eksikler kodda tamamlandığında).

---

## 5. Yeni Müşteri Bilgileri – Nasıl Eklenir, Sisteme Nasıl Dahil Olur?

- **Kayıt:** Her müşteri **kendisi** landing sayfasından “Kayıt ol” ile eklenir (Ad, E-posta, Şifre, Mağaza Adı). Yeni bir `tenant_id` (örn. mağaza adından slug) oluşturulur.
- **Bilgi ekleme:** Ekstra “müşteri listesi”ne manuel ekleme şu an yok; tüm müşteriler self-registration ile gelir. İleride admin panelinde “Tenant ekle / davet gönder” eklenebilir.
- **Sisteme dahil olma:**  
  - Giriş yapması  
  - Ayarlar → WhatsApp’tan kendi numarasını (ve gerekirse token’ı) girmesi  
  - (İsteğe bağlı) Kendi prompt’unun olması (dosya veya ileride panel alanı)  

Bu üç adım tamamsa, gelen mesajlar doğru tenant’a, doğru prompt ve doğru numaradan cevaplanır (yukarıdaki kod değişiklikleri yapıldıktan sonra).

---

## 6. Özet: Hazır mı, Ne Yapılmalı?

| Soru | Cevap |
|------|--------|
| Proje çoklu kişiye hizmet edecek mi? | Evet; yapı tenant_id ile çoklu kiracı için. |
| Panelde sadece üyelik (kayıt) yeterli mi? | Evet; kayıt yeterli. Ek olarak **Ayarlar → WhatsApp** doldurulmalı (ve istenirse prompt). |
| Her gelen müşteri nasıl eklenir? | Kendisi “Kayıt ol” ile eklenir; ileride admin ile davet/manuel ekleme eklenebilir. |
| Zafer farklı prompt ile çalışabilir mi? | Şu an hayır (tek Tuba prompt’u). Dosya veya DB ile kiracıya özel prompt eklendikten sonra evet. |
| Zafer hemen aksiyon alabilir mi? | Kayıt olup panele girebilir; WhatsApp’ı ayarlayabilir. **Ancak** gelen/giden mesajların ve AI’nın Zafer’e özel olması için aşağıdaki 3 teknik değişiklik gerekir. |

### Yapılacak 3 teknik değişiklik (özet)

1. **`phone_id_to_tenant(phone_id)`**  
   Önce `tenants` tablosunda `whatsapp_phone_number_id = phone_id` ile ara; bulunursa o tenant’ı döndür. Bulunamazsa mevcut env mantığına (veya varsayılan tuba) düş.

2. **`send_whatsapp_message(phone, text, tenant_id=None)`**  
   `tenant_id` verilmişse bu tenant’ın `whatsapp_phone_number_id` ve `whatsapp_access_token` değerini kullan (webhook ve panel gönderiminde tenant_id ilet).

3. **Kiracıya özel sistem prompt’u**  
   `TubaAIAssistant` içinde prompt yüklerken `tenant_id` kullan: önce `prompts/{tenant_id}_system.txt`, yoksa `prompts/tuba_system.txt` veya DB’deki alan. Webhook’ta `mesaj_olustur(..., tenant_id=tenant_id)` çağrılsın; asistan ya tenant_id ile oluşturulsun ya da çağrıda tenant_id geçilsin ve prompt o anda seçilsin.

Bu üçü yapıldığında “Zafer bu hizmeti almak istiyor” denildiğinde: Zafer kayıt olur → WhatsApp’ı (ve istenirse prompt’u) ayarlar → kendi numarası ve kendi prompt’u ile çalışır; ek aksiyon gerekmez.

---

## 7. E-ticaret Backend: Butik Sistem vs İkas (Zafer Örneği)

Müşteriler farklı e-ticaret / mağaza sistemleri kullanabilir. Ürün, stok, sipariş bilgisi bu sistemlerden alınmalı.

| Tenant örneği | E-ticaret backend | Projede durum |
|---------------|-------------------|----------------|
| **Tuba** | **Butik Sistem** | Var: `ButikSistemClient`, sipariş, ürün/stok; env: BUTIK_API_* |
| **Zafer** | **İkas** | **Yok.** İkas API entegrasyonu ve dokümantasyonu ayrıca yapılmalı. |

- **Şu an:** AI sipariş için `butik_client.check_order_by_phone()`, ürün için `butik_client.get_product_by_model_code()` kullanıyor; client global tek instance, tenant'a göre değişmiyor.
- **Zafer (İkas) için:** ButikSistem benzeri bir İkas client (sipariş + ürün/stok), tenant'a göre backend seçimi (örn. `tenants.ecommerce_backend`: butik | ikas), İkas için ayrı kurulum dokümanı gerekli.

**Özet:** Zafer Butik değil İkas kullanıyor; entegrasyon ve dokümantasyon İkas için ayrıca ayarlanmalı. Projede şu an sadece Butik Sistem var.

---

## 8. Kim Ne Öder? İş Modeli: İki Ayrı Ödeme Noktası

Sisteme dahil olan müşteriler **kendi Meta (WhatsApp Business) hesaplarıyla** bağlanacak. **Müşteri iki ayrı yerden ödeme yapar:**

| Nereye? | Ne için? | Kim faturalandırır? |
|---------|----------|---------------------|
| **Bize (platform)** | 1) Sistemi kullanmaları için **aylık ödeme** (abonelik). 2) **Token bedelleri** (model/Claude kullanımı) – maliyeti müşteriye yansıtıyoruz. | Biz |
| **Meta (WhatsApp)** | WhatsApp Business API kullanımı (mesaj/konuşma). Müşterinin kendi Meta hesabı faturalanır. | Meta |

**Özet:** Evet, doğru. Hem bizden (aylık kullanım bedeli + token maliyeti yansıtması) hem de Meta/WhatsApp tarafından (mesaj kotası) ayrı ayrı ödeme alınacak; müşteri iki ayrı yer için ödeme yapacak.

---

## 9. Meta (WhatsApp) Tarafı Kabaca Ne Kadar Maliyet Çıkar? (Tuba / Zafer)

Meta **mesaj adedi değil, konuşma (conversation)** bazlı faturalandırıyor. Bir **konuşma** = müşteri ile işletme arasında **24 saatlik pencere**; bu pencerede kaç mesaj atılırsa atılsın genelde tek konuşma sayılır.

- **Servis konuşmaları (müşteri yazdı, siz cevapladınız):** Çoğu bölgede **ayda 1.000 konuşmaya kadar ücretsiz**. Sonrası bölgeye göre (ör. Türkiye için) konuşma başı birkaç cent–birkaç on cent USD mertebesinde olabiliyor.
- **Utility / Marketing / Authentication:** Ayrı kategoriler, genelde ücretli; fiyat yine bölgeye göre değişir.

**Sizin senaryo (müşteri soruyor, bot cevaplıyor):** Neredeyse tamamı “servis” kategorisine girer. Aylık **toplam konuşma sayısı** (her benzersiz müşteri numarası için 24 saatte 1 konuşma) önemli.

**Verdiğiniz hacim: günlük ~2.000 farklı müşteri (hem Tuba hem Zafer için)**

| | Günlük (konuşma) | Aylık (konuşma, ~30 gün) | Ücretsiz kotadan sonra (ayda) |
|--|------------------|---------------------------|--------------------------------|
| **Tuba**  | ~2.000 | ~60.000 | ~59.000 ücretli |
| **Zafer** | ~2.000 | ~60.000 | ~59.000 ücretli |

(İlk 1.000 konuşma/ay ücretsiz; geri kalanı Meta’nın fiyat listesine göre.)

**Kabaca Meta maliyeti (her tenant için, aylık):**

- Konuşma başı fiyat bölgeye göre değişir (Türkiye için genelde birkaç cent–on cent USD mertebesi). **Resmi fiyat:** [WhatsApp Business Platform Pricing](https://business.whatsapp.com/products/platform-pricing) (ülke + para birimi seçin).
- **Örnek aralık (59.000 ücretli konuşma için):** Konuşma başı 0,03–0,10 USD varsayılırsa → **ayda ~1.770–5.900 USD / tenant**. Yüksek hacimde Meta’nın volume tier’ları daha uygun olabilir; kesin rakam için fiyat sayfası ve (varsa) anlaşma gerekir.

**Özet:** Günlük 2.000’er farklı müşteri ile Tuba ve Zafer için aylık **~60.000’er konuşma** beklenir; Meta maliyeti tenant başı **birkaç yüz – birkaç bin USD/ay** bandında olabilir. Net rakam için Meta fiyat listesi ve hacim indirimleri mutlaka kontrol edilmeli.

---

## 10. Bu Maliyetler Yüksek – Ne Yapabiliriz?

Meta tarafı maliyet büyük görünüyorsa aşağıdaki yollar işi kolaylaştırır; hepsi birden veya bir kısmı uygulanabilir.

### 10.1 Meta tarafında maliyeti düşürmek

- **BSP (Business Solution Provider) kullanmak:** Meta’ya doğrudan değil, bir WhatsApp BSP üzerinden bağlanmak. BSP’ler toplu hacim nedeniyle daha uygun konuşma fiyatı sunabiliyor; Tuba/Zafer kendi hesaplarını BSP ile açabilir veya siz platform olarak bir BSP ile anlaşıp tenant’ları onun üzerinden bağlayabilirsiniz.
- **Volume / kurumsal anlaşma:** Yüksek hacim (toplam 100k+ konuşma/ay) için Meta veya BSP ile özel fiyat görüşmesi yapmak. Konuşma başı maliyet 0,03–0,10 USD’den daha aşağı çekilebilir.
- **Doğru konuşma kategorisi:** Mesajların tamamı “servis” (müşteri başlattı, siz cevapladınız) kategorisinde kalsın; gereksiz utility/marketing kullanımı fiyatı artırır.

### 10.2 Maliyeti müşteriye doğru yansıtmak

- **Meta faturası zaten müşteride:** Tuba ve Zafer kendi Meta hesaplarına fatura görüyor; bu maliyet sizin değil, onların. Siz sadece **aylık abonelik + token** alıyorsunuz. Müşteri toplam maliyeti (sizin ücret + Meta) bilerek karar verebilir.
- **Abonelikte “WhatsApp kotası” tanımak:** Örn. “Paket: aylık X konuşmaya kadar dahil” değil (Meta’yı siz ödemiyorsunuz), ama **fiyatlandırmayı hacme göre kademelendirmek**: düşük hacimli müşteri daha ucuza, yüksek hacimli (2.000/gün gibi) daha yüksek aylık ücret. Böylece yüksek hacim size değil, müşteriye maliyet olarak kalır; siz sadece platform + AI maliyetini karşılıyorsunuz.

### 10.3 İş modelini netleştirmek

- **Hedef müşteri:** Günlük 2.000 müşteri mesajı olan işletme zaten büyük ölçek; bu segment için toplam maliyet (sizin ücret + Meta) kabul edilebilir olanları hedeflerin. Küçük işletmeler (günde 50–200 konuşma) için Meta maliyeti çok daha düşük (1.000 ücretsiz kotası bile yeterli olabilir).
- **Tek fatura (opsiyonel):** İleride siz Meta/BSP ile toplu anlaşma yapıp tüm konuşmaları kendiniz üstlenirseniz, müşteriye “tek fatura” (sizin faturanız) sunup içinde WhatsApp maliyetini de yansıtabilirsiniz. Bu durumda risk ve ödeme sizde olur; fiyatı buna göre koymanız gerekir.

### 10.4 Kısa özet

| Ne yapılabilir? | Fayda |
|-----------------|--------|
| BSP veya volume anlaşması | Konuşma başı Meta maliyetini düşürür (müşteri ödüyor olsa bile onlar için iyi). |
| Meta faturasının müşteride kalması | Sizin nakit çıkışınız olmaz; maliyet müşteri tarafında. |
| Aboneliği hacme göre kademelendirmek | Düşük hacim ucuza, yüksek hacim daha yüksek aylık – adil ve anlaşılır. |
| Küçük/orta işletmeleri de hedeflemek | Onlarda Meta maliyeti çok daha düşük; işiniz büyür, toplam maliyet dağılır. |

Bu maliyetler tek başına işi zorlaştırmaz; **Meta tarafını müşteride bırakıp**, **kendi tarafınızı (abonelik + token) net tutup**, isteğe göre **BSP/volume** ile konuşma maliyetini aşağı çekmek yeterli bir başlangıç stratejisi olur.

---

*Son güncelleme: 2026-02-08*
