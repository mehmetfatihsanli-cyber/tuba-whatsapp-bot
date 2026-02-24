# Railway MCP'yi Cursor'a Bağlama Rehberi

Supabase MCP gibi, **Railway MCP** ile Cursor'dan proje, deploy, değişkenler ve loglar üzerinde işlem yapılabilir.

---

## Ön koşul: Railway CLI + Giriş

Railway MCP, arka planda **Railway CLI** kullanır. Bu yüzden:

1. **Railway CLI kurulu olmalı.**  
   - Kurulu değilse: [Railway CLI](https://docs.railway.com/develop/cli) sayfasına göre kur (örn. `npm i -g @railway/cli` veya Mac’te `brew install railway`).
2. **Giriş yapılmış olmalı.**  
   - Terminalde: `railway login`  
   - Tarayıcı açılır, Railway hesabınla giriş yaparsın.

Bunlar tamamsa MCP, Cursor üzerinden Railway işlemlerini yapabilir.

---

## Projede ne yaptık?

**`.cursor/mcp.json`** dosyasına Railway MCP eklendi. İçerik örneği:

```json
{
  "mcpServers": {
    "supabase": { "url": "https://mcp.supabase.com/mcp" },
    "railway": {
      "command": "npx",
      "args": ["-y", "@railway/mcp-server"]
    }
  }
}
```

Supabase MCP aynen duruyor; Railway ikinci sunucu olarak eklendi.

---

## Cursor’da ne yapmalısın?

1. **Cursor’u yeniden başlat** (veya Cursor Settings → Tools & MCP bölümünde MCP’lerin yeniden yüklenmesini bekle).
2. **Settings → Cursor Settings → Tools & MCP** kısmında **Railway** listelenmiş ve bağlı mı kontrol et.
3. İlk kullanımda **Railway CLI girişi** istenebilir; daha önce `railway login` yaptıysan genelde sorun çıkmaz.

---

## Railway MCP ile neler yapılabilir?

Railway dokümantasyonuna göre örnekler:

- **Proje / servis:** Projeleri listeleme, servis bilgisi.
- **Deploy:** Servis deploy etme, template’den deploy.
- **Değişkenler:** Environment variable listeleme, `.env`’e çekme (MCP aracılığıyla).
- **Loglar:** Servis loglarını çekme.
- **Domain:** Domain oluşturma / listeleme.

Yıkıcı işlemler (örn. proje silme) MCP’de kısıtlı; yine de canlı ortamda dikkatli kullanmak iyi olur.

---

## Özet

| Adım | Yapılacak |
|------|-----------|
| 1 | Railway CLI kur (`railway` komutu çalışsın). |
| 2 | Terminalde `railway login` ile giriş yap. |
| 3 | Cursor’da MCP’lerin yüklü olduğunu kontrol et (Railway görünsün). |
| 4 | Artık sohbette “Railway’deki değişkenleri listele” / “Son deploy loglarını getir” gibi isteklerde bulunabilirsin. |

**Kaynak:** [Railway MCP Server – Railway Docs](https://docs.railway.com/reference/mcp-server)
