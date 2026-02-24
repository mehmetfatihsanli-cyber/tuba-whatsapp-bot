# AI Studio: ürün görseli → manken/model üzerinde gösterme (Nano Banana veya alternatif API).
# Görsel(ler) + metin prompt ile "ürünü manken üzerinde göster" / "stüdyo çekimi" gibi sonuç üretir.

import os
import base64
import logging
import requests

logger = logging.getLogger(__name__)

NANO_BANANA_API_KEY = os.getenv("NANO_BANANA_API_KEY", "").strip()
NANO_BANANA_BASE_URL = os.getenv("NANO_BANANA_API_URL", "https://api.nano-banana.run").rstrip("/")


def is_configured():
    """API anahtarı tanımlı mı?"""
    return bool(NANO_BANANA_API_KEY)


def generate_product_on_model(image_b64: str, prompt: str, model: str = "nano-banana-v1"):
    """
    Tek ürün görseli + prompt ile düzenlenmiş görsel URL'si döndürür.
    Örn: prompt = "Bu giysiyi profesyonel bir manken üzerinde göster, stüdyo ışığı."
    Returns: (success: bool, image_url: str | None, error: str | None)
    """
    if not NANO_BANANA_API_KEY:
        return False, None, "API anahtarı ayarlanmadı. Lütfen NANO_BANANA_API_KEY ortam değişkenini ekleyin."
    if not image_b64 or not prompt or not prompt.strip():
        return False, None, "Görsel ve talimat (prompt) gerekli."

    url = f"{NANO_BANANA_BASE_URL}/v1/edit"
    headers = {
        "Authorization": f"Bearer {NANO_BANANA_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "image": image_b64 if isinstance(image_b64, str) else base64.b64encode(image_b64).decode("utf-8"),
        "prompt": prompt.strip(),
        "model": model,
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        if r.status_code != 200:
            err = data.get("error") or data.get("message") or r.text or f"HTTP {r.status_code}"
            logger.warning("Nano Banana API hatası: %s", err)
            return False, None, str(err)
        image_url = data.get("edited_image_url") or data.get("image_url") or data.get("url")
        if not image_url:
            return False, None, "API cevap verdi ancak görsel URL'si dönmedi."
        return True, image_url, None
    except requests.exceptions.Timeout:
        logger.warning("Nano Banana API timeout")
        return False, None, "İstek zaman aşımına uğradı. Tekrar deneyin."
    except Exception as e:
        logger.exception("Nano Banana API exception: %s", e)
        return False, None, str(e)


def generate_from_multiple_images(images_b64: list, prompt: str, model: str = "nano-banana-v1"):
    """
    Birden fazla görsel varsa ilkini ana görsel olarak kullanır (Nano Banana /v1/edit tek görsel alıyor).
    İleride /v1/batch kullanılabilir.
    """
    if not images_b64:
        return False, None, "En az bir görsel gerekli."
    first = images_b64[0]
    if isinstance(first, bytes):
        first = base64.b64encode(first).decode("utf-8")
    return generate_product_on_model(first, prompt, model)
