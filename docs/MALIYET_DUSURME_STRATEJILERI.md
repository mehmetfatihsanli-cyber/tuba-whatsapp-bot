# Maliyet Düşürme Stratejileri (Aynı Performans)

**Hedef:** Günlük 225–360 TL bandını düşürmek; performansı müşteri deneyimi açısından aynı tutmak.

---

## 1. Token Tasarrufu (Hemen Uygulanabilir)

| Önlem | Ne yapılıyor? | Tahmini tasarruf |
|-------|----------------|-------------------|
| **Geçmiş konuşma kısaltma** | Son 20 mesaj yerine 12 mesaj gönder. Değişim sohbetinde son birkaç exchange yeterli. | Input ~%25–40 azalır. |
| **max_tokens düşürme** | 1024 → 512. Müşteri cevapları genelde kısa; uzun açıklama nadiren gerekir. | Output maliyeti ~%30–50 azalır (cevaplar çoğunlukla 300–500 token). |
| **Sipariş listesi sınırı** | CONTEXT’e tüm siparişler değil, son 5 sipariş ver. Zaten iade/değişim listesinde 5 gösteriyoruz. | Input azalır (özellikle çok siparişli müşterilerde). |

**Toplam etki:** Çağrı başı ~%25–35 daha az token → **günlük maliyet kabaca %25–35 düşer** (örn. 270 TL → 175–200 TL).

---

## 2. Daha Ucuz Model (Haiku) – Kademeli Kullanım

- **Claude Haiku 4.5:** Input ~\$1/M, output ~\$5/M (Sonnet’e göre ~1/3 fiyat).
- **Fikir:** Basit / kısa takip mesajlarında Haiku, şikayet / karmaşık taleplerde Sonnet kullan.
- **Basit sayılacak örnekler:** "Bilgiler yok", "Teşekkürler", "Tamam", "Hangi beden var?", "Sipariş kodum X" (kısa, net).
- **Sonnet kalsın:** "Çok kızdım", "İade etmek istemiyorum para istiyorum", uzun şikayet, belirsiz karmaşık soru.

**Uygulama:** Mesaj uzunluğu < 100 karakter ve şikayet/yönlendirme kelimesi yok → Haiku; diğer tüm karmaşık → Sonnet.  
**Kod:** `AI_USE_HAIKU_FOR_SIMPLE=1` (Railway Variables) açınca devreye girer. İsteğe bağlı `AI_HAIKU_MODEL=claude-haiku-4-5`.  
**Tasarruf:** Claude çağrılarının ~%40–50’si Haiku’ya kayarsa, **toplam günlük maliyet ~%30–40 daha düşer** (Haiku ~1/3 fiyat).

---

## 3. Sabit Cevap Genişletme (Claude Çağrısı Azaltma)

- Şu an: Merhaba, teşekkür, iade/değişim ilk cevap (sipariş listesi) sabit.
- **Eklenebilir:**  
  - "İade süresi kaç gün?" → Sabit: "14 gün."  
  - "Değişim hakkı kaç?" → Sabit: "En fazla 2 değişim hakkı."  
  - "Sipariş kodum yok" (ve sipariş varsa) → Zaten sipariş listesi; tekrar "Numaranızdan baktım…" sabit.  
- Bu tür kalıplar Claude’a hiç gitmez → **çağrı sayısı %5–15 azalır**, maliyet doğrudan düşer.

---

## 4. Prompt Caching (Orta Vadeli)

- Sistem promptu + kurallar her istekte tekrar gidiyor. Anthropic **prompt caching** ile bu blok cache’lenir; sonraki isteklerde cache’den okunur (~%90 daha ucuz input).
- **Koşul:** Cache’lenecek blok en az 1024 token (Sonnet). Sistem promptu tek başına ~500–700 token; “sabit kurallar” metni eklenerek 1024’e çıkarılabilir.
- **Sonuç:** Özellikle yüksek trafikte input maliyeti belirgin azalır; implementasyon için API’de `cache_control` ile system/content yapısı güncellenmeli.

---

## 5. Özet: Tahmini Günlük Maliyet (100 müşteri × 20 mesaj, değişim)

| Senaryo | Günlük (TL) | Açıklama |
|--------|-------------|----------|
| **Şu an** | 270–360 | Sonnet, 20 mesaj geçmiş, max 1024, tüm siparişler |
| **Token tasarrufu (1)** | 175–235 | Geçmiş 12, max_tokens 512, sipariş 5 ile sınır |
| **+ Haiku kademeli (2)** | 120–170 | Basit karmaşık → Haiku |
| **+ Sabit cevap (3)** | 110–155 | Sık sorular sabit |
| **+ Prompt cache (4)** | 90–130 | Cache ile input maliyeti düşük |

**Hedef:** Aynı performansla **günlük ~100–170 TL** bandına inmek; ileride cache ile **~90–130 TL/gün** mümkün.

---

## Uygulanan Değişiklikler (Kod)

- **Geçmiş:** `get_gecmis_konusma` limit 20 → 12.
- **max_tokens:** 1024 → 512.
- **Sipariş:** CONTEXT’e en fazla 5 sipariş (`_format_orders`).
- **Haiku (opsiyonel):** Railway’de `AI_USE_HAIKU_FOR_SIMPLE=1` verirsen, kısa ve sakin mesajlarda Haiku, diğerlerinde Sonnet kullanılır.

---

## Tuba Özel Durum: Meta Geçişi vs Eleman Maliyeti

**Durum:** Tuba bu sistemi kullanabilmek için Meta (WhatsApp Business API) geçişi yapacak. Plan, eleman maliyetlerini bot ile kaldırmaktı; ama Meta tarafı maliyeti (günlük ~2.000 müşteri ile) neredeyse **en az bir eleman maliyeti** seviyesinde çıkıyor. Bu, "elemanı kaldırıyoruz" vaadini zayıflatıyor mu?

**Değerlendirme:**

- **Tek başına sorun sayılmaz**, ama **anlatımı ve beklentiyi netleştirmek** iyi olur:
  1. **Eleman sayısı hâlâ azalabilir.** Örn. 2–3 kişi müşteri hizmeti yapıyorsa → bot + 1 kişi (sadece yönlendirmeler / istisnalar) ile 1–2 kişi maliyeti düşer. Meta maliyeti "1 eleman" civarındaysa bile, toplamda hâlâ tasarruf olur (2 eleman → 1 eleman + Meta).
  2. **Değer sadece maliyet değil.** 7/24 cevap, tutarlı ton, ölçek (2.000/gün insanla zor). Tuba için "maliyet aynı kalsa bile 1 kişi + bot" = daha az yük, daha iyi kapasite.
  3. **Meta maliyetini aşağı çekmek mümkün.** BSP veya volume anlaşması ile konuşma başı ücret düşerse, "neredeyse 1 eleman" → "1 elemanın yarısı" bandına inebilir; o zaman hem eleman azalır hem Meta makul kalır.

**Önerilen çerçeve (Tuba'ya anlatırken):**

- "Elemanı sıfırlamıyoruz; **yükü ve eleman sayısını azaltıyoruz**. Bot günlük akışın büyük kısmını alır; siz 1 kişi ile sadece karmaşık / yönlendirilen konulara bakarsınız. WhatsApp tarafı maliyeti (Meta) var; BSP/volume ile bunu makul seviyede tutmayı hedefliyoruz. Net sonuç: daha az eleman maliyeti + daha iyi kapasite."

**Kısa cevap:** En az bir eleman maliyeti kadar Meta çıkması tek başına işi bozmaz; **eleman sayısını 2–3'ten 1'e indirip + Meta** ile toplam maliyet ve iş yükü hâlâ düşer. Değeri "elemanı sıfırla" değil "elemanı azalt + 7/24 kapasite" diye konumlarsanız ve Meta tarafını BSP/volume ile mümkün olduğunca aşağı çekerseniz Tuba için sorun olmaz.
