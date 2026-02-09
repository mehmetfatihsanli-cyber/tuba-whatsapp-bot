import os
import json
import anthropic
from modules.tuba_rules import TubaButikKurallari
import config
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

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
    
    def _load_system_prompt(self):
        """Sistem promptunu prompts/tuba_system.txt dosyasından oku; yoksa varsayılan döndür."""
        for path in ('prompts/tuba_system.txt', 'tuba_system.txt'):
            try:
                if os.path.isfile(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            logger.info(f"✅ Sistem prompt yüklendi: {path}")
                            return content
            except Exception as e:
                logger.warning(f"Prompt dosyası okunamadı ({path}): {e}")
        # Varsayılan (dosya yoksa)
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
                result = self.butik_client.check_order_by_phone(phone, days=90)
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
        """İade/değişim: sipariş kodu sor; numaradan sipariş varsa listele."""
        t = self._turkce_arama_metni(mesaj)
        if "iade" not in t and "değişim" not in t and "degisim" not in t:
            return None
        orders = []
        if musteri_telefon:
            orders = self._get_orders_by_phone(musteri_telefon)
        if orders:
            lines = []
            for i, o in enumerate(orders[:5], 1):
                urun = (o.get("products") or [{}])[0]
                lines.append(f"• {o.get('orderId', '?')} – {urun.get('name', 'Ürün')} ({o.get('orderDate', '')})")
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
        karmaşık_kelimeler = ['iade', 'değişim', 'degisim', 'şikayet', 'sorun', 'kusur', 'yardım', 'öneri', 'tavsiye', 'hangi', 'uygun', 'siparişim', 'kargo']
        t = self._turkce_arama_metni(mesaj)
        if any(k in t for k in basit_kelimeler):
            if not any(k in t for k in karmaşık_kelimeler):
                return "basit"
        if any(k in t for k in karmaşık_kelimeler):
            return "karmaşık"
        return "basit"
    
    def mesaj_olustur(self, musteri_mesaji, musteri_telefon=None, gecmis_konusma=None, siparis_bilgisi=None):
        tur = self.basit_mi_karmaşik_mi(musteri_mesaji)
        logger.info(f"[AI] mesaj türü={tur} | metin={musteri_mesaji[:60]}...")
        if tur == "basit":
            return self.basit_cevap(musteri_mesaji)
        return self.karmaşık_cevap(musteri_mesaji, musteri_telefon, gecmis_konusma, siparis_bilgisi)
    
    def basit_cevap(self, mesaj):
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
            return self.karmaşık_cevap(mesaj)

    def karmaşık_cevap(self, mesaj, musteri_telefon=None, gecmis_konusma=None, siparis_bilgisi=None):
        # İade/değişim: sipariş kodu sor, numaradan sipariş varsa listele (Butik veya test)
        iade_cevap = self._iade_degisim_ilk_cevap(mesaj, musteri_telefon)
        if iade_cevap:
            logger.info("[AI] İade/değişim sabit cevap (model yok)")
            return iade_cevap

        api_key = self.claude_api_key
        if not api_key:
            logger.warning("[AI] ANTHROPIC_API_KEY yok, yönlendirme dönüyor")
            return "🤔 Bu konuda size yardımcı olmak için yetkilimize yönlendiriyorum."

        if musteri_telefon:
            orders = self._get_orders_by_phone(musteri_telefon)
            if orders:
                siparis_bilgisi = self._format_orders(orders)

        try:
            logger.info("[AI] Claude çağrılıyor...")
            client = anthropic.Anthropic(api_key=api_key, timeout=25.0)
            context = self._context_olustur(gecmis_konusma, siparis_bilgisi)
            model = getattr(config, "AI_MODEL", None) or os.getenv("AI_MODEL", "claude-3-5-sonnet-latest")
            response = client.messages.create(
                model=model,
                max_tokens=1024,
                temperature=0.7,
                system=self.sistem_prompt,
                messages=[
                    {"role": "user", "content": f"CONTEXT:\n{context}\n\nMÜŞTERİ MESAJI:\n{mesaj}"}
                ]
            )
            return response.content[0].text
        except Exception as e:
            logger.exception(f"Claude hatası: {e}")
            return "🤔 Bu konuda size yardımcı olmak için yetkilimize yönlendiriyorum. En kısa sürede dönüş yapılacaktır."
    
    def _format_orders(self, orders):
        """Siparişleri formatla"""
        text = "Müşteri Siparişleri:\n"
        for i, order in enumerate(orders, 1):
            text += f"{i}. Sipariş No: {order['orderId']}\n"
            text += f"   Tarih: {order['orderDate']}\n"
            text += f"   Ürün: {order['products'][0]['name']} ({order['products'][0]['size']})\n"
            text += f"   Tutar: {order['total']} TL\n"
            text += f"   Durum: {order['status']}\n\n"
        return text
    
    def _context_olustur(self, gecmis, siparis):
        context = ""
        if gecmis:
            context += f"Önceki Konuşma:\n{gecmis}\n\n"
        if siparis:
            context += siparis
        return context
