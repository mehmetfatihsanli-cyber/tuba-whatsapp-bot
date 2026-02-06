import logging
from claude_client import get_text_response

logger = logging.getLogger(__name__)

def handle_sales_inquiry(tenant, customer_message):
    logger.info(f"Sales assistant activated for tenant {tenant['name']}")
    
    system_prompt = tenant.get('system_prompt_rules', 'Sen bir müşteri hizmetleri asistanısın.')
    
    user_prompt = f"""
Müşteri ürün hakkında soru soruyor.

Müşteri mesajı: {customer_message}

Lütfen yardımcı ol:
- Ürün özellikleri
- Beden bilgileri
- Renk seçenekleri
- Stok durumu
- Fiyat bilgisi

Nazik ve profesyonel ol.
"""
    
    response = get_text_response(system_prompt, user_prompt)
    return response
