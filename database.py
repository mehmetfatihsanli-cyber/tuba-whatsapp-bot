from supabase import create_client, Client
import config
import logging

logger = logging.getLogger(__name__)

# Test modu - Supabase bağlantısını devre dışı bırak
try:
    supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    logger.info("Supabase client created (test mode)")
except Exception as e:
    logger.warning(f"Supabase connection disabled (test mode): {e}")
    supabase = None

def get_tenant_by_phone_id(whatsapp_phone_id: str):
    """Test modu - Mock tenant döndür"""
    logger.info(f"TEST MODE: Returning mock tenant for {whatsapp_phone_id}")
    
    # Mock tenant (test için)
    return {
        'id': 'test_tenant_123',
        'name': 'test_business',
        'whatsapp_phone_id': whatsapp_phone_id,
        'modules': {
            'sales_assistant': True,
            'return_exchange': True
        },
        'system_prompt_rules': 'Sen bir test asistanısın.'
    }

def log_conversation(tenant_id: str, customer_phone: str, message_type: str, message_content: str, ai_response: str, module_used: str, processing_time_ms: int = None, error_message: str = None, image_url: str = None):
    """Test modu - Sadece log'a yaz"""
    logger.info(f"TEST MODE: Would log conversation for {customer_phone}")
    return True

def log_missed_opportunity(tenant_id: str, customer_phone: str, requested_module: str, customer_message: str):
    """Test modu - Sadece log'a yaz"""
    logger.warning(f"TEST MODE: ⚠️ MISSED OPPORTUNITY - {customer_phone} requested {requested_module}")
    return True
