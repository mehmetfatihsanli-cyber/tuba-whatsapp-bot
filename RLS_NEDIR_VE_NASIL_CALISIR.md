# RLS (Row Level Security) — Nedir, Nasıl Çalışıyor?

Bu projede Supabase tablolarında **RLS açıldı**. Kısa özet aşağıda.

---

## RLS ne demek?

- **Row Level Security** = Satır bazlı güvenlik. Tabloya kim, hangi satırlara erişebilir, veritabanı seviyesinde kısıtlanır.
- **Kapalıyken (kırmızı):** Tabloya bağlanan herkes (anon key dahil) tüm satırları okuyup yazabilir; doğrudan API ile erişim riski vardır.
- **Açıkken (yeşil):** Varsayılan olarak kimse satır göremez/yazamaz; sadece **politika (policy)** tanımladığın roller/koşullar erişebilir. Supabase’te **service_role** anahtarı RLS’i bypass eder (backend bu yüzden etkilenmez).

---

## Bu projede ne yapıldı?

- **tenants**, **messages**, **customers**, **conversation_state**, **media_files** tablolarında RLS **açıldı**.
- **Ek politika yazılmadı** → Anon/authenticated ile doğrudan tabloya erişim yok; sadece **service_role** (backend’de kullandığın `SUPABASE_KEY`) erişebilir.
- Backend (Flask) zaten **service_role** ile çalıştığı için **test mesajları ve tüm mevcut akış aynen çalışır**; ek bir kod değişikliği gerekmez.

---

## Özet

| Soru | Cevap |
|------|--------|
| RLS açmak test mesajlarını bozar mı? | Hayır. Backend service_role kullandığı için RLS’ten muaf. |
| Ek maliyet / performans? | Hayır. Sadece güvenlik kuralı. |
| İleride panelden anon key ile okuma istersem? | O zaman ilgili tabloya **policy** eklenir (örn. tenant_id = auth.uid() veya JWT’deki tenant). |
| RLS’i kapatmak ister sem? | `ALTER TABLE ... DISABLE ROW LEVEL SECURITY;` (önerilmez). |

Migration zaten uygulandı; Supabase Dashboard’da tabloların RLS’i **yeşil** görünecek.

Son güncelleme: Şubat 2026
