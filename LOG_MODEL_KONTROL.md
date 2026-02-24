# Model (Claude) Neden Devreye Girmiyor? – Log Kontrolü

Railway’de **Deployments → son deploy → View Logs** (veya **Service → Logs**) aç. Test mesajı attıktan sonra şu satırlara bak.

---

## 1. API key yok / test değeri

**Log’da görürsen:**
```text
[AI] ANTHROPIC_API_KEY yok veya 'sk-ant-test' - Claude CAGILMIYOR. Railway -> Project -> Variables -> ANTHROPIC_API_KEY ekle ...
[Webhook] Cevap = yönlendirme (model devreye girmedi: API key eksik/hatalı veya Claude istisnası) ...
```

**Anlamı:** Claude hiç çağrılmıyor; cevap her zaman “yetkilimize yönlendiriyorum” oluyor.

**Yapman gereken:**  
Railway → Proje → **Variables** → `ANTHROPIC_API_KEY` ekle. Değer Anthropic Console’dan aldığın, `sk-ant-api03-...` ile başlayan gerçek key olmalı (placeholder veya `sk-ant-test` olmamalı).

---

## 2. Claude API hatası (istisna)

**Log’da görürsen:**
```text
[AI] Claude API HATASI (model cevap veremedi): AuthenticationError: ...
[AI] Claude API HATASI (model cevap veremedi): RateLimitError: ...
```

**Anlamı:** Key var ama istek başarısız (yetki, kota, ağ vb.).

**Yapman gereken:**  
- `AuthenticationError` → Key’i kontrol et; süresi dolmamış, doğru kopyalanmış olsun.  
- `RateLimitError` → Kullanım limiti; biraz bekleyip tekrar dene.  
- Başka hata → Log’taki tam hata mesajını not alıp kontrol et.

---

## 3. Model gerçekten çalışıyorsa

**Log’da görürsen:**
```text
[Webhook] AI cevap üretiliyor...
[AI] Claude modeli cagriliyor (cevap modelden gelecek)...
[AI] Cevap: Claude'dan geldi (model calisti).
[Webhook] Cevap üretildi (sabit veya Claude).
```

**Anlamı:** Cevap Claude’dan veya sabit kurallardan geliyor; model devrede.

---

## 4. Sabit cevaplar (Claude’a gerek yok)

“Merhaba”, “teşekkür”, “fiyat”, “stok” gibi mesajlarda kod önce sabit cevap dener; Claude sadece karmaşık cevaplarda çağrılır. Bu yüzden bazen log’da “Claude modeli cagriliyor” görünmeyebilir; bu normal.

---

## Özet

| Log satırı | Ne yapmalısın? |
|------------|-----------------|
| `ANTHROPIC_API_KEY yok veya 'sk-ant-test'` | Railway Variables’a gerçek `ANTHROPIC_API_KEY` ekle. |
| `Claude API HATASI ... AuthenticationError` | Key’i kontrol et / yenile. |
| `Claude API HATASI ... RateLimitError` | Limit; bekleyip tekrar dene. |
| `Cevap: Claude'dan geldi (model calisti)` | Model çalışıyor. |

Deploy’u tekrar atıp test mesajı gönder; yukarıdaki satırlardan hangisi çıkıyor bak. En sık sebep: **Railway’de `ANTHROPIC_API_KEY` hiç tanımlı değil veya `sk-ant-test` / yanlış değer.**
