import os
import json
import re
import anthropic
from modules.tuba_rules import TubaButikKurallari
import config
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Duygusal zeka: Claude'dan beklenen JSON anahtarları
SENTIMENT_VALUES = ("positive", "neutral", "negative", "angry")
INTENT_VALUES = ("question", "purchase_signal", "complaint", "return_request", "greeting")
URGENCY_VALUES = ("low", "medium", "high")

STRUCTURED_OUTPUT_INSTRUCTION = """Cevap vermeden önce müşteri mesajını analiz et. Yanıtın SADECE aşağıdaki JSON nesnesi olsun, başka metin yazma.
Geçerli değerler:
- sentiment: positive, neutral, negative, angry
- intent: question (soru), purchase_signal (satın alma sinyali), complaint (şikayet), return_request (iade talebi), greeting (selamlaşma)
- urgency: low, medium, high
- reply: Müşteriye yazılacak cevap metni (Türkçe, samimi, tek mesaj)

Örnek format:
{"sentiment": "neutral", "intent": "question", "urgency": "medium", "reply": "Tabii, size yardımcı olayım..."}"""


def _parse_structured_response(raw_text):
    """
    Claude yanıtından JSON çıkar. Önce doğrudan parse, olmazsa regex ile {...} ayıkla.
    Returns: (reply_text, analysis_dict) veya (raw_text, None) hata durumunda.
    """
    if not raw_text or not isinstance(raw_text, str):
        return (raw_text or "", None)
    text = raw_text.strip()
    analysis = None
    reply = text
    try:
        data = json.loads(text)
        if isinstance(data, dict) and "reply" in data:
            reply = (data.get("reply") or "").strip() or text
            s = (data.get("sentiment") or "").strip().lower()
            i = (data.get("intent") or "").strip().lower()
            u = (data.get("urgency") or "").strip().lower()
            if s in SENTIMENT_VALUES:
                analysis = {"sentiment": s, "intent": i if i in INTENT_VALUES else None, "urgency": u if u in URGENCY_VALUES else None, "reply": reply}
            else:
                analysis = {"sentiment": s or None, "intent": i if i in INTENT_VALUES else None, "urgency": u if u in URGENCY_VALUES else None, "reply": reply}
            return (reply, analysis)
    except (json.JSONDecodeError, TypeError):
        pass
    # Süslü parantez eşleştirerek JSON bloğu ayıkla (reply içinde } olabilir)
    start = text.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        data = json.loads(text[start : i + 1])
                        if isinstance(data, dict) and data.get("reply"):
                            reply = (data.get("reply") or "").strip()
                            s = (data.get("sentiment") or "").strip().lower()
                            i_val = (data.get("intent") or "").strip().lower()
                            u = (data.get("urgency") or "").strip().lower()
                            analysis = {"sentiment": s if s in SENTIMENT_VALUES else s or None, "intent": i_val if i_val in INTENT_VALUES else None, "urgency": u if u in URGENCY_VALUES else None, "reply": reply}
                            return (reply, analysis)
                    except (json.JSONDecodeError, TypeError):
                        pass
                    break
    logger.warning("[AI] Structured JSON parse edilemedi, düz metin cevap kullanılıyor.")
    return (text, None)

# Kızgın müşteri: sadece bu durumlarda yönlendir (fazla tetikleme olmasın)
YONLENDIRME_KELIMELERI = [
    "yetkili", "müdür", "şikayet edeceğim", "tüketici hakları", "avukat", "savcılık",
    "çok kızdım", "rezalet", "berbat", "işe yaramaz", "talanız", "kandırdınız",
    "yetkiliniz", "patron", "savcı", "tüketici derneği"
]
HANDOVER_MESAJI = "Bu konuda size yardımcı olmak için yetkilimize yönlendiriyorum. En kısa sürede dönüş yapılacaktır."


class TubaAIAssistant:
    """
    Tuba Butik AI Asistanı
    Ücretsiz ve Ücretli modları destekler
    """
    
    def __init__(self, butik_client=None):
        self._claude_api_key = None
        self.pinecone = None
        self.butik_client = butik_client
        try:
            from modules.pinecone_manager import PineconeManager
            self.pinecone = PineconeManager()
        except Exception as e:
            logger.warning(f"Pinecone atlandi (opsiyonel): {e}")
        self.kurallar = TubaButikKurallari()
        
        # TEST MODU: Manuel sipariş verisi
        self.test_orders = self._load_test_orders()
        # Sistem promptu: önce dosyadan oku, yoksa varsayılan
        self.sistem_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self, tenant_id=None):
        """tenant_id verilirse once prompts/{tenant_id}_system.txt dene; yoksa tuba, sonra varsayilan."""
        paths = []
        if tenant_id:
            paths.append(f"prompts/{tenant_id}_system.txt")
            paths.append(f"{tenant_id}_system.txt")
        paths.extend(('prompts/tuba_system.txt', 'tuba_system.txt'))
        for path in paths:
            try:
                if os.path.isfile(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            logger.info(f"✅ Sistem prompt yüklendi: {path}")
                            return content
            except Exception as e:
                logger.warning(f"Prompt dosyası okunamadı ({path}): {e}")
        logger.warning("prompts/tuba_system.txt bulunamadı; varsayılan prompt kullanılıyor.")
        return """Sen Tuba Butik'in satış asistanısın. Samimi ve profesyonel ol. İade 14 gün, değişim max 2. Gereksiz yere yetkiliye yönlendirme; sadece gerçekten kızgınlık/küfür/yetkili talebi varsa yönlendir."""

    def _load_test_orders(self):
        """Test siparişlerini yükle"""
        try:
            with open('test_orders.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('test_orders', [])
        except Exception as e:
            logger.warning(f"Test siparişleri yüklenemedi: {e}")
            return []

    def musteri_kizgin_mi(self, mesaj):
        """
        Müşteri mesajında açık kızgınlık/küfür/yetkili talebi var mı?
        Sadece gerçekten net durumlarda True döner; fazla yönlendirme yapılmasın.
        """
        if not (mesaj and isinstance(mesaj, str)):
            return False
        t = self._turkce_arama_metni(mesaj)
        # Küfür / sansürlü ifade
        if "***" in mesaj or (len(mesaj) >= 3 and mesaj.count("*") >= 2):
            return True
        # Mesajın büyük kısmı büyük harf (bağırma)
        harf_say = sum(1 for c in mesaj if c.isalpha())
        buyuk_say = sum(1 for c in mesaj if c.isupper())
        if harf_say >= 10 and buyuk_say >= harf_say * 0.7:
            return True
        # Açık kızgınlık / yetkili talebi kelimeleri
        if any(k in t for k in YONLENDIRME_KELIMELERI):
            return True
        return False

    def detect_sales_intent(self, mesaj):
        """
        Satış hunisi için müşteri niyetini analiz et.
        Dönen değer: None (değiştirme), 'interested', 'negotiation', 'won'.
        Webhook'ta bu değer customers.status güncellemesi için kullanılır.
        """
        if not (mesaj and isinstance(mesaj, str)):
            return None
        t = self._turkce_arama_metni(mesaj)
        # Satış kapandı: sipariş verdi / ödedi
        won_kelimeler = ["sipariş verdim", "siparis verdim", "ödeme yaptım", "odeme yaptim", "havale yaptım", "havale yaptim", "geçti ödeme", "gecti odeme", "siparişi verdim", "siparisi verdim", "aldım", "alındı", "alindi"]
        if any(k in t for k in won_kelimeler):
            return "won"
        # Sıcak temas: ödeme / pazarlık
        negotiation_kelimeler = ["iban", "ödeme", "odeme", "indirim", "indirim yap", "alıyorum", "aliyorum", "alacağım", "alacagim", "karar verdim", "kaç lira", "kac lira", "taksit", "havale", "eft", "kapıda ödeme", "kapida odeme"]
        if any(k in t for k in negotiation_kelimeler):
            return "negotiation"
        # İlgileniyor: fiyat, ürün, beden, kumaş
        interested_kelimeler = ["fiyat", "ne kadar", "beden", "kumaş", "kumas", "renk", "stok", "var mı", "varmı", "var mi", "tavsiye", "öneri", "oneri", "ürün", "urun", "model", "gösterebilir", "gorebilir"]
        if any(k in t for k in interested_kelimeler):
            return "interested"
        return None
    
    def get_orders_by_phone(self, phone):
        """Telefon numarasına göre test siparişlerini bul (test_orders.json)"""
        clean_phone = ''.join(filter(str.isdigit, str(phone)))
        matching = []
        for order in self.test_orders:
            order_phone = ''.join(filter(str.isdigit, str(order.get('orderPhone', ''))))
            if clean_phone in order_phone or order_phone in clean_phone:
                matching.append(order)
        return matching

    def _get_orders_by_phone(self, phone):
        """Önce Butik Sistemden dene, yoksa test siparişlerinden al"""
        if self.butik_client and getattr(self.butik_client, 'username', None):
            try:
                result = self.butik_client.check_order_by_phone(phone, days=30)
                if result.get("found") and result.get("orders"):
                    return result["orders"]
            except Exception as e:
                logger.warning(f"Butik sipariş sorgusu atlandi: {e}")
        return self.get_orders_by_phone(phone)

    def _turkce_arama_metni(self, mesaj):
        """Türkçe İ/ı farkını kaldırıp arama için normalize metin (İade = iade)."""
        s = (mesaj or "").lower()
        s = s.replace("\u0131", "i")
        s = s.replace("\u0069\u0307", "i")
        s = s.replace("\u0130", "i")
        return s

    def _iade_degisim_ilk_cevap(self, mesaj, musteri_telefon):
        """İade/değişim: sipariş kodu sor; numaradan sipariş varsa listele. Farklı renk/beden, aynı ürün değişim niyeti de dahil."""
        t = self._turkce_arama_metni(mesaj)
        degisim_anahtar = [
            "iade", "değişim", "degisim", "farklı renk", "farkli renk", "farklı beden", "farkli beden",
            "renk değişimi", "renk degisimi", "beden değişimi", "beden degisimi", "değiştirmek istiyorum",
        ]
        if not any(k in t for k in degisim_anahtar):
            if "aynı ürün" in t or "ayni urun" in t:
                if "farklı" in t or "farkli" in t or "istiyorum" in t or "değiş" in t:
                    pass
                else:
                    return None
            else:
                return None
        orders = []
        if musteri_telefon:
            orders = self._get_orders_by_phone(musteri_telefon)
        if orders:
            lines = []
            for i, o in enumerate(orders[:5], 1):
                oid = o.get("orderId") or o.get("id") or o.get("siparisNo") or "?"
                urunler = o.get("products") or o.get("items") or []
                urun = urunler[0] if urunler else {}
                urun_ad = urun.get("name") or urun.get("productName") or "Ürün"
                tarih = o.get("orderDate") or o.get("date") or ""
                lines.append(f"• {oid} – {urun_ad} ({tarih})")
            liste = "\n".join(lines)
            return f"📦 Tabii. Sipariş kodunuzu biliyor musunuz? Numaranızdan baktım, siparişleriniz:\n{liste}\n\nHangisini değiştirmek/iade etmek istiyorsunuz?"
        return "📦 Tabii. Sipariş kodunuzu öğrenebilir miyim? Bilmiyorsanız numaranızdan siparişlerinize bakabilirim."
    
    @property
    def claude_api_key(self):
        """Lazy loading - API key'i ilk kullanımda oku"""
        if self._claude_api_key is None:
            self._claude_api_key = os.getenv("ANTHROPIC_API_KEY")
            if self._claude_api_key:
                logger.info(f"✅ Claude API key loaded (length: {len(self._claude_api_key)})")
            else:
                logger.error("❌ ANTHROPIC_API_KEY not found!")
        return self._claude_api_key
    
    def basit_mi_karmaşik_mi(self, mesaj):
        basit_kelimeler = ['merhaba', 'merhava', 'merha', 'selam', 'günaydın', 'iyi günler', 'fiyat', 'ne kadar', 'stokta var mı']
        karmaşık_kelimeler = [
            'iade', 'değişim', 'degisim', 'şikayet', 'sorun', 'kusur', 'yardım', 'öneri', 'tavsiye', 'hangi', 'uygun', 'siparişim', 'kargo',
            'farklı renk', 'farkli renk', 'farklı beden', 'farkli beden', 'aynı ürün', 'ayni urun', 'renk değişimi', 'renk degisimi', 'beden değişimi', 'beden degisimi',
        ]
        t = self._turkce_arama_metni(mesaj)
        if any(k in t for k in basit_kelimeler):
            if not any(k in t for k in karmaşık_kelimeler):
                return "basit"
        if any(k in t for k in karmaşık_kelimeler):
            return "karmaşık"
        return "basit"
    
    # Üç kaynak (temel kurallar, panel talimatları, analiz özeti) çakışmasın diye model'e verilen öncelik metni
    _PROMPT_HIERARCHY = (
        "PROMPT ÖNCELİĞİ (çakışmada buna uy): "
        "(1) Aşağıdaki temel kurallar ve mağaza bilgisi her zaman geçerli; ihlal etme. "
        "(2) Mağaza ek talimatları bunları tamamlar; çakışırsa temel kural öncelikli. "
        "(3) Son analiz özeti sadece bilgi/bağlam; müşteri eğilimlerine uyum sağla ama kuralları gevşetme.\n\n"
    )

    def mesaj_olustur(self, musteri_mesaji, musteri_telefon=None, gecmis_konusma=None, siparis_bilgisi=None, tenant_id=None, tenant_extra_instruction=None, line=None, analysis_summary_for_prompt=None):
        """tenant_id ile base prompt; line=sales|exchange ile satış/değişim hattı davranışı; tenant_extra_instruction panelden; analysis_summary_for_prompt Dinle+Analiz özeti (sadece bu hat). Döner: (cevap_metni, analysis_dict|None)."""
        system_prompt_override = self._load_system_prompt(tenant_id) if tenant_id else None
        if system_prompt_override:
            if line == "exchange":
                system_prompt_override = "ÖNEMLİ: Şu an DEĞİŞİM/İADE HATTındasın. Yanıtların iade, değişim, sipariş takibi ve kargo odaklı olsun; satış teklifi yapma.\n\n" + system_prompt_override
            elif line == "sales":
                system_prompt_override = "ÖNEMLİ: Şu an SATIŞ HATTındasın. Yanıtların satış, sipariş, ürün ve fiyat odaklı olsun.\n\n" + system_prompt_override
        has_extra = bool((tenant_extra_instruction or "").strip())
        has_analysis = bool((analysis_summary_for_prompt or "").strip())
        if system_prompt_override and (has_extra or has_analysis):
            system_prompt_override = self._PROMPT_HIERARCHY + system_prompt_override
        if system_prompt_override and tenant_extra_instruction:
            extra = (tenant_extra_instruction or "").strip()
            if extra:
                system_prompt_override = system_prompt_override + "\n\n--- Mağaza ek talimatları (panelden) ---\n" + extra
        if system_prompt_override and analysis_summary_for_prompt:
            summary = (analysis_summary_for_prompt or "").strip()
            if summary:
                system_prompt_override = system_prompt_override + "\n\n--- Son analiz özeti (Dinle+Analiz, bu hat) ---\n" + summary
        tur = self.basit_mi_karmaşik_mi(musteri_mesaji)
        logger.info(f"[AI] mesaj türü={tur} | tenant={tenant_id or 'default'} | line={line} | metin={musteri_mesaji[:60]}...")
        if tur == "basit":
            cevap = self.basit_cevap(musteri_mesaji, system_prompt_override=system_prompt_override)
            logger.info("[AI] Cevap: basit (sabit) veya karmaşık'a gonderildi")
            return (cevap, None)
        return self.karmaşık_cevap(musteri_mesaji, musteri_telefon, gecmis_konusma, siparis_bilgisi, system_prompt_override=system_prompt_override)
    
    def basit_cevap(self, mesaj, system_prompt_override=None):
        t = self._turkce_arama_metni(mesaj)
        # Karşılama: merhaba, merhava, merha, selam, günaydın vb.
        if any(k in t for k in ['merhaba', 'merhava', 'merha', 'selam', 'günaydın', 'gunaydin', 'iyi gün', 'iyi gun']):
            return "👋 Merhaba, Tuba Muttioğlu'na hoş geldiniz. Size nasıl yardımcı olabilirim?"
        
        elif any(k in t for k in ['teşekkür', 'sağol', 'teşekkürler', 'tesekkur']):
            return "🙏 Rica ederiz! Başka bir konuda yardımcı olabilir miyim?"
        
        elif any(k in t for k in ['görüşürüz', 'bye', 'hoşçakal']):
            return "👋 Görüşmek üzere! İyi günler dileriz."
        
        elif 'fiyat' in t or 'ne kadar' in t:
            return "💰 Fiyat bilgisi için ürün adı veya kodu paylaşabilir misiniz?"
        
        elif 'stok' in t:
            return "📦 Stok durumunu kontrol etmek için ürün bilgisi verebilir misiniz?"
        
        else:
            return self.karmaşık_cevap(mesaj, system_prompt_override=system_prompt_override)

    def karmaşık_cevap(self, mesaj, musteri_telefon=None, gecmis_konusma=None, siparis_bilgisi=None, system_prompt_override=None):
        # İade/değişim: sipariş kodu sor, numaradan sipariş varsa listele (Butik veya test)
        iade_cevap = self._iade_degisim_ilk_cevap(mesaj, musteri_telefon)
        if iade_cevap:
            logger.info("[AI] Cevap: iade/değişim sabit (Claude cagrilmadi)")
            return (iade_cevap, {"intent": "return_request", "sentiment": None, "urgency": None})

        api_key = self.claude_api_key
        if not api_key or api_key == "sk-ant-test":
            logger.warning("[AI] ANTHROPIC_API_KEY yok veya 'sk-ant-test' - Claude CAGILMIYOR.")
            return ("🤔 Bu konuda size yardımcı olmak için yetkilimize yönlendiriyorum.", None)

        if musteri_telefon:
            orders = self._get_orders_by_phone(musteri_telefon)
            if orders:
                siparis_bilgisi = self._format_orders(orders)

        system_prompt = system_prompt_override if system_prompt_override else self.sistem_prompt
        try:
            client = anthropic.Anthropic(api_key=api_key, timeout=25.0)
            urunler_metni = self._satis_urun_context(mesaj)
            context = self._context_olustur(gecmis_konusma, siparis_bilgisi, urunler_metni)
            use_haiku = os.getenv("AI_USE_HAIKU_FOR_SIMPLE", "").strip().lower() in ("1", "true", "yes")
            is_simple = len((mesaj or "").strip()) < 100 and not self.musteri_kizgin_mi(mesaj)
            if use_haiku and is_simple:
                model = os.getenv("AI_HAIKU_MODEL", "claude-haiku-4-5")
                logger.info("[AI] Claude Haiku (basit mesaj) cagriliyor...")
            else:
                model = getattr(config, "AI_MODEL", None) or os.getenv("AI_MODEL", "claude-sonnet-4-5")
                logger.info("[AI] Claude Sonnet cagriliyor (duygusal zeka + cevap).")
            user_content = f"{STRUCTURED_OUTPUT_INSTRUCTION}\n\nCONTEXT:\n{context}\n\nMÜŞTERİ MESAJI:\n{mesaj}"
            response = client.messages.create(
                model=model,
                max_tokens=512,
                temperature=0.5,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}]
            )
            raw = response.content[0].text
            reply, analysis = _parse_structured_response(raw)
            if analysis:
                logger.info("[AI] Cevap: Claude'dan geldi (sentiment=%s intent=%s).", analysis.get("sentiment"), analysis.get("intent"))
            else:
                logger.info("[AI] Cevap: Claude'dan geldi (JSON parse fallback, düz metin).")
            return (reply, analysis)
        except Exception as e:
            logger.exception(f"[AI] Claude API HATASI: {type(e).__name__}: {e}")
            return ("🤔 Bu konuda size yardımcı olmak için yetkilimize yönlendiriyorum. En kısa sürede dönüş yapılacaktır.", None)
    
    def _format_orders(self, orders):
        """Siparişleri formatla (en fazla 5 - maliyet için). Butik API bazen farkli alan adlari doner; guvenli erisim."""
        text = "Müşteri Siparişleri:\n"
        for i, order in enumerate(orders[:5], 1):
            oid = order.get("orderId") or order.get("id") or order.get("siparisNo") or "?"
            tarih = order.get("orderDate") or order.get("date") or ""
            urunler = order.get("products") or order.get("items") or []
            urun = urunler[0] if urunler else {}
            urun_ad = urun.get("name") or urun.get("productName") or "Ürün"
            beden = urun.get("size") or urun.get("beden") or ""
            tutar = order.get("total") or order.get("tutar") or "?"
            durum = order.get("status") or order.get("durum") or ""
            text += f"{i}. Sipariş No: {oid}\n"
            text += f"   Tarih: {tarih}\n"
            text += f"   Ürün: {urun_ad}" + (f" ({beden})" if beden else "") + "\n"
            text += f"   Tutar: {tutar} TL\n"
            text += f"   Durum: {durum}\n\n"
        return text
    
    def _context_olustur(self, gecmis, siparis, urunler_metni=None):
        context = ""
        if gecmis:
            context += f"Önceki Konuşma:\n{gecmis}\n\n"
        if siparis:
            context += siparis
        if urunler_metni:
            context += urunler_metni
        return context

    def _satis_urun_context(self, mesaj):
        """Satış sorularında önce Pinecone, yoksa/hata varsa Butik (ürün kodu) ile CONTEXT metni döndür."""
        if not (mesaj or "").strip():
            return ""
        t = self._turkce_arama_metni(mesaj)
        satis_kelimeler = ["abiye", "model", "fiyat", "almak", "stok", "beden", "renk", "ürün", "nelervar", "neler var", "katalog", "reklam", "gördüm", "istiyorum", "leriniz", "larınız", "etek", "elbise", "ferace", "var mı", "varmı", "var mi", "tavsiye", "öneri"]
        if not any(k in t for k in satis_kelimeler):
            return ""

        # 1) Pinecone dene (Pinecone yoksa veya hata verirse Butik'e geçeceğiz)
        if self.pinecone:
            try:
                matches = self.pinecone.benzer_urunleri_bul(mesaj.strip(), top_k=5)
                stokta_olanlar = [m for m in matches if m.get("metadata", {}).get("stok", 0) > 0]
                if stokta_olanlar:
                    lines = ["Ürün listesi (müşteri sorusuyla ilgili, stokta olanlar):"]
                    for i, m in enumerate(stokta_olanlar[:5], 1):
                        meta = m.get("metadata", {})
                        satir = f"  {i}. {meta.get('isim', '?')} - {meta.get('fiyat', '?')} TL (stok: {meta.get('stok', 0)})"
                        if meta.get("product_url"):
                            satir += f" | Link: {meta['product_url']}"
                        lines.append(satir)
                    logger.info("[AI] Satış context: Pinecone'dan %s ürün eklendi.", len(stokta_olanlar[:5]))
                    return "\n".join(lines) + "\n\n"
            except Exception as e:
                logger.warning("[AI] Pinecone ürün araması atlandi (Butik deneniyor): %s", e)

        # 2) Pinecone yoksa veya sonuç yoksa: mesajda ürün kodu varsa Butik'ten canlı stok al
        if self.butik_client:
            kod_aday = re.search(r"\b(\d{3,}[-_][a-zA-Z0-9]+|\d{4,}[-_][a-zA-Z0-9]+)\b", (mesaj or "").strip())
            if not kod_aday:
                kod_aday = re.search(r"\b(\d+[-_][a-zA-Z0-9]+)\b", (mesaj or "").strip())
            if kod_aday:
                model_code = kod_aday.group(1)
                urun = self.butik_client.get_product_by_model_code(model_code)
                if urun and (urun.get("stok") or 0) >= 0:
                    satir = f"  1. {urun.get('isim', '?')} - {urun.get('fiyat', '?')} TL (stok: {urun.get('stok', 0)})"
                    if urun.get("product_url"):
                        satir += f" | Link: {urun['product_url']}"
                    logger.info("[AI] Satış context: Butik'ten canlı ürün eklendi: %s", model_code)
                    return "Ürün listesi (Butik sistemden güncel stok):\n" + satir + "\n\n"
        return ""
