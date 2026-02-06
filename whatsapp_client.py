import httpx
import config
import logging

logger = logging.getLogger(__name__)

def send_message(phone_number_id: str, to: str, message: str):
    try:
        url = f"https://graph.facebook.com/v21.0/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {config.META_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "text": {"body": message}
        }
        
        with httpx.Client() as client:
            response = client.post(url, headers=headers, json=data, timeout=10.0)
            response.raise_for_status()
            logger.info(f"Message sent to {to}")
            return True
    except Exception as e:
        logger.error(f"WhatsApp send error: {e}")
        return False

def download_media(media_id: str):
    try:
        url = f"https://graph.facebook.com/v21.0/{media_id}"
        headers = {"Authorization": f"Bearer {config.META_ACCESS_TOKEN}"}
        
        with httpx.Client() as client:
            response = client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            media_url = response.json().get('url')
            
            media_response = client.get(media_url, headers=headers, timeout=30.0)
            media_response.raise_for_status()
            return media_response.content
    except Exception as e:
        logger.error(f"Media download error: {e}")
        return None
