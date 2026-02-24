# Meta (WhatsApp) Test — Model Neden Cevap Vermiyor? Kontrol Listesi

Bu dosya, Meta üzerinden test mesajı atıp Claude modelinin cevap vermemesi sorununu adım adım kontrol etmek için hazırlandı.

---

## MCP bu sorunu çözmez

- **MCP**, Cursor’un (IDE’nin) dış araçlarla konuşması içindir (örn. Supabase, TestSprite).
- WhatsApp akışı: **Meta → senin sunucun (webhook) → Anthropic API → cevap**. Bu akış Cursor’dan bağımsız; MCP burada devreye girmez.
- **Claude/Anthropic için ayrı bir MCP gerekmez.** Model zaten `ai_assistant.py` içinde Anthropic API ile çağrılıyor.

---

## Model ne zaman devreye girer?

Kodda iki tür cevap var:

1. **Sabit cevaplar** (Claude çağrılmaz): Merhaba, teşekkürler, günaydın, “fiyat ne kadar?”, “stok var mı?” gibi kısa mesajlara hazır metin döner.
2. **Claude cevabı**: Daha karmaşık sorular (iade, değişim, siparişim nerede, şikayet vb.) veya basit kategoride eşleşmeyen mesajlarda `claude-3-5-sonnet` çağrılır.

Testte **“Merhaba”** veya **“Teşekkürler”** yazıyorsan zaten sabit cevap gider; model hiç çağrılmaz. Modeli test etmek için örneğin: **“Siparişim nerede?”, “İade yapmak istiyorum”, “Ürün önerir misin?”** gibi mesajlar at.

---

## Kontrol listesi (sırayla)

### 1. ANTHROPIC_API_KEY (Railway / ortam)

- Railway: **Project → Variables** içinde `ANTHROPIC_API_KEY` var mı?
- Değer **gerçek key** olmalı; `sk-ant-api03-...` ile başlar. `sk-ant-test` veya boş ise **Claude hiç çağrılmaz**, her zaman “yetkilimize yönlendiriyorum” gider.
- Key’i [Anthropic Console](https://console.anthropic.com/) → API Keys’ten alabilirsin.

### 2. Meta token ve webhook

- **META_ACCESS_TOKEN** (veya META_TOKEN) Railway’de doğru mu? 60 dakikalık test token’ı süresi dolduysa yenile.
- Webhook URL’in Railway’deki canlı adrese mi gidiyor? (Meta Developer Console’da doğru URL kayıtlı mı?)

### 2b. “Add a recipient phone number” (farklı numaradan mesaj gelmiyor / bot cevap vermiyor)

WhatsApp Business API (Cloud) **geliştirme aşamasındayken**, Meta sadece **eklediğin alıcı numaralarından** gelen mesajları webhook’una iletir. Test için kullandığın numara **“Add a recipient phone number”** listesinde yoksa:

- Meta o numaradan gelen mesajı **bizim sunucuya hiç göndermez** → webhook’ta `📩 Mesaj Geldi` log’u da çıkmaz, bot cevap veremez.
- Bizim kodda numara filtresi **yok**; mesaj bir kez webhook’a düştüyse işlenir. Sorun genelde Meta tarafında: numara ekli değil.

**Yapılacak:** Meta Developer Console → WhatsApp → **Add a recipient phone number** (veya API kurulum sayfasındaki “To” / test numaraları bölümü) → Mesaj atacak test numarasını ekle. O numaradan atılan mesajlar artık webhook’a düşer.

**Kontrol:** Railway Logs’ta test mesajı attığın anda `📩 Mesaj Geldi: <o_numara>` satırı var mı? **Yoksa** mesaj Meta’dan gelmemiştir (recipient ekle). **Varsa** sorun bizim tarafta (bot modu, AI key, vb.).

### 3. Loglar (model çağrılıyor mu?)

Railway’de **Deploy → Logs** aç. Test mesajı attığında şunlara bak:

- `[Webhook] AI cevap üretiliyor...` → Mesaj AI’a gidiyor.
- `[AI] Claude modeli cagriliyor...` → Claude gerçekten çağrılıyor.
- `[AI] Cevap: Claude'dan geldi` → Model cevap üretti.
- `ANTHROPIC_API_KEY yok` veya `Claude API HATASI` → Key eksik/hatalı veya API hata veriyor.

Bu satırlar hangi adımda kesiliyorsa sorun orada.

### 4. Mesaj türü

- Sadece “merhaba” / “selam” atıyorsan → Sabit cevap; model çağrılmaz (bu normal).
- “İade yapmak istiyorum”, “Siparişim nerede?” gibi bir mesaj at → Claude’un cevap vermesi gerekir.

---

## Özet

| Soru | Cevap |
|------|--------|
| MCP model sorununu çözer mi? | Hayır. |
| Claude/Anthropic için MCP gerekir mi? | Hayır. |
| Model neden cevap vermiyor olabilir? | 1) ANTHROPIC_API_KEY yok/yanlış. 2) Testte hep “merhaba” gibi sabit cevap tetikleyen mesaj atıyorsun. 3) API hata veriyor (loglara bak). |
| İlk bakılacak yer | Railway Variables’da ANTHROPIC_API_KEY + Railway Logs. |

Son güncelleme: Şubat 2026
