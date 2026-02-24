# GitHub’a push için kullanıcı adı ve token

Bu rehber: **GitHub kullanıcı adını** ve **Personal Access Token**’ı nerede bulacağını, nasıl kaydedeceğini adım adım anlatır.

---

## Bu token ne işe yarar? (Detay)

**Kısaca:** Bilgisayarındaki proje kodunu GitHub’daki repoya göndermek (`git push`) için kullanıyorsun. GitHub artık şifre ile push kabul etmiyor; “Bu istek gerçekten senin” diyebilmesi için **token** istiyor. Token = senin adına repo’ya yazma yetkisi veren özel bir anahtar.

**Akış:**
1. Sen `git push origin main` yazıyorsun.
2. Git, GitHub’a “Bu kodu fatihsanli/tuba-whatsapp-bot repo’suna yüklemek istiyorum” diyor.
3. GitHub: “Kanıt göster” diyor → sen **kullanıcı adı + token** veriyorsun.
4. Token doğruysa GitHub kodu alıyor; push tamamlanıyor.
5. Railway (eğer bu repo’ya bağlıysa) GitHub’daki yeni kodu görüp canlıya deploy ediyor.

Yani: **Token → GitHub’a push → Railway deploy** zincirinin ilk halkası. Token olmadan push yapamazsın; deploy da güncellenmez.

**“repo” tikinin anlamı:** Bu token’a sadece **repo** yetkisi veriyorsun. Ne yapar: Senin erişebildiğin repolara (tuba-whatsapp-bot dahil) kod gönderebilir (push), okuyabilir (pull/clone). Ne yapmaz: Hesap silme, e-posta değiştirme, başka kullanıcıları yönetme vb. Sadece repolarla çalışmak için; güvenli ve sınırlı.

**90 gün:** Bu token 90 gün geçerli. Süre bitince “yetkisiz” sayılır; push tekrar isim/token ister. O zaman GitHub’da yeni token üretir, terminalde bir kez daha username + yeni token yazarsın; devam edersin.

---

## 1. GitHub kullanıcı adın

- **Nerede:** GitHub’a giriş yaptıktan sonra sağ üstteki profil fotoğrafına tıkla → açılan menüde **kullanıcı adın** yazar (örn. `fatihsanli`).
- **Alternatif:** Tarayıcıda `https://github.com/fatihsanli` gibi bir adres kullanıyorsan, `fatihsanli` kısmı kullanıcı adındır.
- **Kaydetmene gerek yok:** Terminal “Username for 'https://github.com':” dediğinde bu ismi yazıp Enter’a basarsın.

---

## 2. Personal Access Token (şifre yerine kullanılacak)

GitHub artık şifre ile push kabul etmiyor; **token** kullanman gerekiyor.

### Token’ı nerede oluşturursun?

1. **GitHub’a giriş yap:** https://github.com  
2. **Sağ üst** → profil fotoğrafına tıkla → **Settings**.  
3. Sol menüden en alta in → **Developer settings** (Geliştirici ayarları).  
4. Sol menüden **Personal access tokens** → **Tokens (classic)**.  
   - Doğrudan link: https://github.com/settings/tokens  
5. **Generate new token** → **Generate new token (classic)**.  
6. **Note:** İstediğin bir isim yaz (örn. `tuba-bot-push`).  
7. **Expiration:** 90 days veya No expiration seç.  
8. **Scopes:** En az **repo** kutusunu işaretle (tüm alt kutular da işaretlenir).  
9. En alta in → **Generate token**.  
10. **Oluşan token’ı hemen kopyala** (örn. `ghp_xxxxxxxxxxxx`). Bu sayfa bir daha gösterilmez; kaydetmezsen yeniden token üretmen gerekir.

### Token’ı nerede “kaydedersin”?

- **“Kaydetmek”** = Git’in bir daha senden sormaması için bilgiyi saklamak.

**Seçenek A – Sadece bu bilgisayarda (önerilen)**  
Terminalde bir kez şunu çalıştır (token’ı kendi token’ınla değiştir):

```bash
git config --global credential.helper store
```

Sonra ilk kez:

```bash
cd /Users/fatihsanli/tuba-whatsapp-bot
git push origin main
```

- **Username for 'https://github.com':** GitHub kullanıcı adını yaz → Enter.  
- **Password:** Buraya **şifreni değil**, az önce kopyaladığın **token’ı** yapıştır → Enter.

Bu bir kez başarılı olunca, Git bilgileri `~/.git-credentials` dosyasına yazar; sonraki push’larda tekrar sormaz.

**Seçenek B – Her seferinde yazmak**  
`credential.helper store` yapmazsan, her `git push`’ta tekrar username ve token girmen gerekir. Token’ı bir yere (not defteri, şifre yöneticisi) yazıp oradan kopyalayabilirsin.

---

## 3. Kısa özet

| Ne | Nerede bulunur | Nasıl “kaydedilir” |
|----|----------------|---------------------|
| Kullanıcı adı | GitHub sağ üst profil / URL’deki isim | Sadece push sırasında yazarsın; ayrıca kaydetmene gerek yok. |
| Token | GitHub → Settings → Developer settings → Personal access tokens → Generate new token (classic) | `git config --global credential.helper store` + bir kez `git push` yapıp username + token yazınca Git kendi kaydeder. |

---

## 4. Terminal işlemleri – Baştan sırayla

**Hazırlık:** GitHub’da yeni token oluşturduysan, token’ı kopyala (Ctrl+C). Token’ı sohbet veya ekrana yazma; sadece Password alanına yapıştıracaksın.

**Adım 1 – Terminali aç**  
- Mac: Spotlight (Cmd+Space) → “Terminal” yaz → Enter.  
- Veya Cursor içinde: üst menü **Terminal** → **New Terminal**.

**Adım 2 – Proje klasörüne geç**  
Aşağıdaki komutu yazıp Enter’a bas:
```bash
cd /Users/fatihsanli/tuba-whatsapp-bot
```

**Adım 3 – (İsteğe bağlı) Bir daha sormasın diye kaydet**  
Sadece ilk seferde; sonraki push’larda kullanıcı adı ve token sormasın istersen:
```bash
git config --global credential.helper store
```
Enter. Hata vermezse devam et.

**Adım 4 – GitHub’a gönder (push)**  
```bash
git push origin main
```
Enter’a bas.

**Adım 5 – Kullanıcı adı**  
Terminal şunu yazar: `Username for 'https://github.com':`  
→ GitHub kullanıcı adını yaz (örn. `fatihsanli`) → Enter.

**Adım 6 – Token (şifre yerine)**  
Terminal şunu yazar: `Password for 'https://fatihsanli@github.com':`  
→ **Şifreni yazma.** Token’ı yapıştır (Cmd+V). Ekranda görünmez; normal. → Enter.

**Adım 7 – Sonuç**  
“Writing objects: 100%” veya “Everything up-to-date” gibi bir satır görürsen push tamam demektir. Railway bu repo’ya bağlıysa kısa süre sonra deploy da güncellenir.

---

**Özet komut sırası:**  
`cd /Users/fatihsanli/tuba-whatsapp-bot` → `git config --global credential.helper store` → `git push origin main` → Username yaz → Token yapıştır.
