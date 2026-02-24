import os
from dotenv import load_dotenv

load_dotenv()

# Anthropic Claude API
# Varsayilan: Claude 3.5 Sonnet (en son, akilli model). Degistirmek icin AI_MODEL env kullan.
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', 'sk-ant-test')
AI_MODEL = os.getenv('AI_MODEL', 'claude-sonnet-4-5')

# Supabase - GEÇERLİ FORMAT (geçici)
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://test.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test')

# WhatsApp Business API
META_ACCESS_TOKEN = os.getenv('META_ACCESS_TOKEN', 'test_token')
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN', 'test_verify')
WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID', 'test_phone')

# Admin
ADMIN_PHONE = os.getenv('ADMIN_PHONE', '+905551234567')
