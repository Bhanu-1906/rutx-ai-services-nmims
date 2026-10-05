from fastapi import APIRouter, File, UploadFile, HTTPException
from app.services.menu_analyze import analyze_menu_image
from app.schemas.planogram_model import MenuAnalysisResponse

router = APIRouter(prefix="/menu", tags=["Menu Analysis"])

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/gif",
    "image/bmp",
}


@router.post(
    "/analyze",
    response_model=MenuAnalysisResponse,
    summary="Analyze a menu card image",
    description=(
        "Upload a menu card image (JPEG, PNG, WEBP, GIF, BMP). "
        "Returns total products, our vs competitor counts, share percentages, and product lists."
    ),
)
async def analyze_menu(
    file: UploadFile = File(..., description="Menu card image file"),
):
    content_type = file.content_type or ""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{content_type}'. Accepted: {sorted(ALLOWED_CONTENT_TYPES)}",
        )

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    report = analyze_menu_image(image_bytes, content_type)
    return MenuAnalysisResponse(**report)