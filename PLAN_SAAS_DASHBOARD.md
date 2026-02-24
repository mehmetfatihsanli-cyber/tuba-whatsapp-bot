# Plan: Kommo Tarzı SaaS Dashboard

## 1. Yapı Özeti

- **Sol sabit sidebar:** Logo + şirket adı (veritabanından, hardcoded değil), menü: Dashboard, Müşteriler, AI Stüdyo.
- **Sağ alan:** İçerik (dashboard’da KPI + modül kartları + canlı akış; Müşteriler’de mevcut sohbet ekranı).
- **Tasarım:** Arka plan #F3F4F6, kartlar beyaz rounded-xl + gölge, font Inter (Google Fonts), Tailwind CDN.

---

## 2. Adres Değişikliği (Panel adresleri güncellenecek)

| Eski | Yeni |
|------|------|
| `/panel` = Mesajlar (sohbet) | `/panel` = **Dashboard** (yeni ana ekran) |
| — | `/panel/messages` = **Mesajlar** (mevcut sohbet ekranı) |
| `/panel/studio` = AI Stüdyo | `/panel/studio` = AI Stüdyo (aynı) |

Giriş sonrası kullanıcı **Dashboard**’a (`/panel`) gidecek; oradan “Müşteriler”e tıklayınca `/panel/messages` açılacak.  
**PANEL_ADRESLERI.md** buna göre güncellenecek.

---

## 3. Dinamik Marka (current_user)

- **Veritabanı:** Supabase’de `tenants` tablosu: `tenant_id` (PK), `company_name`, `logo_url`.
- **Varsayılan (tablo yoksa/boşsa):** Backend’de fallback: tuba → "Tuba Butik", zafer → "Zafer Giyim", ali → "Ali".
- **Şablon:** Tüm panel sayfalarında `current_user.company_name` ve `current_user.logo_url` (Jinja2). Sol üstte logo + isim asla sabit yazılmayacak.

---

## 4. Şablon Yapısı

- **base.html:** Tailwind CDN, Inter font. Sol sidebar (logo, `{{ current_user.company_name }}`, menü linkleri), sağda `{% block content %}`. İsteğe bağlı şifre kapalı banner.
- **index.html (Dashboard):** `extends base`. Üstte 4 KPI kartı (Toplam Ciro, Aktif Sohbetler, Bekleyen İadeler, AI Maliyeti). Ortada 4 modül kartı (Satış & Kombin, İade/Değişim, AI Stüdyo, Entegrasyonlar) – AKTİF/PASİF anahtarı ve butonlar. Sağ altta “Canlı akış” son 5 mesaj.
- **panel.html (Mesajlar):** `extends base`; `content` bloğu mevcut sohbet arayüzü (müşteri listesi + mesaj alanı). Sidebar’daki “Müşteriler” aktif link.
- **studio.html:** `extends base`; mevcut “Yakında” içeriği.

---

## 5. Backend

- **get_tenant_info(tenant_id):** Supabase `tenants` tablosundan company_name, logo_url; yoksa fallback dict. Her panel sayfasında `current_user` olarak şablona geçirilecek.
- **Yeni route:** `/panel` → dashboard (index.html), `/panel/messages` → mesajlar (panel.html).
- **API:** `/api/dashboard/last-messages` → tenant’a göre son 5 mesaj. `/api/dashboard/kpis` → 4 KPI (Toplam Ciro, Aktif Sohbetler, Bekleyen İadeler, AI Maliyeti); ilk aşamada gerçek/Butik verisi veya mock.
- **Modül AKTİF/PASİF:** İlk aşamada sadece arayüz (toggle); istenirse ileride backend’de saklanabilir.

---

## 6. Teknik

- Tailwind: CDN ile dahil; stiller class olarak HTML’de.
- Ayrı CSS dosyası yok (base/index’te inline class’lar).
- Flask’ta giriş yapan tenant’a göre `current_user` (company_name, logo_url) hazırlanacak.

---

## Onay

Bu planı onaylıyorsan “onaylı” yazman yeterli; ardından sırayla:

1. Supabase `tenants` tablosu için SQL + fallback
2. `base.html` ve `index.html` (dashboard)
3. `panel.html` refactor (extends base, /panel/messages)
4. `studio.html` refactor (extends base)
5. `app.py` route ve API güncellemeleri
6. **PANEL_ADRESLERI.md** güncellemesi

yapılacak.
