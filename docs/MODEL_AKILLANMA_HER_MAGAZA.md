# Model Akıllanması: Her Mağaza İçin Ayrı Ayrı

**Sistemin asıl amacı ve temel taşı:** Modelin **her gelen mağazaya adapte olması** – o mağazanın ürününü, müşteri kitlesini ve konuşma tarzını anlaması, gelen müşteriyi analiz etmesi ve **o mağazanın kafasıyla** (Tuba kafasında, Zafer kafasında) potansiyel satış mantığı ile yaklaşması. Rakiplerden fark: “AI asistan” değil; **mağazayı büyütecek ve benimseyecek** bir beyin.

---

## 1. Adaptör ≠ Model Akıllanması

| Katman | Ne? | Her mağaza için? |
|--------|-----|-------------------|
| **E-ticaret adaptörü** (Butik, İkas, Tiximax) | Sipariş/ürün **verisi** nereden gelecek? REST API, credential. | Aynı platformu kullanan mağazalar **aynı adaptör**, sadece **farklı API bilgisi**. Veri katmanı. |
| **Model akıllanması** | Bot **kim**? Hangi ürünler, hangi kitle, hangi ton, hangi kurallar? | **Her mağaza ayrı.** Tuba = tesettür, ferace, abiye, etek, Tuba tonu. Başka mağaza = erkek eşortman/tişört, o mağazanın tonu. **Temel taş bu.** |

Adaptör, “hangi sistemden sipariş/ürün çekeceğiz” sorusuna cevap. **Mağazanın tanınması, konuşmanın analizi, müşteriye o mağaza gibi davranması** model tarafında; her mağaza için **ayrı ayrı akıllanma** gerekir. Bunu tek bir “örnek prompt” ile tüm mağazalara vermek amacımızdan sapmak olur.

---

## 2. Ne Yapılmalı? Her Mağaza İçin Akıllanma

Her yeni müşteri (mağaza) için:

1. **Mağaza kimliği:** Ne satıyor? (Tesettür / erkek eşortman–tişört / vb.) Hangi kitle? (Kadın tesettür / erkek spor / vb.)
2. **Ton ve kurallar:** Samimi mi, resmi mi? İade/değişim kuralları, link kullanımı, yönlendirme ne zaman?
3. **Sistem prompt’u:** Bu bilgilerle **o mağazaya özel** sistem prompt yazılır. Tuba için “Sen Tuba Butik’sin, tesettür, ferace, abiye, etek…” ; Zafer için “Sen [Zafer mağazasısın], erkek eşortman, tişört…” – ürün seti ve ton ona göre.
4. **Konuşma bağlamı:** Zaten tenant_id ile mesajlar ayrı; her konuşmada **o tenant’ın prompt’u** kullanılır. Böylece model her sohbetten sonra da **o mağazayı tanıyor** çünkü prompt hep o mağazanın tanımı.

Yani: **Sadece e-ticaret entegrasyonu yetmez.** Her mağaza için **model tarafında akıllanma** (mağazaya özel prompt, isteğe bağlı ürün kategorisi/ton bilgisi) şart.

---

## 3. Nasıl Uygulanır?

### 3.1 Teknik

- **Kiracıya özel sistem prompt:** Zaten planda: `prompts/{tenant_id}_system.txt` veya `tenants.system_prompt`. İçeriği **mağaza bazlı** olmalı: ürün türü, kitle, ton, kurallar (Tuba örneği referans).
- **Webhook’ta:** Gelen mesajın `tenant_id`’si ile **o tenant’ın prompt’u** yüklenir; asistan **o prompt** ile cevap üretir. Böylece Tuba sohbetinde “Tuba’nın kafası”, Zafer sohbetinde “Zafer’in kafası” kullanılır.

### 3.2 Operasyonel (onboarding / kalibrasyon)

Yeni mağaza geldiğinde sadece API/Meta bilgisi almak yetmez; **model kalibrasyonu** da yapılmalı:

- **Kısa anket / şablon:** Mağaza adı, ne sattığı (kategori: tesettür / erkek giyim / vb.), hedef kitle, konuşma tonu (sıcak / resmi), temel iade/değişim kuralları.
- Bu bilgilerle **o mağazaya özel** sistem prompt metni üretilir (Tuba prompt’u şablon alınabilir; ürün/kitle/ton mağazaya göre değiştirilir).
- Prompt dosyaya veya DB’ye **tenant’a bağlı** yazılır; bir daha o mağazanın tüm sohbetlerinde bu prompt kullanılır.

Böylece “gelen her yeni müşteriye aynı hizmeti veriyoruz” = **aynı ürün kalitesi** (mağazayı tanıyan, ona göre konuşan model), **içerik olarak her mağaza kendi kimliğiyle** (Tuba tesettür, Zafer erkek eşortman/tişört vb.).

---

## 4. Özet: Amaçtan Sapmamak İçin

- **E-ticaret adaptörü:** Veri için. Aynı platform = aynı adaptör, farklı credential. Bu kısım “her mağaza ayrı akıllanacak” değil.
- **Model akıllanması:** Her mağaza için **ayrı** – mağaza kimliği, ürün türü, kitle, ton, kurallar. Sistem prompt (ve ileride gerekirse ek sinyaller) **tenant bazlı**.
- **Hedef:** Gelen müşteri Tuba’ya yazdığında “Tuba kafasında”, Zafer’e yazdığında “Zafer kafasında” potansiyel satış mantığı ile cevap; her sohbette mağaza tanınmış ve konuşma analiz edilmiş olsun. Bunu sağlamak için **her gelen mağazada model tarafında akıllanma (kalibrasyon)** zorunlu; sadece adaptör örneğiyle yetinmek amacımızdan sapmak olur.

Bu doküman, “her mağaza için akıllanma”nın neden gerekli olduğunu ve teknik + operasyonel olarak ne yapılacağını tek yerde toplar.

---

*Son güncelleme: 2026-02-08*
