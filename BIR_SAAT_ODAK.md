# Bugün 1 Saat – Odak ve Çalışma Şeklimiz

Bu dosya: **seni tanımam**, **beni anlaman** ve **bugün 1 saatte tek kritik adım** için.

---

## Çalışma anlaşması (ikimiz)

- **Sen:** Uzun adım adım anlatım istemiyorsun. "Bunu yap, buraya git, şunu yapıştır, bitince bana yaz" tarzı kısa talimat yeterli.
- **Ben:** Yapabileceğim her şeyi (kod, dosya, SQL vb.) ben yapıyorum. Senin yapman gereken tek iş kaldığında kısa ve net söylüyorum; uzun açıklama yapmıyorum.
- **Bitince:** Sen "bitti" / "yaptım" deyince bir sonraki adıma geçiyoruz.

---

## Ben nasıl çalışıyorum (senin beni anlaman için)

- **Ne yapıyorum:** Kod ve dosyaları okuyup değiştiriyorum; sen “şunu yapalım” dediğinde adım adım yapıyorum. Bazen “şu eksik, önce onu tamamlayalım” diye öneri de veriyorum.
- **Nasıl iletişim kuruyoruz:** Sen Türkçe yazıyorsun; ben de Türkçe, sade ve mümkünse teknik jargon kullanmadan cevaplıyorum. “Şu butona tıkla”, “şu komutu kopyala-yapıştır” gibi net talimatlar verebilirim.
- **Sınırlarım:** Gerçek zamanlı ekranına bakamam; senin bilgisayarında bir şeyi “sen” yapacaksın (ör. Supabase’de SQL çalıştırmak, Railway’de env eklemek). Ben ne yapacağını adım adım yazarım, sen takip edersin.
- **Senin tarafın:** Proje ve iş tarafını sen biliyorsun (kanayan yaralar, ne öncelikli); kod tarafını ben hallederim. “Müşteri iade istediğinde şöyle olsun” dersen kuralı yazarım; “Butik’ten sipariş çekelim” dersen entegrasyonu tarif ederim.

Kısaca: **Sen işi ve önceliği söylüyorsun, ben teknik kısmı yapıyorum; birlikte adım adım ilerliyoruz.**

---

## Seni nasıl anladım

- Kod tarafında acemisin; komutları çoğunlukla **kopyala-yapıştır** ile kullanıyorsun.
- **Proje ve süreç** tecrüben var; “neyin işe yarayacağını” biliyorsun.
- **Kodsuz otomasyon** ile başlayıp bu projeye kadar gelmişsin; teknik detaylar yerine “ne yapacağız, sırada ne var” net olsun istiyorsun.
- Bu yüzden: **uzun kod açıklamaları yerine kısa özet + yapılacaklar listesi** vereceğim; gerektiğinde “şuraya tıkla”, “şunu yapıştır” diyeceğim.

---

## Elimizdekiler (şu an projede kullanılan / hazır olan)

| Ne | Durum | Not |
|----|--------|-----|
| **Butik Sistem API** | Var, dokümantasyon elinde | Kodda `ButikSistemClient` hazır; `BUTIK_API_URL`, `BUTIK_API_USER`, `BUTIK_API_PASS` ile çalışır. Henüz AI cevabına “canlı sipariş” bağlanmadı; test verisi kullanılıyor. |
| **Railway** | Bağlantı var | Projeyi deploy edip çalıştırabilirsin; webhook adresi Railway’den alınacak. |
| **WhatsApp (Meta) API** | Projede kullanılıyor | Token ve Phone ID env’de olunca mesaj alır / gönderir. |
| **Claude (Anthropic) API** | Projede kullanılıyor | Cevap üretimi buna bağlı; API key env’de olmalı. |
| **Pinecone** | Kodda var | Ürün araması için; “ilk çalışan versiyon” için zorunlu değil, sonra açılabilir. |

---

## Eksikler / Belirsizlikler (projemize göre kritik olanlar)

| Ne | Neden kritik | Ne yapacağız |
|----|----------------|--------------|
| **Supabase tablosu** | Mesajlar `messages` tablosuna yazılıyor. Tablo yoksa uygulama hata verir. | Supabase SQL Editor’da tek seferlik bir SQL çalıştıracağız; tablo oluşacak. Dosya: `supabase_messages_table.sql` |
| **Supabase / env değişkenleri** | `SUPABASE_URL`, `SUPABASE_KEY` yoksa veya yanlışsa mesaj kaydedilmez, geçmiş konuşma çalışmaz. | Hangi env’lerin gerekli olduğunu listeleyeceğiz; sen .env ve Railway’e yazacaksın. |
| **Tüm env’lerin yerinde olması** | Eksik key/token varsa webhook, AI veya WhatsApp aşamasında durur. | `check_ortam.py` script’i: “Hangi env tamam, hangisi eksik?” diye rapor verecek; sen sadece çalıştırıp bakacaksın. |

**Pinecone:** Şu an “ilk çalışan bot” için zorunlu değil; istersen sonra açarız.

**Özet:** En kritik nokta, **zincirin kırılmaması**: Supabase’de tablo olsun, env’ler (Supabase + Anthropic + Meta) doğru ve eksiksiz olsun. Bunu bugün 1 saatte netleştirirsek, sonraki adım (deploy + gerçek WhatsApp testi) kolaylaşır.

---

## Bugün 1 saat için: TEK KRİTİK ADIM

**Hedef:** “Mesaj geldi → DB’ye yazıldı → AI cevap verdi → WhatsApp’a gitti” zincirinin **ortam** tarafında kırık kalmasın.

**Yapılacaklar (sırayla):**

1. **Ortam kontrolü**
   - Proje klasöründe terminalde:  
     `python3 check_ortam.py`  
   - Çıktıda **EKSİK** yazan her şeyi .env dosyana (ve gerekiyorsa Railway’e) ekle.  
   - Tekrar `python3 check_ortam.py` çalıştır; hepsi **TAMAM** olana kadar düzelt.

2. **Supabase’de `messages` tablosu**
   - Supabase dashboard → SQL Editor.
   - `supabase_messages_table.sql` dosyasının içini kopyala, yapıştır, çalıştır.
   - “Table already exists” veya “Created” benzeri bir sonuç yeterli.

3. **Kısa özet**
   - En kritik müdahale: **ortamın tam ve doğru olması** (env + Supabase tablosu).  
   - Bunlar tamamsa bir sonraki oturumda: Railway’e deploy → webhook URL’i Meta’ya verme → WhatsApp’tan test mesajı.

İstersen bir sonraki mesajda “check_ortam çalıştırdım, şu satır EKSİK diyor” diye yaz; birlikte tek tek tamamlarız.
