# Railway MCP Kurulumu – Sıfırdan Adım Adım

Bu rehberde **her tıklama ve her yazacağın şey** tek tek anlatılıyor. Sadece sırayla yap.

---

## TERMİNAL NEDİR, NEREDE?

**Terminal** = Siyah veya koyu renk bir kutu; içine **komut** (İngilizce kelimeler) yazıp **Enter** tuşuna basarsın. Program senin yazdığın komutu çalıştırır.

**Cursor’da terminali açmak:**

1. Cursor programını aç (tuba-whatsapp-bot projesi açık olsun).
2. En **üstte** menü çubuğu var: **File, Edit, Selection, View, Go, Run, Terminal, Help** gibi yazılar.
3. **Terminal** yazısına **tıkla** (tek tık).
4. Açılan küçük menüden **"New Terminal"** yazısına **tıkla**.
   - Bazen **"Terminal"** menüsüne tıklayınca doğrudan terminal açılır; o zaman 5. adıma geç.
5. Ekranın **alt kısmında** veya **ortasında** siyah/koyu gri bir kutu açılacak. İçinde bir satır yazı ve yanıp sönen çizgi (imleç) var. **Bu kutu = Terminal.**

**Görsel tarif:** Alt kısımda “TERMINAL” yazan bir sekme görürsün; yanında “PROBLEMS”, “OUTPUT” gibi sekmeler olabilir. İçinde `$` veya `%` işareti ve yanıp sönen çizgi vardır. Oraya yazacaksın.

---

## BÖLÜM 1: Railway’in Bilgisayarda Kurulu mu Kontrol Et

### Adım 1.1 – Terminali aç

- Yukarıdaki gibi **Terminal → New Terminal** ile terminali aç.
- İmleç (yanıp sönen çizgi) **satırın sonunda** olmalı.

### Adım 1.2 – Komutu yaz (kopyala-yapıştır)

1. Aşağıdaki metni **tamamen seç** (fareyle sürükle veya çift tıkla), sonra **Ctrl+C** (Mac’te **Cmd+C**) ile kopyala:
   ```
   railway --version
   ```
2. Terminal kutusunun **içine** tıkla (bir kez tıklaman yeterli).
3. **Ctrl+V** (Mac’te **Cmd+V**) ile yapıştır. Terminalde `railway --version` yazısı görünecek.
4. **Enter** tuşuna bas (klavyede büyük tuş, genelde sağ tarafta).

### Adım 1.3 – Ne gördün?

**A) Şöyle bir satır çıktıysa (örnek):**
```text
railway version 3.2.1
```
veya benzeri bir numara → **Railway zaten kurulu.** BÖLÜM 2’ye (Railway giriş) geç.

**B) Şöyle bir şey çıktıysa:**
```text
railway: command not found
```
veya
```text
'railway' is not recognized
```
→ **Railway kurulu değil.** Aşağıdaki **Adım 1.4**’e geç; kurulumu yap.

### Adım 1.4 – Railway’i kur (sadece “command not found” dediyse)

**Mac kullanıyorsan:**

1. Terminalde (yine kopyala-yapıştır, sonra Enter):
   ```
   brew install railway
   ```
2. Bir süre yazılar akacak; “Successfully installed” veya benzeri bir cümle görünce kurulum biter.
3. Tekrar kontrol et (kopyala-yapıştır, Enter):
   ```
   railway --version
   ```
   Versiyon numarası çıkıyorsa tamam.

**Windows kullanıyorsan:**

1. Önce Node.js kurulu mu bak: Terminalde yaz (kopyala-yapıştır, Enter):
   ```
   node --version
   ```
   - Bir numara (örn. v20.10.0) çıkarsa Node var. Şu komutu yaz:
     ```
     npm install -g @railway/cli
     ```
     Enter’a bas, kurulum bitsin.
   - “command not found” derse önce [nodejs.org](https://nodejs.org) sitesinden Node.js indirip kur, sonra yukarıdaki `npm install` komutunu tekrarla.
2. Sonra tekrar:
   ```
   railway --version
   ```
   Versiyon çıkıyorsa tamam.

---

## BÖLÜM 2: Railway’e Giriş Yap

1. Terminalde (kopyala-yapıştır, Enter):
   ```
   railway login
   ```
2. **Tarayıcı** (Chrome, Safari, Edge vb.) otomatik açılacak.
3. Açılan sayfa **Railway** sitesine ait. Sayfada:
   - **“Log in with GitHub”** veya **“Email”** ile giriş seçeneği görürsün.
4. **GitHub** ile giriş yapmak en kolayı: O butona tıkla, GitHub hesabınla giriş yap, “Authorize Railway” gibi bir izin ekranı çıkarsa **Authorize** / **İzin ver** de.
5. İşlem bitince sayfada **“Success! You can close this window.”** yazacak. O pencereyi kapat.
6. **Cursor’a dön** (terminal hâlâ açık). Hata yazısı yoksa giriş tamamdır.

---

## BÖLÜM 3: Cursor Ayarlarını Aç (MCP Sayfası)

1. Cursor penceresinde **en sol alt köşeye** bak. Orada **dişli (⚙️) simgesi** var. **Ona tıkla.**
   - Dişli yoksa: En **üst menüden** **Cursor** (veya **File**) → **Preferences** (veya **Settings**) aç.
2. Açılan ayar sayfasında **sol tarafta** liste var:
   - **General**
   - **Features**
   - **Tools & MCP**  ← **Bunu bul ve tıkla.**
3. Sağ tarafta **MCP sunucuları** listesi çıkacak. Listede **“supabase”** ve **“railway”** (veya **Railway**) yazıyor olmalı.
4. **Railway** satırında:
   - Yeşil tik veya **“Connected”** yazıyorsa → Kurulum tamam, BÖLÜM 4’e geç.
   - **“Disconnected”** veya kırmızı uyarı varsa: Cursor’u **tamamen kapat** (Cursor → Quit), tekrar aç, yine **dişli → Tools & MCP** bak. Hâlâ disconnected ise BÖLÜM 2’deki `railway login` i tekrarla.

---

## BÖLÜM 4: Test Et

1. Cursor’da **sağ tarafta** veya **yan panelde** **sohbet (Chat)** kutusunu aç. Genelde üstte veya yanda **“Chat”** / **“Cursor Chat”** yazısı vardır; oraya tıkla.
2. En altta **yazı yazılan kutuya** şunu yaz (veya kopyala-yapıştır):
   ```
   Railway'deki projeleri listele
   ```
3. **Enter**’a bas veya **Gönder** butonuna tıkla.
4. Cevap olarak proje listesi veya Railway ile ilgili bir yanıt gelirse Railway MCP çalışıyor demektir.

---

## Tüm Komutlar Özet (Sırayla kopyala-yapıştır)

Terminalde **sırayla** şunları yazıp Enter’a bas (her seferinde bir tane):

| Sıra | Ne yapacaksın | Kopyalayacağın komut |
|------|----------------|-----------------------|
| 1 | Railway kurulu mu bak | `railway --version` |
| 2 | (Sadece “command not found” dediyse) Mac’te kur | `brew install railway` |
| 2b | (Sadece “command not found” dediyse) Windows’ta kur | `npm install -g @railway/cli` |
| 3 | Tekrar kontrol | `railway --version` |
| 4 | Railway’e giriş yap | `railway login` |

Bunlar bittikten sonra Cursor’da **dişli → Tools & MCP** kısmına girip **railway** satırının “Connected” olduğunu kontrol et.

---

## Sık Sorulanlar

**S: Terminal nerede?**  
C: Cursor’da üst menüden **Terminal** → **New Terminal**. Ekranın altında siyah/koyu kutu açılır; oraya yazacaksın.

**S: Komutu nasıl yapıştırıyorum?**  
C: Komutu kopyala (Ctrl+C / Cmd+C), terminal kutusuna bir kez tıkla, yapıştır (Ctrl+V / Cmd+V), sonra Enter.

**S: “Command not found” ne demek?**  
C: O komut (örn. railway) bilgisayarında kurulu değil demek. Kurulum adımını (brew veya npm) yapman gerek.

**S: Dişli simgesini bulamıyorum.**  
C: Üst menüden **Cursor** (veya **File**) → **Preferences** / **Settings** aç; solda **Tools & MCP** ara.

**S: Railway “Disconnected” kalıyor.**  
C: Önce terminalde `railway login` yap, tarayıcıda girişi tamamla. Sonra Cursor’u kapat-aç, tekrar **Tools & MCP** bak.

Takıldığın adımı (“1. adımda terminali açamadım” gibi) yazarsan, o adımı daha da parçalayıp anlatabilirim.
