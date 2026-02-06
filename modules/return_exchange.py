import logging
from claude_client import get_text_response, analyze_image

logger = logging.getLogger(__name__)

def handle_return_exchange_text(tenant, customer_message):
    logger.info(f"Return/exchange (text) for tenant {tenant['name']}")
    
    system_prompt = tenant.get('system_prompt_rules', 'Sen bir müşteri hizmetleri asistanısın.')
    
    user_prompt = f"""
Müşteri ürün değişimi veya iadesi hakkında konuşuyor.

Müşteri mesajı: {customer_message}

Lütfen:
- Nazikçe bilgi al
- Sorun ne olduğunu anla
- Çözüm önerileri sun
- Gerekirse ürün görseli iste

Müşteriyi memnun et.
"""
    
    response = get_text_response(system_prompt, user_prompt)
    return response

def handle_defective_product_image(tenant, image_data, customer_message=""):
    logger.info(f"Defective product image analysis for tenant {tenant['name']}")
    
    prompt = f"""
Bu ürün görselini analiz et.

Müşteri yorumu: {customer_message if customer_message else "Yok"}

Lütfen değerlendir:
1. Görselde kusur var mı? (yırtık, leke, deformasyon, vs.)
2. Kusur varsa ne tür bir kusur?
3. Kusurun ciddiyeti nedir?

Yanıtını şu formatta ver:
- KUSUR DURUMU: [Var/Yok]
- KUSUR TÜRÜ: [Açıklama]
- ÖNERİ: [Değişim/İade/Onarım]

Detaylı ve profesyonel ol.
"""
    
    analysis = analyze_image(image_data, prompt)
    
    if "KUSUR DURUMU: Var" in analysis or "kusur" in analysis.lower():
        response = f"""
Görselinizi inceledik. 

{analysis}

Size en kısa sürede alternatif çözümler sunacağız. Uzman ekibimiz en geç 24 saat içinde sizinle iletişime geçecektir.

Anlayışınız için teşekkür ederiz! 🙏
"""
    else:
        response = f"""
Görselinizi inceledik.

{analysis}

Size yardımcı olmak için buradayız! Başka sorunuz var mı?
"""
    
    return response
