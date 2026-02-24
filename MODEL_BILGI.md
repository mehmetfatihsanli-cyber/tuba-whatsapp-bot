# Hangi model kullanılıyor?

- **Şu anki model:** `claude-sonnet-4-5` (Claude Sonnet 4.5 – güncel, desteklenen model).
- **Nereden geliyor:** `config.py` ve `AI_MODEL` environment variable. Railway’de veya `.env`’de `AI_MODEL` tanımlı değilse bu varsayılan kullanılır.
- **Değiştirmek için:** Railway → Variables → `AI_MODEL=...` (örn. `claude-sonnet-4-5-20250929` sabit sürüm için). Kodda varsayılan: `config.py` ve `modules/ai_assistant.py`.

**Model devre dışı kalırsa (Anthropic yeni sürüm çıkarıp eskisini kaldırırsa):**
1. Railway loglarında `404` veya `not_found_error` / `model: ...` görürsünüz; müşteri “yetkiliye yönlendiriyorum” alır.
2. [Anthropic Models](https://docs.anthropic.com/en/docs/models-overview) sayfasından güncel model ID’yi alın.
3. Railway → Variables → `AI_MODEL` değerini yeni model ID ile güncelleyin (veya projede varsayılanı değiştirip deploy edin).

**“Teknik bir sorun oluştu” mesajı:** Eski backup dosyasında vardı; kaldırıldı. Güncel kodda hata durumunda sadece “Yetkilimize yönlendiriyorum” metni gider.

**İzleme:** Detaylı durum için `docs/IZLEME_VE_SORUN_TESPITI_RAPORU.md` raporuna bakın.

Son güncelleme: Şubat 2026
