# Bağlam Özeti – Cursor Sohbeti + Nerede Kaldık

Bu dosya: proje özeti ve "nerede kaldık" bilgisi.  
**Her yeni sohbet / yeni gün:** Cursor'a şunu yaz: **@BAGLAM_OZETI.md @TODO.md oku, son duruma göre devam edelim.**  
(Detay: `CURSOR_BASLARKEN.md`)

---

## 1. Proje (Tuba WhatsApp Bot)

- **Amaç:** Tuba Butik WhatsApp’ına gelen mesajlara AI asistan (Claude) ile cevap; sipariş/iade/değişim kuralları, geçmiş konuşma bilgisi.
- **Akış:** WhatsApp → Meta webhook → app.py → Supabase (messages) → AI cevap → WhatsApp’a gönder.

---

## 2. Yapılanlar (Koddan + Konuşmalardan)

| Bileşen | Durum |
|--------|--------|
| Flask + webhook (GET/POST) | ✅ |
| Meta WhatsApp (mesaj al/gönder) | ✅ (webhook çalışıyor) |
| Supabase `messages` (kayıt + geçmiş konuşma AI’ya) | ✅ |
| ButikSistem client (sipariş: önce Butik API, yoksa test_orders) | ✅ Bağlı |
| AI asistan (Claude, Tuba kuralları, iade/değişim, kızgın → yönlendir) | ✅ |
| Panel (/panel, son 50 mesaj, panelden mesaj gönder) | ✅ |
| Pinecone (index + modül) | ✅ Cevap akışında kullanılıyor (_satis_urun_context, satış kelimeleri) |
| GitHub repo | ✅ Bağlı |
| Railway deploy | ✅ Yapıldı / railway up kullanıldı |
| Meta 404 hatası | ✅ Çözüm uygulandı (loglar incelendi) |

---

## 2b. Cursor sohbeti – Şubat 2026 (Supabase MCP + RLS)

Bu bölüm başka bir Cursor sohbetinde yapılan işler; diğer sohbetler @BAGLAM_OZETI.md okuyunca haberdar olsun diye ekleniyor.

| Yapılan | Açıklama |
|--------|----------|
| **Supabase MCP** | Cursor’a Supabase MCP bağlandı (Settings → Tools & MCP; Connect ile giriş yapıldı). Cursor artık “Supabase’deki tabloları listele” gibi komutlarla doğrudan Supabase’e erişebilir. Ek maliyet yok. |
| **RLS açıldı** | Tüm ilgili tablolarda Row Level Security açıldı: `tenants`, `messages`, `customers`, `conversation_state`, `media_files`, `conversations`. Backend service_role kullandığı için test mesajları ve akış etkilenmez. |
| **conversations tablosu** | Proje kodunda kullanılmıyor (eski/kopya tablo); yine de RLS açıldı, Supabase’te kırmızı “RLS disabled” kalktı. |
| **Rehberler** | `CURSOR_KULLANIM_REHBERI.md` (yazılım bilmeyenler için), `SUPABASE_MCP_CURSOR_REHBERI.md`, `RLS_NEDIR_VE_NASIL_CALISIR.md`, `META_MODEL_TEST_KONTROL.md` projede mevcut. |
| **.cursor/mcp.json** | Projede Supabase MCP URL’i tanımlı; Cursor’da “Add to Cursor” veya bu dosya ile MCP kullanılabiliyor. |

---

## 2c. Şubat 2026 – Satış/Değişim hatları, kargo akışları, Supabase + deploy

| Yapılan | Açıklama |
|--------|----------|
| **Satış kargo (iki aşama)** | Müşteri bilgi gönderir → özet + "Tamam/Gönderin yazın" → onayda Butik’te sipariş. Ödeme: peşin / kapıda nakit / kapıda kredi / havale. Başarı mesajı: "Kargonuz oluşturuldu" (Butik adı yok). |
| **Değişim kargo** | Adres son siparişten; "farklı adres" derse yeni adres alınır, onayda Butik sipariş (whoPaysShipping: recipient). Tablo: `exchange_cargo_pending`. |
| **Satış / Değişim hatları** | İki numara: satış numarası → `line=sales`, değişim numarası → `line=exchange`. Mesajlar ve müşteriler `tenant_id` + `line` ile kaydedilir. Panel: Satış Hattı / Değişim İade Hattı sekmeleri; mesajlar karışmaz. Model: "Satış hattındasın" / "Değişim hattındasın" prompt ile davranır. |
| **Tek numara test** | Değişim numarası tanımlı değilse, mesajda "iade"/"değişim" geçiyorsa o mesaj otomatik `line=exchange` sayılır; aynı numaradan iki davranış test edilebilir. |
| **Supabase migration (MCP)** | `add_line_sales_exchange`: tenants (whatsapp_phone_number_id_exchange, whatsapp_access_token_exchange), messages.line, customers.line. `add_exchange_cargo_pending`: exchange_cargo_pending tablosu. MCP ile uygulandı (proje: tuba-whatsapp-bot). |
| **Railway deploy** | Deploy MCP ile tetiklendi; canlıda güncel kod çalışıyor. |
| **Doküman** | `docs/SATIS_DEGISIM_HATLARI.md` (tek/çift numara, canlıya alma). `docs/GUN_SONU_OZET.md` (gün sonu durum). |

---

## 2d. 8 Şubat 2026 – AI Stüdyo: Kategoriler, manken Kaldır, prompt açıklaması, deploy

| Yapılan | Açıklama |
|--------|----------|
| **Kategoriler genişletildi** | Panelde: Bluz/Gömlek/Ceket, Pantolon, Etek, Elbise (+ Üst/Alt genel). Replicate sadece 3 tip (upper_body, lower_body, dresses) kabul ettiği için backend’de eşleme: bluz/gomlek/ceket→upper_body, pantolon/etek→lower_body, elbise→dresses. `virtual_studio.CATEGORY_MAP` ve `app.py` form kabulü güncellendi. |
| **Varsayılan manken Kaldır** | Backend: `POST/DELETE /api/ai-studio/default-mannequin/remove` eklendi (dosya silinir). Panel: “Manken görseli ayarlandı” satırının yanına **Kaldır** butonu; tıklanınca API çağrılıp durum güncelleniyor. |
| **Metin prompt açıklaması** | “Bu resim nasıl olsun?” alanının altına not: “Bu metin, AI’a kıyafet açıklaması olarak gönderilir; kategori ile birlikte sonucu etkiler.” Metin zaten Replicate’e `garment_des` olarak gidiyordu; kullanıcı netleşsin diye açıklama eklendi. Kategori alanına da “Kıyafet tipine uygun kategoriyi seçin” notu eklendi. |
| **Railway deploy** | `railway up` ile canlıya alındı. AI Stüdyo güncel: kategoriler, Kaldır butonu ve prompt notu yayında. |

---

## 2e. Şubat 2026 – Dinle+Analiz akıllanma, prompt önceliği, Bot modu sadeleştirme, deploy

| Yapılan | Açıklama |
|--------|----------|
| **Analiz → modele (akıllanma)** | Dinle+Analiz döneminde toplanan veriler: **satış hattı** analizleri sadece satış model prompt’una, **değişim hattı** analizleri sadece değişim model prompt’una ekleniyor. Son 2 günlük özet (~420 karakter, token dostu) `get_analysis_summary_for_prompt(tenant_id, line, days=2)` ile alınıp `mesaj_olustur(..., analysis_summary_for_prompt=...)` ile prompt’a ekleniyor. |
| **Prompt önceliği (çakışma önleme)** | Üç kaynak (temel kurallar, panel talimatları, analiz özeti) birleşince system prompt’un başına kısa metin ekleniyor: (1) Temel kurallar her zaman geçerli, (2) Panel talimatları tamamlar; çakışırsa temel öncelikli, (3) Analiz özeti sadece bilgi/bağlam; kuralları gevşetme. `ai_assistant.py` içinde `_PROMPT_HIERARCHY`. |
| **Bot modu sadeleştirme** | WhatsApp Ayarlar sayfasındaki “Bot modu” bölümü (Canlı / Sadece dinle / Dinle+Analiz + Kaydet butonu) kaldırıldı. Satış ve Değişim modu **yalnızca Genel Bakış**’taki kartlardan (Canlı \| Dinle+Analiz \| Kapat) yönetiliyor. Dinle+Analiz’te gelen mesajlar otomatik `message_analyses`’e yazılıyor; ekstra kaydetme butonu yok. Ayarlar sayfasında kısa bilgi metni eklendi. |
| **Railway deploy** | Değişiklikler `railway up` ile canlıya alındı. |

---

## 3. Gemini Konuşmasından Önemli Noktalar

- **Canlı ortam:** Sistem çalışırken güncelleme yapılabilir; büyük kod değişikliğinde test ortamında dene veya az yoğun saatte güncelle.
- **WhatsApp + Tuba:** API kullanılan numara sadece bot; Tuba web panelden “manuel müdahale” veya “canlı destek” ile devreye girer.
- **Geçiş planı:** Test → Beta (Railway + test numaraları) → Pilot müşteriler → Tam canlı.
- **SEO Ajansı (ileride):** Cursor + Python ile; n8n yerine Python tercih edildi. Önce WhatsApp botu bitir, sonra SEO projesi.
- **Cursor’a verilen 1. emir (Gemini’nin son mesajı):**  
  `requirements.txt`’e `pinecone-client`, `openai`, `python-dotenv` ekle; pip install; `.env` için gerekli anahtar listesini (PINECONE_API_KEY, OPENAI_API_KEY vb.) ver.

---

## 4. Nerede Kaldık (Son Durum)

- **Proje tarafı:** Railway’de güncel deploy çalışıyor. Satış kargo (iki aşama, peşin/kapıda/havale) ve değişim kargo (son adres / farklı adres, onayda Butik) akışları canlıda. Satış ve değişim **hat ayrımı** (numara → line; panelde iki sekme; model hatta göre davranır) tamamlandı. Tek numara test modu: iade/değişim kelimesi geçen mesajlar exchange sayılıyor. Supabase’te `messages.line`, `customers.line`, `exchange_cargo_pending` ve tenants’ta değişim numarası alanları mevcut. **AI Stüdyo (8 Şubat):** Kategoriler (Bluz/Pantolon/Etek/Elbise), varsayılan manken “Kaldır” butonu ve API, metin prompt açıklaması canlıda. **Şubat (2e):** Dinle+Analiz akıllanma (satış/değişim analiz özeti ilgili hattın prompt’una kısa ekleniyor), prompt önceliği metni (çakışma önleme), Bot modu yalnızca Genel Bakış’tan; Ayarlar sayfasında bot modu bloğu kaldırıldı.
- **Olası sıradaki adımlar:**  
  1) E-posta (şifre sıfırlama) kurulumu (TODO.md),  
  2) Canlıda iki numara tanımlanınca (Tuba/Zafer/Ali) panelden Ayarlar > WhatsApp > Değişim hattı doldurulacak,  
  3) İsteğe bağlı: Butik test siparişi + log kontrolü.

---

## 5. Dosya Referansları

- **Tam Gemini konuşması:** `GECMIS_LOGLARI.md` (satır 79’dan itibaren, ~14340 satır). Derin detay için bu dosyaya bakılabilir.
- **Yol haritası:** `YOL_HARITASI.md`, **Model tam çözüm:** `YOL_HARITASI_MODEL_TAM_COZUM.md`
- **Yapılacaklar:** `TODO.md`
- **Butik API:** `BUTIK_API_DOKUMANTASYON.md`

---

**Son güncelleme:** Şubat 2026 (Dinle+Analiz akıllanma, prompt önceliği, Bot modu sadece Genel Bakış, deploy)  
**Kullanım:** Yeni sohbet/gün: `@BAGLAM_OZETI.md @TODO.md oku, son duruma göre devam edelim.` İş bittiğinde TODO.md güncelle. “nerede kaldık” 