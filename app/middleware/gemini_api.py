from google import genai
from google.genai import types
from app.core.config import settings
import functools
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create reusable client
client = genai.Client(api_key=settings.VOICE_MEMO_GEMINI_API_KEY)


@functools.lru_cache(maxsize=4)
def get_gemini_model(model_name="gemini-2.5-flash", temperature=0.2):
    """
    Returns cached model configuration.
    """
    try:
        logger.info(f"Preparing Gemini config for model: {model_name}")

        config = types.GenerateContentConfig(
            temperature=temperature,
            top_p=0.95,
            top_k=40,
        )

        return {
            "client": client,
            "model_name": model_name,
            "config": config
        }

    except Exception as e:
        logger.error(f"Failed to prepare Gemini client config: {e}")
        raise