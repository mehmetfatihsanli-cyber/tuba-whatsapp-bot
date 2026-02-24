# Panel giriş adresleri

Bu dosyada panel ve ilgili sayfaların adresleri var. Sürekli sormana gerek kalmaz.

---

## Canlıya nasıl çıkarım? (Deploy)

**Hızlı deploy (tek komut – kopyala yapıştır):**
```bash
cd /Users/fatihsanli/tuba-whatsapp-bot && railway up
```

**Adım adım:**
1. Proje klasöründe terminali aç.
2. Şu komutu yaz:
   ```bash
   cd /Users/fatihsanli/tuba-whatsapp-bot
   railway up
   ```
3. Bitti. Railway bu kodu alıp canlıya basar. **GitHub’a git push yapmana gerek yok.**

**Eğer Railway, GitHub repo’na bağlıysa (her push’ta otomatik deploy alıyorsan):**  
O zaman `git add .` → `git commit -m "..."` → `git push origin main` yaparsın; deploy GitHub’dan tetiklenir.

**Özet:** Sen daha önce `railway up` ile çıkardıysan, yapacağın işlem **railway up**. GitHub push, sadece “Railway’i GitHub’a bağladım, her push’ta canlı güncelleniyor” diyorsan gerekir.

---

## Canlı (Railway)

- **Ana sayfa (Landing – tanıtım):**  
  https://tuba-whatsapp-bot-production.up.railway.app

- **Giriş (Tuba / Zafer / Ali buradan girer):**  
  https://tuba-whatsapp-bot-production.up.railway.app/login

- **Dashboard (giriş sonrası – KPI, modüller, canlı akış):**  
  https://tuba-whatsapp-bot-production.up.railway.app/dashboard

- **Mesajlar (Satış Hattı):**  
  https://tuba-whatsapp-bot-production.up.railway.app/dashboard/messages?hat=satis
- **Mesajlar (Değişim/İade Hattı):**  
  https://tuba-whatsapp-bot-production.up.railway.app/dashboard/messages?hat=iade

- **AI Stüdyo (Beta):**  
  https://tuba-whatsapp-bot-production.up.railway.app/dashboard/studio

*(Eski adresler: /panel/login → /login, /panel → /dashboard yönlendirmesi yapılır.)*

---

## Yerel (localhost)

Port varsayılan 5001 ise:

- **Ana sayfa (Landing):** http://localhost:5001
- **Giriş:** http://localhost:5001/login
- **Dashboard:** http://localhost:5001/dashboard
- **Mesajlar (Satış Hattı):** http://localhost:5001/dashboard/messages?hat=satis
- **Mesajlar (Değişim/İade):** http://localhost:5001/dashboard/messages?hat=iade
- **AI Stüdyo:** http://localhost:5001/dashboard/studio

---

## Panel şekillendirme modu (şifreyi geçici kapat)

Paneli **görüp "şunu ekle, rengi böyle olsun"** diyebilmen için şifreyi kaldırmadan geçici kapatıyoruz:

- **Railway:** Variables kısmına ekle: `PANEL_SKIP_LOGIN` = `1`
- **Yerel:** `.env` dosyana ekle: `PANEL_SKIP_LOGIN=1`

Ne olur:
- Ana sayfa yine landing kalır; **"Giriş Yap"** tıklanınca `/login` açılır, şifre kapalıysa direkt `/dashboard`'a yönlendirilir.
- Dashboard'da sarı şerit: *"Şifre kapalı – paneli şekillendirme modu"* görünür.
- Panel istediğin gibi olunca Railway’den **PANEL_SKIP_LOGIN** değişkenini sil (veya `0` yap); şifre tekrar devreye girer. Kodda hiçbir şey silinmez.

---

## Önemli

- **Ana sayfa** artık kurumsal landing (tanıtım). Giriş için **"Giriş Yap"** → `/login`. Böylece ziyaretçi önce markayı görür, giriş yapan paneli kullanır.
- Tuba, Zafer, Ali **mağaza seçip şifre** ile giriş yapar; sadece **kendi tenant’ına ait mesajlar** listelenir.
- **Şifreler:** Railway (ve .env) içinde `PANEL_PASS_TUBA`, `PANEL_PASS_ZAFER`, `PANEL_PASS_ALI` tanımla. Örnek: `PANEL_PASS_TUBA=guclu_sifre_123`
- **Veritabanı:** Mesajların kiracıya ayrılması için Supabase’de `supabase_tek_seferlik_ekleme.sql`; sol üst marka için `supabase_tenants_table.sql` (bir kez).

---

## Özet tablo

| Sayfa          | Canlı URL |
|----------------|-----------|
| Ana sayfa (Landing) | `https://tuba-whatsapp-bot-production.up.railway.app` |
| Giriş          | `https://tuba-whatsapp-bot-production.up.railway.app/login` |
| Dashboard      | `https://tuba-whatsapp-bot-production.up.railway.app/dashboard` |
| Mesajlar (Satış) | `.../dashboard/messages?hat=satis` |
| Mesajlar (İade)  | `.../dashboard/messages?hat=iade`  |
| AI Stüdyo      | `https://tuba-whatsapp-bot-production.up.railway.app/dashboard/studio` |

Son güncelleme: Şubat 2026
