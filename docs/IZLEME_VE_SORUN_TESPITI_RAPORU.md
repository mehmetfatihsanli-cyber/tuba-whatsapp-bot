# İzleme ve Sorun Tespiti Raporu

**Tarih:** Şubat 2026  
**Amaç:** Model devre dışı kalması, API hataları ve müdahale hızı açısından mevcut yapının değerlendirilmesi.

---

## 1. Mevcut Durum Özeti

### 1.1 Model (Claude) ile ilgili

| Konu | Şu an ne var? | Eksik / risk |
|------|----------------|--------------|
| **Model devre dışı kalırsa nasıl anlarız?** | Sadece **canlıda hata** oluşunca: müşteri “yetkiliye yönlendiriyorum” görür, siz Railway loglarına bakınca 404 / `not_found_error` görürsünüz. | **Proaktif kontrol yok.** Anthropic yeni model çıkarıp eskisini kaldırdığında önceden haberimiz olmaz. |
| **API key kontrolü** | `check_ortam.py` (yerel): key var mı, uzunluk, `sk-ant-` ile başlıyor mu. `/api/check-model`: sadece key **tanımlı mı** bakar, key’i göstermez. | **Gerçek API çağrısı yok.** Model ID’nin hâlâ geçerli olduğu kontrol edilmiyor. |
| **Hata anında ne oluyor?** | `ai_assistant.py` içinde `except` ile yakalanıyor → `logger.exception(...)` → müşteriye “yetkilimize yönlendiriyorum” gidiyor. | Log’a yazılıyor ama **uyarı/alert yok**; sorunu siz manuel log inceleyerek görüyorsunuz. |

### 1.2 Diğer bileşenler

| Bileşen | Kontrol / izleme | Eksik |
|---------|-------------------|-------|
| **ButikSistem** | Sadece çağrı anında: hata olursa `print("❌ API Hatası: ...")` ve log. | Periyodik sağlık kontrolü yok; MaxQueryRangeIs30Days gibi hatalar yine log’dan fark ediliyor. |
| **Supabase** | Başlangıçta bağlantı denemesi; `check_ortam.py` ile yerel test. | Canlıda periyodik “Supabase erişilebilir mi?” kontrolü yok. |
| **WhatsApp (Meta)** | Webhook çalışınca mesaj gelir; token geçersizse gönderim hata verir, log’a düşer. | Token süresi dolmadan uyarı yok. |

### 1.3 Health check

- **PROJECT_SPEC.md:** `GET /health` → `{"status": "ok"}` tanımlı.
- **Uygulama:** `app.py` içinde **`/health` route’u yok.** Railway veya başka bir sistem “canlı mı?” diye tek endpoint’e bakamıyor.

---

## 2. Sorunlara Müdahale Hızı

| Aşama | Nasıl öğreniyorsunuz? | Tahmini süre |
|-------|------------------------|--------------|
| Sorun çıktı | Müşteri şikayeti veya sizin log’a bakmanız | 0 (şans) – birkaç saat / 1 gün |
| Teşhis | Railway deploy logları / `get-logs` ile inceleme | 5–15 dakika (log’u bulunca) |
| Çözüm | Model/env değişikliği + deploy veya kod düzeltmesi | 10–30 dakika |

**Sonuç:** Sorun **reaktif** tespit ediliyor; “model kalktı” veya “Butik 30 gün hatası” gibi durumlar ancak biri mesaj atıp hata görünce veya siz log’a bakınca ortaya çıkıyor. Proaktif (otomatik) bir “model geçerli mi?” veya “son 1 saatte Claude 404 arttı mı?” kontrolü yok.

---

## 3. Mevcut Yapının Yeterliliği

- **Küçük ölçek / az mesaj:** Şu anki yapı (log + manuel kontrol) çoğu zaman yeterli; sorun çıkınca log’dan teşhis edilebiliyor.
- **Büyüme / daha fazla müşteri:** Aynı yapıda kalırsa:
  - Model değişimi / kalkması yine “ilk hata”da fark edilecek.
  - Hata oranı artsa bile otomatik uyarı olmayacak; müdahale hızı insanın log’a bakmasına bağlı kalacak.

Yani **“olan durum”** şu an için **çalışıyor** ama **“model devre dışı kaldı / API değişti”** gibi durumları **erken ve otomatik** görmüyoruz; **yeterli mi?** sorusu için: “Şimdilik evet, ileride daha sık sorun yaşamak istemiyorsan iyileştirme yapılmalı” cevabı doğru.

---

## 4. Önerilen İyileştirmeler (Öncelik Sırasıyla)

### 4.1 Hemen yapılabilecekler (düşük efor)

1. **`GET /health` eklenmesi**  
   - PROJECT_SPEC’te var, kodda yok.  
   - `app.py` içine örn. `GET /health` → `{"status": "ok", "timestamp": "..."}` eklensin.  
   - Railway veya harici izleme “canlı mı?” diye bu endpoint’e bakabilsin.

2. **`/api/check-model` genişletilmesi**  
   - Şu an: Sadece “ANTHROPIC_API_KEY var mı?”  
   - Öneri: İsteğe bağlı **gerçek bir test çağrısı** (tek mesaj, düşük token) ile:
     - Key geçerli mi?
     - **Kullanılan model ID (AI_MODEL) hâlâ API’de var mı?**  
   - Dönüşe örn. `model_ok: true/false`, `error_type: "not_found" | "auth" | null` eklenebilir.  
   - Böylece panel veya periyodik kontrol ile “model devre dışı” **proaktif** görülebilir.

3. **MODEL_BILGI.md güncellemesi**  
   - Varsayılan/önerilen model adı güncel olsun (örn. `claude-sonnet-4-5`).  
   - “Model değişince ne yapılır?” kısa adımlar halinde yazılsın (Railway Variables → `AI_MODEL`, dokümanlar).

### 4.2 Orta vadede (isteğe bağlı)

4. **Basit “sağlık” endpoint’i: `/api/health` veya `/health` detaylı**  
   - Örn: Supabase’e tek SELECT, (opsiyonel) Claude’a tek minimal istek.  
   - Dönüş: `supabase_ok`, `claude_model_ok` gibi alanlar.  
   - Cron veya harici izleme (UptimeRobot, vb.) ile 5–15 dk’da bir çağrılıp “kırmızı” verince bildirim alınabilir.

5. **Hata sınıflarının log’da netleştirilmesi**  
   - Claude 404 → `[CLAUDE_MODEL_NOT_FOUND]`  
   - Butik MaxQueryRange → `[BUTIK_RANGE_ERROR]`  
   - Böylece log aramak ve ileride basit alert kuralları yazmak kolaylaşır.

### 4.3 Uzun vadede (büyüme olursa)

6. **Alerting**  
   - Railway log’ları veya uygulama içi metrikler bir servise (örn. Sentry, Grafana, vb.) gönderilip “son 1 saatte 5+ Claude 404” gibi kurallarla bildirim.

7. **Model sürüm stratejisi**  
   - Sabit tarihli model ID kullanıyorsanız (örn. `claude-sonnet-4-5-20250929`), Anthropic deprecation duyurularını takip etmek; `-latest` alias kullanıyorsanız dokümanları periyodik kontrol (yılda 1–2 kez).

---

## 5. Sonuç Tablosu

| Soru | Cevap |
|------|--------|
| Model devre dışı kalınca nasıl anlayacağız? | Şu an: **Sadece canlı hata + log.** Öneri: `/api/check-model` ile gerçek model kontrolü ve isteğe bağlı periyodik çalıştırma. |
| Herhangi bir sorun olduğunda nereden bilgimiz olacak? | Şu an: **Log (Railway) + müşteri geri bildirimi.** Otomatik uyarı yok. İyileştirme: `/health` + genişletilmiş check-model + (opsiyonel) harici izleme. |
| Daha verimli kullanma olasılığı? | Evet: Health endpoint, check-model’e “model geçerli mi?” eklenmesi ve (ileride) basit alerting ile müdahale hızı artar. |
| Olan durum yeterli mi? | Az trafik için **kısmen yeterli**; model/API değişimlerine **erken** müdahale için **yetersiz**. |
| Sorunlara müdahale hızı? | **Reaktif:** Sorun çıktıktan sonra log ile teşhis (dakikalar–saatler). Proaktif kontrol olmadığı için “ilk hatada” fark ediyoruz. |

---

## 6. Düzenlenmesi Gerekenler (Kısa Liste)

- [ ] **app.py:** `GET /health` route ekle (`{"status": "ok"}` + isteğe bağlı timestamp).
- [ ] **app.py:** `/api/check-model` içinde (opsiyonel) gerçek Claude test çağrısı ve `model_ok` / `error_type` dönüşü.
- [ ] **MODEL_BILGI.md:** Güncel model adı ve “model değişince ne yapılır?” adımları.
- [ ] (İsteğe bağlı) **check_ortam.py:** Model ID’yi env’den okuyup “Anthropic’te bu model var mı?” için tek bir test çağrısı (yerel kurulum kontrolü).

Bu rapor, proje yapısı ve mevcut kod taramasına dayanarak hazırlanmıştır; izleme/alerting için harici servis detayları (Sentry, UptimeRobot vb.) ayrıca seçilip yapılandırılmalıdır.
