# Tuba Bot – Veri Kaynakları (XML, Butik, Model)

## Özet

| Kaynak        | Ne çekiyoruz?      | Model ne zaman kullanıyor? |
|---------------|--------------------|----------------------------|
| **Tuba XML**  | Ürün listesi (id, isim, fiyat, stok, beden, renk, link) | Dolaylı: XML → sync → **Pinecone** → model Pinecone’a bakıyor |
| **Butik API** | Siparişler (order/get), **ürün/stok (product/get)**    | Sipariş: her mesajda telefonla sorgu. Ürün: Pinecone boşsa **ürün kodu** varsa canlı product/get |

---

## 1. Tuba XML

- **Dosya:** `sync_products.py` (proje kökü)
- **URL:** `https://www.tubamutioglu.com/xml.php?c=facebookproduct&xmlc=...`
- **Akış:** XML indirilir → parse (id, title, price, quantity, size, color, link) → **Pinecone**’a yazılır.
- **Model:** Mesaj anında **XML’e istek atmıyor**. Sadece daha önce sync edilmiş **Pinecone** verisine bakıyor (`_satis_urun_context`).
- **Güncellik:** Sync’i siz çalıştırıyorsunuz (`python sync_products.py`). Ne sıklıkla çalıştırırsanız stok o kadar güncel olur.

Yani: XML’den çekebiliyoruz, model “bakıyor” ama **Pinecone üzerinden**; canlı XML çağrısı yok.

---

## 2. Butik Sistem API

- **Dosya:** `modules/butiksistem_client.py`
- **Kullanılan endpoint’ler:**
  - **order/get** – Sipariş listesi (tarih aralığı). Model, müşteri telefonuyla `check_order_by_phone` ile siparişleri CONTEXT’e alıyor. **Canlı.**
  - **product/get** – Ürün kodu (modelCode) ile ürün + stok. **Yeni eklendi:** Model, satış sorularında önce Pinecone’a bakıyor; **Pinecone’da eşleşme yoksa** mesajda ürün kodu (örn. `2209_t1`) görürse Butik’ten **canlı** ürün/stok çekip CONTEXT’e ekliyor.

Yani: Sipariş için zaten canlı kullanıyorduk; ürün/stok için de artık **ürün kodu** geçen sorularda (Pinecone boşsa) Butik’e bakıyoruz.

---

## 3. Modelin gördüğü veri (CONTEXT)

- **Sipariş:** Butik `check_order_by_phone` → CONTEXT’e sipariş listesi.
- **Ürün / stok:**
  1. Önce **Pinecone** (XML sync’ten gelen veri): semantik arama + stokta olanlar.
  2. Pinecone’da sonuç yoksa ve mesajda **ürün kodu** (örn. `2209_t1`) varsa → **Butik product/get** ile tek ürün bilgisi + stok CONTEXT’e eklenir.

Böylece hem XML (Pinecone) hem Butik (sipariş + ürün kodu fallback) kullanılmış oluyor; “bakamıyor” kısmı, ürün kodu fallback eklenene kadar sadece Pinecone’a bağlıydı ve Butik ürün API’si bağlı değildi.

---

## 4. modules/sync_products.py (Butik → Pinecone)

- Bu script **Butik’ten ürün listesi** alıp Pinecone’a yazmak için yazılmış ama `ButikSistemClient.urunleri_getir()` **tanımlı değildi**; sadece `order/get` vardı.
- Şu an **ürün verisi** için kullanılan kaynaklar:
  - **Pinecone:** Kök `sync_products.py` ile **Tuba XML**’den dolduruluyor.
  - **Canlı stok:** Mesaj anında **product/get** ile tek ürün (ürün koduyla) Butik’ten alınıyor (Pinecone boşsa).

**Güncel:** `urunleri_getir()` eklendi. XML alternatifi: `python -m modules.sync_products` ile Butik'ten sync alınabilir. İsterseniz ileride `urunleri_getir()` (Butik’ten toplu ürün listesi) ekleyip `modules/sync_products.py` ile Butik → Pinecone sync de açılabilir; şu an zorunlu değil.
