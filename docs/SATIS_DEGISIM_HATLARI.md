# Satış ve Değişim Hatları (Tek / Çift Numara)

## Veritabanı nerede?

- **Veritabanı = Supabase** (zaten kullandığınız proje). Railway'de **yeni bir veritabanı eklenmez**.
- **Railway** sadece uygulama (Flask) sunucusudur; Supabase bağlantı bilgileri env (SUPABASE_URL, SUPABASE_KEY) ile verilir.

## Canlıya alma sırası

1. **Supabase:** Mevcut Supabase projenizde **SQL Editor**'da `supabase_line_sales_exchange.sql` dosyasındaki SQL'i çalıştırın. Bu, mevcut tablolara `line` ve (tenants'ta) değişim numarası alanlarını ekler.
2. **Railway:** Kodu deploy edin (git push veya manuel deploy). Yeni env eklemenize gerek yok; değişim numarasını canlıda panelden tanımlayacaksınız.

## Canlıda (Tuba / Zafer / Ali)

- **İki numara** olacak: biri **satış**, biri **değişim/iade**.
- Satış numarasına gelen mesajlar → satış hattı (model satış odaklı, satış kargo akışı).
- Değişim numarasına gelen mesajlar → değişim hattı (model iade/değişim odaklı, değişim kargo akışı).
- Panelde **Satış Hattı** ve **Değişim/İade Hattı** sekmeleriyle ayrı listeler; mesajlar karışmaz.
- Değişim numarası: **Ayarlar > WhatsApp** sayfasında "Değişim/İade hattı (opsiyonel)" alanlarına girilir.

## Şu an tek numara ile test

- Siz şu an **tek numara** kullanıyorsunuz; Tuba/Zafer/Ali’de ileride iki numara olacak.
- **Tek numara** kullanırken:
  - Değişim hattı numarası **tanımlı değilse** (panelde boş, env’de PHONE_ID_EXCHANGE yok),
  - Mesajda **iade / değişim** geçiyorsa (örn. "iade istiyorum", "değişim", "değişim istiyorum"),
  - O mesaj **otomatik olarak değişim hattı** gibi işlenir: model "Değişim hattındasın" davranışına geçer, panelde **Değişim/İade Hattı** sekmesinde görünür.
- Satış gibi test etmek için normal mesaj yazın (ürün, fiyat, sipariş vb.) → **Satış Hattı** davranışı ve listesi.
- Yani: **Aynı numaradan** bazen satış, bazen değişim gibi yazarak iki davranışı da test edebilirsiniz.

## Özet

| Ortam        | Satış / değişim ayrımı |
|-------------|-------------------------|
| **Canlı (iki numara)** | Hangi numaraya mesaj geldiyse o hat (satış / değişim). |
| **Test (tek numara)**  | Değişim numarası yoksa; mesajda iade/değişim varsa → değişim hattı, yoksa → satış hattı. |
