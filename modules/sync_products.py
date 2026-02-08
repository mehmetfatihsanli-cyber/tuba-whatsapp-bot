import os
import sys
import logging

# Proje kök dizinini ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.butiksistem_client import ButikSistemClient
from modules.pinecone_manager import PineconeManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Butik sisteminden ürünleri al ve Pinecone'a kaydet"""
    
    logger.info("🚀 Ürün senkronizasyonu başlıyor...")
    
    try:
        # Butik sistemden ürünleri çek
        client = ButikSistemClient()
        urunler = client.urunleri_getir()
        
        logger.info(f"📦 {len(urunler)} ürün bulundu")
        
        if not urunler:
            logger.warning("❌ Ürün bulunamadı!")
            return
        
        # Pinecone'a kaydet
        pinecone = PineconeManager()
        basarili = 0
        
        for urun in urunler:
            try:
                pinecone.urun_ekle(urun)
                basarili += 1
                logger.info(f"✅ Eklendi: {urun.get('isim', 'Bilinmeyen')}")
            except Exception as e:
                logger.error(f"❌ Hata: {urun.get('isim', 'Bilinmeyen')} - {e}")
        
        logger.info(f"🎉 Senkronizasyon tamamlandı! {basarili}/{len(urunler)} ürün eklendi")
        
    except Exception as e:
        logger.error(f"🚨 Genel hata: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
