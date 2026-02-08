from datetime import datetime, timedelta
import re

class TubaButikKurallari:
    """
    Tuba Hanım'ın İade/Değişim Kuralları
    """
    
    # Sabit Kurallar
    IADE_SURESI_GUN = 14
    MAX_DEGISIM_SAYISI = 2
    
    @staticmethod
    def siparis_kodu_olustur(musteri_telefon, siparis_tarihi, sira_no=1):
        """
        Akıllı sipariş kodu oluşturucu
        Format: TB-TELEFONSON4-TARIH-SIRA
        Örnek: TB-7705-07022026-1
        """
        tarih_str = siparis_tarihi.strftime("%d%m%Y")
        # Son 4 hane
        telefon_son4 = musteri_telefon[-4:] if len(musteri_telefon) >= 4 else musteri_telefon
        return f"TB-{telefon_son4}-{tarih_str}-{sira_no}"
    
    @staticmethod
    def degisim_kodu_olustur(ana_siparis_kodu, degisim_sayisi):
        """
        Değişim sipariş kodu
        Örnek: TB-7705-07022026-1-D1 (1. değişim)
        """
        return f"{ana_siparis_kodu}-D{degisim_sayisi}"
    
    @staticmethod
    def iade_hakki_kontrol(siparis_tarihi, degisim_sayisi=0, ilk_degisim_tarihi=None):
        """
        Müşterinin iade hakkını kontrol et
        """
        bugun = datetime.now()
        
        # İlk alış tarihinden itibaren 14 gün
        ana_iade_sonu = siparis_tarihi + timedelta(days=TubaButikKurallari.IADE_SURESI_GUN)
        
        # Eğer değişim yapıldıysa, değişim tarihinden yeni 14 gün
        if degisim_sayisi > 0 and ilk_degisim_tarihi:
            degisim_iade_sonu = ilk_degisim_tarihi + timedelta(days=TubaButikKurallari.IADE_SURESI_GUN)
            gecerli_son_tarih = max(ana_iade_sonu, degisim_iade_sonu)
        else:
            gecerli_son_tarih = ana_iade_sonu
        
        kalan_gun = (gecerli_son_tarih - bugun).days
        
        # İade hakkı var mı?
        iade_hakki_var = (kalan_gun > 0) and (degisim_sayisi < TubaButikKurallari.MAX_DEGISIM_SAYISI)
        
        return {
            "iade_hakki_var": iade_hakki_var,
            "kalan_gun": max(0, kalan_gun),
            "degisim_hakki_kaldi": TubaButikKurallari.MAX_DEGISIM_SAYISI - degisim_sayisi,
            "degisim_sayisi": degisim_sayisi,
            "son_tarih": gecerli_son_tarih.strftime("%d.%m.%Y"),
            "ana_iade_sonu": ana_iade_sonu.strftime("%d.%m.%Y")
        }
    
    @staticmethod
    def durum_mesaji_olustur(kontrol_sonucu):
        """Müşteriye gösterilecek mesajı oluştur"""
        if not kontrol_sonucu["iade_hakki_var"]:
            if kontrol_sonucu["degisim_sayisi"] >= TubaButikKurallari.MAX_DEGISIM_SAYISI:
                return "❌ Üzgünüm, iade/değişim hakkınız dolmuştur. Maksimum 2 değişim hakkı bulunmaktadır."
            else:
                return f"❌ İade süreniz dolmuştur. Son tarih: {kontrol_sonucu['son_tarih']}"
        
        mesaj = f"✅ İade/değişim hakkınız bulunmaktadır.\n\n"
        mesaj += f"📅 Son tarih: {kontrol_sonucu['son_tarih']}\n"
        mesaj += f"⏰ Kalan gün: {kontrol_sonucu['kalan_gun']} gün\n"
        
        if kontrol_sonucu["degisim_hakki_kaldi"] > 0:
            mesaj += f"🔄 Kalan değişim hakkı: {kontrol_sonucu['degisim_hakki_kaldi']}\n\n"
        
        mesaj += "Lütfen ürünü orijinal ambalajında, etiketleri takılı olarak gönderiniz."
        
        return mesaj
    
    @staticmethod
    def siparis_kodu_parse(siparis_kodu):
        """Sipariş kodunu parse et"""
        # Format: TB-XXXX-XXXXXXXX-X veya TB-XXXX-XXXXXXXX-X-DX
        pattern = r'TB-(\d{4})-(\d{8})-(\d+)(?:-D(\d+))?'
        match = re.match(pattern, siparis_kodu)
        
        if match:
            return {
                "telefon_son4": match.group(1),
                "tarih": match.group(2),
                "sira": int(match.group(3)),
                "degisim_no": int(match.group(4)) if match.group(4) else 0
            }
        return None
