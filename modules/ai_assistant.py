import os
import json
import anthropic
from modules.tuba_rules import TubaButikKurallari
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TubaAIAssistant:
    """
    Tuba Butik AI Asistanı
    Ücretsiz ve Ücretli modları destekler
    """
    
    def __init__(self):
        # API key'i hemen okuma, lazy loading yap
        self._claude_api_key = None
        self.pinecone = None
        try:
            from modules.pinecone_manager import PineconeManager
            self.pinecone = PineconeManager()
        except Exception as e:
            logger.warning(f"Pinecone atlandi (opsiyonel): {e}")
        self.kurallar = TubaButikKurallari()
        
        # TEST MODU: Manuel sipariş verisi
        self.test_orders = self._load_test_orders()
        
        # Sistem promptu - Tuba Butik karakteri
        self.sistem_prompt = """Sen Tuba Butik'in AI satış asistanısın. Adın Tuba.

🎯 KARAKTERİN:
- Samimi, sıcak ve profesyonel
- Emoji kullan (👋 💝 📦 🚚 ✅)
- "Siz" diye hitap et, saygılı ol
- Net ve kısa cevaplar ver, gereksiz uzatma

📋 İADE PROSEDÜRÜ:
1. Müşteri "iade" derse: WhatsApp'tan iade formu linki ver
2. Ürünler orijinal ambalajında ve etiketli olmalı
3. Kargo ücreti müşteriye ait
4. İade onayı sonrası 3-5 iş günü içinde para iadesi
5. İade süresi: Sipariş tesliminden itibaren 14 gün

🔄 DEĞİŞİM PROSEDÜRÜ:
1. Maksimum 2 değişim hakkı var
2. Beden/renk değişimi yapılır, para iadesi yok
3. Stokta olmayan ürün için alternatif öner
4. Değişim kargo ücreti müşteriye ait

💡 ÜRÜN ÖNERİSİ:
- Sadece stokta olan ürünleri öner
- Fiyatı net söyle, kargo bedava ise belirt
- Beden tablosu varsa paylaş

⚠️ KURALLAR:
- KVKK onayı olmayan müşteriyle ürün bilgisi verme
- Karmaşık sorunlarda insan temsilciye yönlendir
- Asla sağlık/beauty garantisi verme
- Tedarik sorunlarını dürüstçe açıkla

🆘 YÖNLENDİRME:
- Şikayet/özel durum → "Size özel yardım için yetkilimize yönlendiriyorum"
- Stokta olmayan ürün → Alternatif öner veya "Gelince haber verelim mi?"
"""
    
    def _load_test_orders(self):
        """Test siparişlerini yükle"""
        try:
            with open('test_orders.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('test_orders', [])
        except Exception as e:
            logger.warning(f"Test siparişleri yüklenemedi: {e}")
            return []
    
    def get_orders_by_phone(self, phone):
        """Telefon numarasına göre test siparişlerini bul"""
        clean_phone = ''.join(filter(str.isdigit, str(phone)))
        matching = []
        for order in self.test_orders:
            order_phone = ''.join(filter(str.isdigit, str(order.get('orderPhone', ''))))
            if clean_phone in order_phone or order_phone in clean_phone:
                matching.append(order)
        return matching
    
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
        basit_kelimeler = ['merhaba', 'selam', 'günaydın', 'iyi günler', 'fiyat', 'ne kadar', 'stokta var mı']
        karmaşık_kelimeler = ['iade', 'değişim', 'şikayet', 'sorun', 'kusur', 'yardım', 'öneri', 'tavsiye', 'hangi', 'uygun', 'siparişim', 'kargo']
        
        mesaj_lower = mesaj.lower()
        
        if any(kelime in mesaj_lower for kelime in basit_kelimeler):
            if not any(kelime in mesaj_lower for kelime in karmaşık_kelimeler):
                return "basit"
        
        if any(kelime in mesaj_lower for kelime in karmaşık_kelimeler):
            return "karmaşık"
        
        return "basit"
    
    def mesaj_olustur(self, musteri_mesaji, musteri_telefon=None, gecmis_konusma=None, siparis_bilgisi=None):
        tur = self.basit_mi_karmaşik_mi(musteri_mesaji)
        
        if tur == "basit":
            return self.basit_cevap(musteri_mesaji)
        else:
            return self.karmaşık_cevap(musteri_mesaji, musteri_telefon, gecmis_konusma, siparis_bilgisi)
    
    def basit_cevap(self, mesaj):
        mesaj_lower = mesaj.lower()
        
        if any(k in mesaj_lower for k in ['merhaba', 'selam', 'günaydın']):
            return "👋 Merhaba! Tuba Butik'e hoş geldiniz. Size nasıl yardımcı olabilirim?"
        
        elif any(k in mesaj_lower for k in ['teşekkür', 'sağol', 'teşekkürler']):
            return "🙏 Rica ederiz! Başka bir konuda yardımcı olabilir miyim?"
        
        elif any(k in mesaj_lower for k in ['görüşürüz', 'bye', 'hoşçakal']):
            return "👋 Görüşmek üzere! İyi günler dileriz."
        
        elif 'fiyat' in mesaj_lower or 'ne kadar' in mesaj_lower:
            return "💰 Fiyat bilgisi için ürün adı veya kodu paylaşabilir misiniz?"
        
        elif 'stok' in mesaj_lower:
            return "📦 Stok durumunu kontrol etmek için ürün bilgisi verebilir misiniz?"
        
        else:
            return self.karmaşık_cevap(mesaj)

    def karmaşık_cevap(self, mesaj, musteri_telefon=None, gecmis_konusma=None, siparis_bilgisi=None):
        api_key = self.claude_api_key
        
        if not api_key:
            return "🤔 Bu konuda size yardımcı olmak için yetkilimize yönlendiriyorum."
        
        # TEST: Telefon numarasına göre sipariş bul
        if musteri_telefon:
            orders = self.get_orders_by_phone(musteri_telefon)
            if orders:
                siparis_bilgisi = self._format_orders(orders)
        
        try:
            client = anthropic.Anthropic(api_key=api_key)
            
            context = self._context_olustur(gecmis_konusma, siparis_bilgisi)
            
            # DÜZELTİLMİŞ MODEL ADI
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
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
            # Claude hata verirse bile iade/değişim için kısa cevap ver
            mesaj_lower = (mesaj or "").lower()
            if "iade" in mesaj_lower and "değişim" not in mesaj_lower:
                return "📦 İade için: Ürünler orijinal ambalajında ve etiketli olmalı. Sipariş tesliminden itibaren 14 gün içinde iade yapabilirsiniz. Kargo ücreti müşteriye aittir. Detaylı form için WhatsApp üzerinden ileteceğimiz linki kullanabilirsiniz. Başka sorunuz var mı?"
            if "değişim" in mesaj_lower:
                return "🔄 Değişim için: En fazla 2 değişim hakkınız var; beden/renk değişimi yapılır. Stokta olmayan ürün için alternatif önerebiliriz. Değişim kargo ücreti müşteriye aittir. Sipariş bilginizle birlikte yazarsanız yardımcı oluruz."
            return "⚠️ Teknik bir sorun oluştu. Lütfen daha sonra tekrar deneyin."
    
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
