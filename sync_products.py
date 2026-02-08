import os
import xml.etree.ElementTree as ET
import requests
from modules.pinecone_manager import PineconeManager
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class XMLProductSync:
    def __init__(self):
        self.xml_url = "https://www.tubamutioglu.com/xml.php?c=facebookproduct&xmlc=aed644a383"
        self.pinecone = PineconeManager()
    
    def xml_indir(self):
        """XML dosyasını indir"""
        try:
            logger.info("XML indiriliyor...")
            response = requests.get(self.xml_url, timeout=30)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"XML indirme hatası: {e}")
            return None
    
    def xml_parse(self, xml_content):
        """XML'i parse et ve ürün listesi oluştur"""
        try:
            root = ET.fromstring(xml_content)
            urunler = []
            
            # XML yapısına göre ürünleri bul
            for item in root.findall('.//item'):
                urun = {
                    'id': item.findtext('id', ''),
                    'isim': item.findtext('title', ''),
                    'aciklama': item.findtext('description', ''),
                    'fiyat': item.findtext('price', '0'),
                    'stok': item.findtext('quantity', '0'),
                    'gorsel': item.findtext('image_link', ''),
                    'varyantlar': item.findtext('size', '') + ' ' + item.findtext('color', '')
                }
                urunler.append(urun)
            
            logger.info(f"{len(urunler)} ürün parse edildi")
            return urunler
            
        except Exception as e:
            logger.error(f"XML parse hatası: {e}")
            return []
    
    def pinecone_aktar(self, urunler):
        """Ürünleri Pinecone'a aktar"""
        basari = 0
        hata = 0
        
        for urun in urunler:
            try:
                self.pinecone.urun_ekle(
                    urun_id=urun['id'],
                    isim=urun['isim'],
                    aciklama=urun['aciklama'],
                    fiyat=float(urun['fiyat']),
                    stok=int(urun['stok']),
                    gorsel=urun['gorsel'],
                    varyantlar=urun['varyantlar']
                )
                basari += 1
            except Exception as e:
                logger.error(f"Ürün aktarma hatası {urun['id']}: {e}")
                hata += 1
        
        logger.info(f"Aktarım tamamlandı: {basari} başarılı, {hata} hata")
        return basari, hata
    
    def senkronize_et(self):
        """Tam senkronizasyon işlemi"""
        xml_content = self.xml_indir()
        if not xml_content:
            return False
        
        urunler = self.xml_parse(xml_content)
        if not urunler:
            return False
        
        basari, hata = self.pinecone_aktar(urunler)
        
        # Supabase'e senkronizasyon logu kaydet (opsiyonel)
        logger.info(f"Senkronizasyon tamamlandı: {datetime.now()}")
        return True

if __name__ == "__main__":
    sync = XMLProductSync()
    sync.senkronize_et()
