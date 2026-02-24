# Supabase MCP'yi Cursor'a Bağlama Rehberi

Bu rehber, Supabase MCP'yi Cursor'da nasıl kuracağını ve **ek maliyet** olup olmadığını anlatır.

---

## Ek maliyet var mı?

**Hayır. Supabase MCP kullanımı ek ücret getirmez.**

- **MCP bağlantısı** = Ücretsiz (Supabase’in sunduğu bir özellik).
- **Cursor** = Zaten kullandığın aboneliğin; MCP için ayrı bir ücret yok.
- **Supabase** = Şu an kullandığın plan (Free / Pro / vb.) aynen devam eder. MCP, o planın üzerine ekstra fiyat eklemez.

Özet: Sadece mevcut Supabase ve Cursor hesaplarını kullanıyorsun; MCP için ekstra ödeme yok.

---

## Cursor'a Supabase MCP nasıl bağlanır?

İki yol var: **tek tıkla kurulum** veya **manuel ayar**.

### Yol 1: Tek tıkla kurulum (en kolay)

1. Tarayıcıda aç: [Supabase MCP – Cursor kurulum sayfası](https://supabase.com/docs/guides/getting-started/mcp)
2. Sayfada **"Add to Cursor"** veya **"Cursor’a Ekle"** benzeri butona tıkla.
3. Cursor açılır ve MCP eklenir. İlk bağlantıda tarayıcıda **Supabase’e giriş yapman** ve MCP’ye izin vermen istenebilir.
4. Cursor’da **Settings → Cursor Settings → Tools & MCP** bölümüne gir; Supabase’in “connected” / aktif göründüğünü kontrol et.

Bu adımlardan sonra Cursor, Supabase’e bağlı MCP ile çalışır.

### Yol 2: Manuel ayar (projede `.cursor/mcp.json`)

1. Proje klasöründe **`.cursor`** klasörü var mı kontrol et. Yoksa oluştur.
2. **`.cursor/mcp.json`** dosyası oluştur (veya varsa aç) ve içine şunu yaz:

```json
{
  "mcpServers": {
    "supabase": {
      "url": "https://mcp.supabase.com/mcp"
    }
  }
}
```

3. Sadece **belirli bir projeyi** kullanmak istiyorsan (daha güvenli), `url` satırını şöyle yap (proje referansını Supabase dashboard’dan alırsın):

```json
"url": "https://mcp.supabase.com/mcp?project_ref=PROJE_REF_BURAYA"
```

4. Dosyayı kaydet. Cursor’u **yeniden başlat** (veya MCP ayarlarını yenile).
5. Cursor ilk kez Supabase MCP’yi kullanırken **tarayıcıda Supabase’e giriş** ve izin verme isteyebilir; onayla.
6. **Settings → Cursor Settings → Tools & MCP** kısmında Supabase’in listelendiğini ve bağlı olduğunu kontrol et.

---

## Bağlantıyı test etme

Cursor sohbetinde örneğin şunu yaz:

- “Supabase’deki tabloları listele, MCP kullan.”
- “messages tablosunun yapısını göster.”

Cursor, MCP üzerinden Supabase’e bağlanıp cevap verebiliyorsa kurulum tamamdır.

---

## Güvenlik notu

- MCP’yi **müşterilere veya son kullanıcıya verme**; sadece sen (geliştirici) kullan. Supabase’e senin yetkinle bağlanır.
- Mümkünse **sadece geliştirme/test projesi** ile kullan; canlı (production) veritabanına bağlarken dikkatli ol. İstersen `?read_only=true` ile sadece okuma modunda bağlanabilirsin.

---

## Kısa özet

| Soru | Cevap |
|------|--------|
| Supabase MCP ek maliyet çıkarır mı? | Hayır. |
| Nasıl bağlanır? | “Add to Cursor” ile veya `.cursor/mcp.json` içine `supabase` url’i ekleyerek. |
| Token gerekir mi? | Yeni yöntemde ilk seferde tarayıcıdan Supabase’e giriş yeterli; ayrıca PAT zorunlu değil. |
| Cursor’da nerede görünür? | Settings → Cursor Settings → Tools & MCP. |

Son güncelleme: Şubat 2026
