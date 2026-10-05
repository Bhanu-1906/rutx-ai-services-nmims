import json
import logging
from google import genai
from google.genai import types
from fastapi import HTTPException
from rapidfuzz import process, fuzz
from app.core.config import settings

logger = logging.getLogger(__name__)

# ==========================
# Gemini Client
# ==========================

client = genai.Client(api_key=settings.VOICE_MEMO_GEMINI_API_KEY)

MODEL_NAME = "gemini-2.5-flash"

GENERATION_CONFIG = types.GenerateContentConfig(
    temperature=0.1,
    top_p=0.95,
    top_k=40,
)

# ==========================
# Prompt
# ==========================

EXTRACTION_PROMPT = """
You are a precise product name extraction engine analyzing a menu card image.

EXTRACTION RULES — follow every rule strictly:

1. EXTRACT EVERY LINE ITEM as a separate product entry, exactly as it appears on the menu.
   - Every numbered or bulleted item is ONE product entry.
   - Do not skip any item, even if it looks similar to another.

2. PRESERVE EXACT TEXT — copy the product name character-for-character from the menu.
   - Do not correct spelling, change casing, or paraphrase.
   - Do not add or remove words.

3. DO NOT SPLIT combined items joined by "/" or "or"
   - If the menu says "still water / sparkling water" → extract it as ONE entry: "still water / sparkling water"
   - The "/" means it is ONE menu line item offered together. Keep it as one string.

4. DO NOT MERGE or SKIP separate items
   - If "minute maid", "minute maid orange", and "minute maid apple" are three separate numbered lines, extract all three as separate entries.
   - Never skip the base/generic version just because variants exist.
   - Each numbered line = one entry, no exceptions.

5. IGNORE section headers (e.g., "Soft Drinks", "Premium Drinks", "Snacks", "Starters", "Beverages")
6. IGNORE prices, quantities, sizes, descriptions, and item serial numbers (01., 02., etc.)

Return ONLY a valid JSON array of product name strings. No explanation, no markdown, no extra text.

Example:
["coca-cola", "coca-cola zero sugar", "sprite", "minute maid", "minute maid orange"]
"""

# ==========================
# Extraction
# ==========================

def extract_products_from_image(image_bytes: bytes, content_type: str) -> list[str]:
    """
    Extract product names from menu image using Gemini.
    """

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                EXTRACTION_PROMPT,
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=content_type
                )
            ],
            config=GENERATION_CONFIG
        )

        raw = response.text.strip()

        # Cleanup if Gemini wraps JSON in markdown
        raw = raw.replace("```json", "").replace("```", "").strip()

        products = json.loads(raw)

        if not isinstance(products, list):
            raise ValueError("Gemini response was not a JSON list.")

        return [str(p) for p in products]

    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to parse Gemini response: {exc}"
        ) from exc

    except Exception as exc:
        logger.exception("Gemini extraction failed")
        raise HTTPException(
            status_code=500,
            detail=f"Gemini API error: {str(exc)}"
        ) from exc


# ==========================
# Deduplication
# ==========================

def deduplicate_products(products: list[str]) -> list[str]:
    """
    Remove duplicate product names (case-insensitive).
    Keep first occurrence.
    """
    seen = set()
    unique = []

    for product in products:
        key = product.lower().strip()

        if key not in seen:
            seen.add(key)
            unique.append(product)

    return unique


# ==========================
# Classification
# ==========================

def _fuzzy_match(name: str):
    """
    Match extracted product against owned product DB.
    """
    result = process.extractOne(
        name.lower().strip(),
        settings.OUR_PRODUCTS,
        scorer=fuzz.WRatio,
        score_cutoff=settings.OWNERSHIP_MATCH_THRESHOLD,
    )

    if result:
        matched_name, score, _ = result
        return matched_name, score

    return None


def classify_product(product_name: str) -> dict:
    """
    Classify product as our brand or competitor.
    """

    # Try full product name
    match = _fuzzy_match(product_name)

    if match:
        return {
            "product": product_name,
            "ownership": "our",
            "matched_db_entry": match[0],
            "confidence": round(match[1], 2),
        }

    # Handle combined products
    if "/" in product_name:
        parts = [part.strip() for part in product_name.split("/")]

        for part in parts:
            part_match = _fuzzy_match(part)

            if part_match:
                return {
                    "product": product_name,
                    "ownership": "our",
                    "matched_db_entry": part_match[0],
                    "confidence": round(part_match[1], 2),
                    "note": f"Matched via split part: '{part}'",
                }

    return {
        "product": product_name,
        "ownership": "competitor",
        "matched_db_entry": None,
        "confidence": None,
    }


# ==========================
# Report Generation
# ==========================

def generate_report(classified_products: list[dict]) -> dict:
    """
    Generate final summary report.
    """

    our_products = [
        product
        for product in classified_products
        if product["ownership"] == "our"
    ]

    competitor_products = [
        product
        for product in classified_products
        if product["ownership"] == "competitor"
    ]

    total = len(classified_products)
    our_count = len(our_products)
    competitor_count = len(competitor_products)

    our_share = round((our_count / total) * 100, 2) if total else 0.0
    competitor_share = round((competitor_count / total) * 100, 2) if total else 0.0

    return {
        "summary": {
            "total_products_detected": total,
            "our_products_count": our_count,
            "competitor_products_count": competitor_count,
            "our_share_percent": our_share,
            "competitor_share_percent": competitor_share,
        },
        "our_products": [
            {
                "product": p["product"],
                "matched_as": p["matched_db_entry"],
                "confidence": p["confidence"],
                **({"note": p["note"]} if p.get("note") else {}),
            }
            for p in our_products
        ],
        "competitor_products": [
            {"product": p["product"]}
            for p in competitor_products
        ],
    }


# ==========================
# Main Pipeline
# ==========================

def analyze_menu_image(image_bytes: bytes, content_type: str) -> dict:
    """
    Full image analysis pipeline.
    """

    extracted_products = extract_products_from_image(
        image_bytes=image_bytes,
        content_type=content_type
    )

    if not extracted_products:
        raise HTTPException(
            status_code=422,
            detail="No products could be extracted from the image."
        )

    unique_products = deduplicate_products(extracted_products)

    classified_products = [
        classify_product(product)
        for product in unique_products
    ]

    return generate_report(classified_products)