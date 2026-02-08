import os
import pinecone
from sentence_transformers import SentenceTransformer
import numpy as np

class PineconeManager:
    def __init__(self):
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.environment = os.getenv("PINECONE_ENVIRONMENT", "gcp-starter")
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "tuba-products")
        
        # Embedding modeli (Türkçe destekli, hafif)
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
        # Pinecone bağlantısı
        pinecone.init(api_key=self.api_key, environment=self.environment)
        self.index = pinecone.Index(self.index_name)
    
    def metin_vektorune_cevir(self, metin):
        """Metni vektöre dönüştür"""
        return self.model.encode(metin).tolist()
    
    def urun_ekle(self, urun_id, isim, aciklama, fiyat, stok, gorsel, varyantlar):
        """Ürünü Pinecone'a ekle"""
        # Arama metni oluştur
        arama_metni = f"{isim} {aciklama} {varyantlar}"
        vektor = self.metin_vektorune_cevir(arama_metni)
        
        # Metadata ile kaydet
        self.index.upsert([
            (str(urun_id), vektor, {
                "isim": isim,
                "aciklama": aciklama,
                "fiyat": fiyat,
                "stok": stok,
                "gorsel": gorsel,
                "varyantlar": varyantlar
            })
        ])
    
    def benzer_urunleri_bul(self, sorgu, top_k=5):
        """Müşteri sorgusuna göre ürün ara"""
        sorgu_vektoru = self.metin_vektorune_cevir(sorgu)
        
        sonuclar = self.index.query(
            vector=sorgu_vektoru,
            top_k=top_k,
            include_metadata=True
        )
        
        return sonuclar['matches']
    
    def stok_kontrol(self, urun_id):
        """Ürün stok durumunu kontrol et"""
        sonuc = self.index.fetch([str(urun_id)])
        if sonuc['vectors']:
            return sonuc['vectors'][str(urun_id)]['metadata']['stok']
        return 0
