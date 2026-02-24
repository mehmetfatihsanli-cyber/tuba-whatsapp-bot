# Model (Claude) Devreye Girme – Tam Çözüm Yol Haritası

Bu dosya: **Claude modelinin WhatsApp cevaplarında devreye girmemesi** sorununu adım adım bitirmek için yol haritası.  
Bağlam: BAGLAM_OZETI.md, TODO.md. Supabase MCP bağlantısı mevcut.

---

## Sorun Özeti

- WhatsApp’tan mesaj geliyor, bazen **sabit cevap** veya **“Yetkilimize yönlendiriyorum”** gidiyor; **Claude’dan gerçek cevap** gelmiyor.
- Olası nedenler: **ANTHROPIC_API_KEY** yok/yanlış, test mesajı Claude’u tetiklemiyor (sabit cevap), veya API hata veriyor.

---

## Ne Zaman Claude Çağrılır, Ne Zaman Çağrılmaz?

| Durum | Claude çağrılır mı? | Örnek mesaj |
|--------|----------------------|--------------|
| Basit karşılama | Hayır (sabit cevap) | "Merhaba", "Selam", "Teşekkürler" |
| Basit: fiyat/stok | Hayır (sabit) | "Fiyatı ne?", "Stokta var mı?" |
| İade/değişim (ilk mesaj) | Hayır (sabit: sipariş kodu sor) | "İade yapmak istiyorum" → "Sipariş kodunuzu biliyor musunuz?" |
| Karmaşık / genel soru | **Evet** | "Ürün önerir misin?", "Hangi renklerde var?", "Siparişim nerede?" (sipariş yoksa) |
| Kızgın müşteri | Hayır (yönlendirme) | "Yetkilinizi istiyorum", küfür |
| **API key yok/yanlış** | **Hayır** (yönlendirme) | Her karmaşık mesajda "Yetkilimize yönlendiriyorum" |

Yani modeli **kesin test etmek** için: **"Ürün önerir misin?"** veya **"Hangi ürünleriniz var?"** gibi bir mesaj at (iade/merhaba değil).

---

## Yol Haritası – Sırayla Yapılacaklar

### Adım 1: Railway’de ANTHROPIC_API_KEY Kontrolü (Zorunlu)

1. **Railway** → Proje → **Variables**.
2. `ANTHROPIC_API_KEY` var mı bak.
3. **Yoksa:** Anthropic Console’dan gerçek key al (`sk-ant-api03-...` ile başlar). Variables’a ekle, **Add** / **Save**.
4. **Varsa:** Değerin `sk-ant-test` veya placeholder olmadığından emin ol; gerçek key olmalı.
5. Key ekledikten/değiştirdikten sonra Railway genelde **redeploy** yapar; yoksa **Redeploy** tetikle.

**Hızlı doğrulama (canlı siteden):** Tarayıcıda şu adresi aç:  
`https://tuba-whatsapp-bot-production.up.railway.app/api/check-model`  
- `claude_configured: true` → Key tanımlı (model kullanılabilir).  
- `claude_configured: false` → Key eksik/yanlış; Railway Variables’a tekrar bak.

---

### Adım 2: Uygulama Başlangıç Logunu Kontrol Et

- Railway **Deployments** → son deploy → **View Logs** (veya **Logs** sekmesi).
- Uygulama açılırken şunlardan biri çıkar:
  - `✅ ANTHROPIC_API_KEY ayarli - Claude modeli kullanilacak.` → Key okunuyor.
  - `⚠️ ANTHROPIC_API_KEY yok veya test - Claude cevap veremez...` → Key yok veya test; Adım 1’i tekrarla.

---

### Adım 3: WhatsApp’tan Modeli Tetikleyen Mesajla Test

1. WhatsApp’tan **test numarasıyla** panele bağlı numaraya mesaj at.
2. **Şu mesajlardan birini** yaz (Claude’un kesin çağrıldığı senaryo):
   - **"Ürün önerir misin?"**
   - **"Hangi renklerde var?"**
   - **"Bana uygun bir kombin önerir misin?"**
3. Beklenen: Cevap **Claude’dan** gelmeli (ürün/kombin tarzı, kişiselleştirilmiş).
4. Eğer yine **"Yetkilimize yönlendiriyorum"** gelirse → Key hâlâ eksik/yanlış veya API hata veriyor (Adım 4).

**Dikkat:** Sadece **"Merhaba"** veya **"İade yapmak istiyorum"** yazarsan sabit cevap gider; bu normal, model atlanır.

---

### Adım 4: Webhook / AI Loglarını İncele

Railway **Logs**’ta (mesaj attıktan sonra) şunlara bak:

| Log satırı | Anlamı |
|------------|--------|
| `[Webhook] AI cevap üretiliyor...` | AI katmanına girildi. |
| `[AI] mesaj türü=karmaşık` | Claude’a gidebilecek tür. |
| `[AI] Claude modeli cagriliyor (cevap modelden gelecek)...` | Claude API çağrıldı. |
| `[AI] Cevap: Claude'dan geldi (model calisti).` | Model cevap üretti. |
| `[AI] ANTHROPIC_API_KEY yok veya 'sk-ant-test'` | Key eksik/yanlış → Adım 1. |
| `[AI] Claude API HATASI ...` | Key var ama API hata (rate limit, auth, ağ). |
| `[Webhook] Cevap = yönlendirme (model devreye girmedi...)` | Sonuç yönlendirme; key veya istisna. |

Hata varsa mesajı kopyalayıp (key’i paylaşmadan) inceleyebilir veya Cursor’da paylaşabilirsin.

---

### Adım 5: Supabase MCP ile Proje Kontrolü (İsteğe Bağlı)

Cursor’da Supabase MCP bağlıysa:

- “Supabase’deki tabloları listele” gibi komutlarla veritabanı tarafını kontrol edebilirsin.
- **API key Railway’de tutulur;** Supabase’te key saklanmıyor. Yani “model devreye girsin” için asıl yapılacak: **Railway Variables’da ANTHROPIC_API_KEY**.

---

## Özet Kontrol Listesi

- [ ] Railway **Variables**’da `ANTHROPIC_API_KEY` var ve gerçek key (sk-ant-api03-...).
- [ ] Canlıda `/api/check-model` → `claude_configured: true`.
- [ ] Railway log’ta başlangıçta: `ANTHROPIC_API_KEY ayarli - Claude modeli kullanilacak`.
- [ ] WhatsApp’tan **"Ürün önerir misin?"** (veya benzeri) ile test; cevap Claude’dan geliyor.
- [ ] Log’ta mesaj sonrası: `Claude modeli cagriliyor` ve `Cevap: Claude'dan geldi`.

Hepsi tamamsa **model sorunu bitti** kabul edilir.

---

## İlgili Dosyalar

- **Kod:** `modules/ai_assistant.py` (Claude çağrısı), `app.py` (webhook, başlangıç logu).
- **Config:** `config.py` (AI_MODEL, ANTHROPIC_API_KEY fallback), `.env` / Railway Variables.
- **Rehberler:** `META_MODEL_TEST_KONTROL.md`, `LOG_MODEL_KONTROL.md`, `TODO.md`.

**Son güncelleme:** Şubat 2026
