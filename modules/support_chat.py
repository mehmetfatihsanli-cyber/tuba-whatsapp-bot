# Web sitesi ve panel canlı destek chatbot'u.
# Aynı proje modeli (Claude) kullanılır; context'e göre farklı system prompt ile
# ziyaretçi = ürün/fiyat/demo, panel = teknik destek.
# Web sitesi (website): aynı soru tekrar gelince Supabase cache'den döner, token harcanmaz.

import os
import re
import logging
import anthropic
import config

logger = logging.getLogger(__name__)

# Cache tablosu: support_faq_cache (context, question_normalized, reply, created_at) UNIQUE(context, question_normalized)
CACHE_TABLE = "support_faq_cache"


def _normalize_question(text: str) -> str:
    """Aynı sayılan soruları tek anahtarda toplamak için: küçük harf, boşluk birleştir, noktalama kaldır."""
    if not text:
        return ""
    t = text.strip().lower()
    t = re.sub(r"[.?!,;:¿?]+", "", t)
    t = " ".join(t.split())
    return t


# Sabit sorularda token harcanmadan kısa yönlendirme cevabı. (anahtar kelimeler, cevap)
# Soru normalize edilir; içinde anahtar geçiyorsa ilk eşleşen cevap döner.
REDIRECT_RULES_WEBSITE = [
    (["fiyat", "fiyatlar", "ne kadar", "ücret", "paket fiyat", "kaç tl", "kac tl", "ödeme"], "Fiyatlar için sayfada Fiyatlandırma bölümüne bakabilirsiniz; aşağı kaydırın veya menüden \"Fiyatlandırma\"yı seçin."),
    (["nasıl üye", "nasil uye", "üye olurum", "uye olurum", "kayıt", "kayit", "üye olmak", "demo", "denemek"], "Üye olmak için sağ üstten \"Kayıt Ol\" butonunu kullanın veya /register sayfasına gidin. Demo için kayıt yeterli."),
    (["abonelik aylık", "aylık mı", "aylik mi", "ödeme nasıl", "odeme nasil", "fatura"], "Abonelik aylıktır. Detaylar için sayfada Fiyatlandırma bölümüne bakabilirsiniz."),
    (["üyelik zorunlu", "uyelik zorunlu", "zorunlu mu", "şart mı", "sart mi"], "Denemek için kayıt yeterli; abonelik zorunlu değil. \"Kayıt Ol\" ile başlayabilirsiniz."),
    (["özellik", "ozellik", "neler var", "ne sunuyorsunuz", "hizmet"], "Tüm özellikler için sayfada \"Özellikler\" ve \"Panelde Neler Var?\" bölümlerine bakabilirsiniz; menüden de ulaşabilirsiniz."),
    (["iletişim", "iletisim", "destek", "sizinle iletişim", "telefon", "mail"], "İletişim için sayfada İletişim bölümüne inebilir veya formu doldurarak yazabilirsiniz."),
]


def _redirect_reply_website(normalized: str) -> str:
    """Sabit sorularda yönlendirme cevabı döndür. Eşleşme yoksa boş string."""
    if not normalized:
        return ""
    for keywords, reply in REDIRECT_RULES_WEBSITE:
        if any(kw in normalized for kw in keywords):
            return reply
    return ""


SYSTEM_PROMPT_WEBSITE = """Sen "AI Satış" ürününün web sitesi destek asistanısın. Sadece Türkçe cevap ver.
Görevin: Sitede gezen potansiyel müşterilere ürünü anlatmak, fiyat ve özellikleri paylaşmak, kayıt/demo yönlendirmek.

Bilgiler (bunların dışına çıkma):
- Ürün: Moda ve perakende mağazaları için WhatsApp üzerinden 7/24 AI müşteri temsilcisi. Kombin önerisi, iade/değişim, sipariş yönetimi tek panelde.
- Fiyatlandırma: Başlangıç 990₺/ay (1 numara, AI asistan, panel). PRO 1.990₺/ay (önerilen). Kurumsal için iletişime geçmelerini söyle.
- Özellikler: 7/24 AI temsilci, otomatik satış, kombin önerisi, Model Talimatı, Akıllı Bot (Canlı/Dinle+Analiz/Kapat), Analiz & Akıllanma, AI Stüdyo (sanal deneme), Satış Panosu, Analiz Raporu.
- Kayıt: /register veya "Kayıt Ol" ile ücretsiz deneyebilirler. Demo istiyorlarsa kayıt olup paneli keşfetmelerini öner.

Kurallar: Kısa, samimi, profesyonel cevaplar ver. Uydurma fiyat veya özellik yazma. Bilmediğin bir şey varsa "Bu konuda detay için kayıt olup paneli inceleyebilir veya iletişim formundan yazabilirsiniz" de. Emojiyi abartma."""

SYSTEM_PROMPT_PANEL = """Sen "AI Satış" panelinin teknik destek asistanısın. Sadece Türkçe cevap ver.
Kullanıcı zaten giriş yapmış; panelde veya WhatsApp entegrasyonunda takıldığı konularda yardım istiyor.

Yardım verebileceğin konular:
- Panel: Genel Bakış, Satış/Değişim hatları, mesaj geçmişi, pipeline, ayarlar.
- Bot modları: Canlı (bot cevap verir), Dinle+Analiz (mesajlar analiz edilir, cevap gönderilmez; sonra Canlıya alınınca veriler kullanılır), Kapat (sadece manuel).
- Model Talimatı: Mağazaya özel AI talimatları nereden yazılır.
- WhatsApp: Numara bağlama, Meta Business hesabı, doğrulama. "Randevu Al & Destek İste" veya Meta dokümanlarına yönlendir.
- AI Stüdyo: Sanal deneme, manken yükleme, ürün paylaşımı.
- Satış Panosu: Huni, KPI, canlı akış.
- Analiz Raporu: Dinle+Analiz dönemindeki konuşma özeti, niyet/duygu.
- Hata mesajları: Token eksik, webhook doğrulama, 401/403 gibi durumlarda env değişkenlerini (ANTHROPIC_API_KEY, META_ACCESS_TOKEN, PHONE_ID, VERIFY_TOKEN) ve Railway/dokümantasyonu kontrol etmelerini söyle.

Kurallar: Çözüm odaklı, adım adım kısa cevap ver. Kod veya hassas bilgi yazma. Bilmediğin teknik detay için "Destek talebi oluşturun veya dokümantasyona bakın" de. Emojiyi abartma."""


def _get_cached_reply(supabase, context: str, question_normalized: str):
    """Cache'de varsa cevabı döndür, yoksa None."""
    if not supabase or not question_normalized:
        return None
    try:
        r = supabase.table(CACHE_TABLE).select("reply").eq("context", context).eq("question_normalized", question_normalized).limit(1).execute()
        if r.data and len(r.data) > 0 and r.data[0].get("reply"):
            return (r.data[0]["reply"] or "").strip() or None
    except Exception as e:
        logger.warning("[SupportChat] Cache okuma hatası: %s", e)
    return None


def _save_to_cache(supabase, context: str, question_normalized: str, reply: str) -> None:
    if not supabase or not question_normalized or not reply:
        return
    try:
        supabase.table(CACHE_TABLE).upsert(
            {"context": context, "question_normalized": question_normalized, "reply": reply},
            on_conflict="context,question_normalized",
        ).execute()
        logger.info("[SupportChat] Cache'e yazıldı: %s", question_normalized[:50])
    except Exception as e:
        logger.warning("[SupportChat] Cache yazma hatası: %s", e)


def get_support_reply(message: str, context: str, history: list, supabase=None) -> str:
    """
    context: "website" (ziyaretçi) veya "panel" (giriş yapmış kullanıcı)
    history: [ {"role": "user"|"assistant", "content": "..." }, ... ] son N mesaj
    supabase: verilirse website için cache okuma/yazma yapılır (token tasarrufu).
    """
    msg = (message or "").strip()
    if context == "website" and msg:
        normalized = _normalize_question(msg)
        if normalized:
            redirect = _redirect_reply_website(normalized)
            if redirect:
                logger.info("[SupportChat] Yönlendirme cevabı (website), token harcanmadı.")
                return redirect
        if supabase and normalized:
            cached = _get_cached_reply(supabase, "website", normalized)
            if cached:
                logger.info("[SupportChat] Cache hit (website), token harcanmadı.")
                return cached

    api_key = os.getenv("ANTHROPIC_API_KEY") or getattr(config, "ANTHROPIC_API_KEY", None)
    if not api_key or (isinstance(api_key, str) and api_key.strip() == "sk-ant-test"):
        logger.warning("[SupportChat] ANTHROPIC_API_KEY yok - cevap verilemiyor.")
        if context == "website":
            return "Şu an sohbet asistanı geçici olarak kullanılamıyor. Lütfen iletişim formundan yazın veya kayıt olup paneli deneyin."
        return "Teknik destek asistanı şu an kullanılamıyor. Lütfen destek talebi oluşturun."

    system = SYSTEM_PROMPT_WEBSITE if context == "website" else SYSTEM_PROMPT_PANEL
    model = getattr(config, "AI_MODEL", None) or os.getenv("AI_MODEL", "claude-sonnet-4-5")

    messages = []
    for h in history[-10:]:  # son 10 mesaj
        role = "user" if h.get("role") == "user" else "assistant"
        messages.append({"role": role, "content": (h.get("content") or "").strip()})
    messages.append({"role": "user", "content": msg})

    try:
        client = anthropic.Anthropic(api_key=api_key, timeout=20.0)
        response = client.messages.create(
            model=model,
            max_tokens=512,
            temperature=0.4,
            system=system,
            messages=messages,
        )
        reply = (response.content[0].text or "").strip()
        reply = reply or "Cevap oluşturulamadı, tekrar deneyebilir misiniz?"
        logger.info("[SupportChat] Claude cevap üretildi (context=%s).", context)

        if context == "website" and supabase and msg and _normalize_question(msg):
            _save_to_cache(supabase, "website", _normalize_question(msg), reply)

        return reply
    except Exception as e:
        logger.exception("[SupportChat] Claude hatası: %s", e)
        if context == "website":
            return "Bir an sorun yaşandı. Lütfen biraz sonra tekrar deneyin veya iletişim formundan yazın."
        return "Bir an sorun yaşandı. Lütfen tekrar deneyin veya destek talebi oluşturun."
