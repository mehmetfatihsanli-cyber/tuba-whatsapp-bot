# Virtual Try-On: Replicate IDM-VTON ile kıyafeti manken/model üzerinde gösterir.

import os
import logging

try:
    import replicate
except ImportError:
    replicate = None  # replicate yüklü değilse panel ve diğer sayfalar yine çalışır

logger = logging.getLogger(__name__)

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "").strip()
# Varsayılan manken: env veya panel yüklemesi yoksa bu sabit URL kullanılır (nötr moda fotoğrafı).
DEFAULT_HUMAN_IMG = os.getenv("VIRTUAL_STUDIO_DEFAULT_MODEL_IMAGE", "").strip()
DEFAULT_MODEL_URL = (
    "https://images.unsplash.com/photo-1539109136881-3be0616acf4b?q=80&w=1887&auto=format&fit=crop"
)
MODEL_VERSION = "cuuupid/idm-vton:906425dbca90663ff5427624839572cc56ea7d380343d13e2a4c4b09d3f0c30f"

# Panel kategorileri -> Replicate category enum (Replicate sadece 3 tip destekler)
CATEGORY_MAP = {
    "elbise": "dresses",
    "ust": "upper_body",
    "alt": "lower_body",
    "upper_body": "upper_body",
    "lower_body": "lower_body",
    "dresses": "dresses",
    "bluz": "upper_body",
    "gomlek": "upper_body",
    "ceket": "upper_body",
    "pantolon": "lower_body",
    "etek": "lower_body",
}


def is_configured():
    return bool(replicate and REPLICATE_API_TOKEN)


def process_tryon(garment_url: str, category: str, garment_instruction: str = "", human_img: str = None):
    """
    Kıyafet görselini varsayılan manken üzerinde dener (Virtual Try-On).
    Args:
        garment_url: Kıyafet görseli URL'si (public erişilebilir).
        category: "elbise" | "ust" | "alt" (veya upper_body, lower_body, dresses).
        garment_instruction: İsteğe bağlı tarif (örn. "stüdyo ışığı, beyaz arka plan").
        human_img: Manken/model görseli URL'si. Verilmezse önce env/panel, yoksa DEFAULT_MODEL_URL kullanılır.
    Returns:
        (success: bool, output_url: str | None, error: str | None)
    """
    if not replicate:
        return False, None, "replicate modülü yüklü değil (pip install replicate)."
    if not REPLICATE_API_TOKEN:
        return False, None, "REPLICATE_API_TOKEN ortam değişkeni ayarlanmamış."
    # Öncelik: frontend/panel'den gelen human_img -> env/panel varsayılanı -> sabit DEFAULT_MODEL_URL
    human_url = (human_img or "").strip() or DEFAULT_HUMAN_IMG or DEFAULT_MODEL_URL
    if not garment_url or not garment_url.strip():
        return False, None, "Kıyafet görseli URL'si gerekli."

    cat = (category or "").strip().lower().replace(" ", "_")
    replicate_category = CATEGORY_MAP.get(cat) or CATEGORY_MAP.get("ust") or "upper_body"
    garment_des = f"A photo of a {replicate_category.replace('_', ' ')}"
    if (garment_instruction or "").strip():
        garment_des = garment_des + ". " + (garment_instruction or "").strip()

    try:
        output = replicate.run(
            MODEL_VERSION,
            input={
                "garm_img": garment_url.strip(),
                "human_img": human_url.strip(),
                "garment_des": garment_des,
                "category": replicate_category,
                "crop": False,
                "seed": 42,
            },
        )
        # Replicate: tek FileOutput, URL string veya liste olabilir. Önce .url ve string kontrolü.
        output_url = None
        if isinstance(output, str) and output.strip().startswith("http"):
            output_url = output.strip()
        elif hasattr(output, "url"):
            output_url = getattr(output, "url", None)
            if output_url and not isinstance(output_url, str):
                output_url = str(output_url) if output_url else None
        if not output_url and hasattr(output, "__iter__") and not isinstance(output, str):
            try:
                out_list = list(output)
                first = out_list[0] if out_list else None
                if first is not None:
                    if hasattr(first, "url"):
                        output_url = getattr(first, "url", None)
                    else:
                        output_url = str(first).strip() if str(first).strip().startswith("http") else None
            except Exception:
                pass
        if not output_url and output is not None:
            output_url = str(output).strip() if str(output).strip().startswith("http") else None
        if not output_url or not str(output_url).strip().startswith("http"):
            logger.warning("IDM-VTON output format unexpected: type=%s", type(output).__name__)
            return False, None, "Model çıktı üretmedi."
        output_url = str(output_url).strip()
        return True, output_url, None
    except Exception as e:
        if replicate and hasattr(replicate, "exceptions") and isinstance(e, replicate.exceptions.ReplicateError):
            logger.warning("Replicate IDM-VTON hatası: %s", e)
        logger.exception("Virtual try-on hatası: %s", e)
        return False, None, str(e)
