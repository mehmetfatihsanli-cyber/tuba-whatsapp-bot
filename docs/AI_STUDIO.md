# AI Stüdyo – Virtual Try-On (Replicate)

## Ne yapar?

Panelde **AI Stüdyo** sayfası (`/dashboard/ai-studio`) ile kullanıcılar:

1. Kıyafet görseli yükler (askıda, düz çekim vb.)
2. Kategori seçer: **Üst**, **Alt** veya **Elbise**
3. **Mankene Giydir** ile Replicate **IDM-VTON** modeli kıyafeti varsayılan manken üzerinde gösterir (yaklaşık 30–40 sn)
4. **İndir** ile sonucu bilgisayara alıp web sitesine ekler

Böylece ajansa iş yaptırmadan sanal manken görseli üretilir.

## Kurulum

### 1. Replicate paketi

```bash
pip install replicate
```

`requirements.txt` içinde `replicate` zaten yer alıyor.

### 2. API anahtarı

`.env` dosyasına (ve Railway / production ortamına):

```bash
REPLICATE_API_TOKEN=r8_xxxxxxxxxxxx
```

Replicate hesabından API token: https://replicate.com/account/api-tokens

### 3. BASE_URL (önemli)

Replicate, yüklenen kıyafet görselini **public URL** üzerinden indirir. Bu yüzden:

- **Production (Railway):** `BASE_URL` zaten tanımlı olmalı (örn. `https://tuba-whatsapp-bot-production.up.railway.app`).
- **Lokal test:** Replicate sunucuları `localhost`'a erişemez. Public URL için ngrok kullanın ve `.env`'e `BASE_URL=https://xxx.ngrok.io` ekleyin.

### 4. Varsayılan manken görseli (isteğe bağlı)

Model, kıyafeti giydirmek için bir "human" (manken/model) görseli kullanır. Varsayılan bir URL kodda tanımlı; kendi görselinizi kullanmak istersen:

```bash
VIRTUAL_STUDIO_DEFAULT_MODEL_IMAGE=https://example.com/3-4-oraninda-manken.jpg
```

Görsel **3:4 en-boy oranında** olursa daha iyi sonuç alınır.

## API özeti

| Endpoint | Açıklama |
|----------|----------|
| `GET /api/tryon-status` | Replicate token tanımlı mı? |
| `POST /api/generate-tryon` | Form: `garment` (file), `category` (ust \| alt \| elbise). Cevap: `{ success, output_url }` |

Yüklenen dosyalar `static/uploads/` altında UUID ile saklanır; Replicate'e `BASE_URL/static/uploads/<uuid>.jpg` olarak verilir.
