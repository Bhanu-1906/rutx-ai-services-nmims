import json
import logging
import asyncio
import time
from functools import lru_cache
from typing import Dict, Any

from fastapi import UploadFile
from google import genai
from google.genai import types

from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# ==========================
# Gemini Client
# ==========================

client = genai.Client(api_key=settings.VOICE_MEMO_GEMINI_API_KEY)

MODEL_NAME = "gemini-2.5-flash"
MODEL_TIMEOUT = 30.0
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB

GENERATION_CONFIG = types.GenerateContentConfig(
    temperature=0.1,
    top_p=0.95,
    top_k=40,
)

# ==========================
# Prompt Cache
# ==========================

@lru_cache(maxsize=1)
def get_invoice_prompt():
    return """Extract all invoice details and return STRICTLY ONLY raw JSON in this EXACT format:
{
  "invoice_number": "string (extract exact invoice number)",
  "billed_to": "string (retailer/company name - extract most prominent business name)",
  "pay_to": {
    "name": "string (account holder name exactly as shown, null if absent)",
    "address": "string (complete address if present, null otherwise)",
    "phone": "string (exact phone number if present, null otherwise)"
  },
  "bank_details": {
    "bank_name": "string (full bank name)",
    "bank_account_name": "string (account holder name as in bank details)",
    "bank_account_number": "string (full account number)"
  },
  "line_items": [
    {
      "description": "string (exact product/service name)",
      "unit_price": number,
      "quantity": number,
      "line_total": number
    }
  ],
  "summary": {
    "subtotal": number,
    "discounts": [
      {
        "percentage": number,
        "amount": number
      }
    ],
    "tax": [
      {
        "percentage": number,
        "amount": number
      }
    ],
    "total": number
  }
}

CRITICAL INSTRUCTIONS:
1. OUTPUT MUST BE RAW JSON ONLY
2. No markdown
3. No explanation
4. No extra text
5. Return ONLY valid JSON
"""


# ==========================
# Main Processing
# ==========================

async def process_invoice(file: UploadFile) -> Dict[str, Any]:
    """
    Process invoice image and extract structured data.
    """
    start_time = time.time()
    request_id = f"inv_{int(start_time)}_{file.filename}"

    logger.info(f"[{request_id}] Processing invoice: {file.filename}")

    try:
        file_content = await read_file_safely(file)

        if isinstance(file_content, dict) and "error" in file_content:
            return file_content

        prompt = get_invoice_prompt()

        result = await process_with_model(
            image_bytes=file_content,
            mime_type=file.content_type,
            prompt=prompt,
            request_id=request_id,
            start_time=start_time,
        )

        return result

    except Exception as e:
        logger.exception(f"[{request_id}] Unhandled invoice processing error")
        return {"error": f"Failed to process invoice: {str(e)}"}


# ==========================
# Safe File Read
# ==========================

async def read_file_safely(file: UploadFile) -> bytes:
    """
    Read uploaded file safely with validation.
    """
    try:
        image_bytes = await file.read()
        file_size = len(image_bytes)

        logger.info(f"File size: {file_size} bytes")

        if file_size > MAX_FILE_SIZE:
            return {
                "error": f"File too large. Maximum size is {MAX_FILE_SIZE / (1024 * 1024)}MB."
            }

        await file.seek(0)

        return image_bytes

    except Exception as e:
        logger.exception("File read failed")
        return {"error": f"Failed to read file: {str(e)}"}


# ==========================
# Gemini Processing
# ==========================

async def process_with_model(
    image_bytes: bytes,
    mime_type: str,
    prompt: str,
    request_id: str,
    start_time: float,
) -> Dict[str, Any]:
    """
    Send invoice image to Gemini.
    """
    try:
        logger.info(f"[{request_id}] Sending request to Gemini")

        response = await asyncio.wait_for(
            asyncio.to_thread(
                client.models.generate_content,
                model=MODEL_NAME,
                contents=[
                    prompt,
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=mime_type,
                    ),
                ],
                config=GENERATION_CONFIG,
            ),
            timeout=MODEL_TIMEOUT,
        )

        raw_text = response.text.strip()

        # Remove markdown if model adds it
        raw_text = raw_text.replace("```json", "").replace("```", "").strip()

        parsed_data = json.loads(raw_text)

        validate_invoice_data(parsed_data)

        elapsed = time.time() - start_time
        logger.info(f"[{request_id}] Invoice processed in {elapsed:.2f}s")

        return parsed_data

    except asyncio.TimeoutError:
        logger.error(f"[{request_id}] Processing timed out")
        return {
            "error": f"Processing timed out after {MODEL_TIMEOUT} seconds."
        }

    except json.JSONDecodeError as e:
        logger.error(f"[{request_id}] JSON parse failed: {e}")
        return {
            "error": "Failed to parse Gemini response as valid JSON"
        }

    except ValueError as e:
        logger.error(f"[{request_id}] Validation failed: {e}")
        return {
            "error": f"Invalid invoice data: {str(e)}"
        }

    except Exception as e:
        logger.exception(f"[{request_id}] Gemini processing failed")
        return {
            "error": f"Gemini processing failed: {str(e)}"
        }


# ==========================
# Validation
# ==========================

def validate_invoice_data(data: Dict[str, Any]) -> None:
    """
    Validate extracted invoice JSON.
    """
    required_fields = [
        "invoice_number",
        "billed_to",
        "summary",
    ]

    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    if "total" not in data.get("summary", {}):
        raise ValueError("Invoice total amount is missing")