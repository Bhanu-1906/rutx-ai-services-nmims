from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi import Form
import os
from typing import Optional
from PIL import Image
import io
import logging
import gc
from app.services.planogram_service_2 import PlanogramAnalyzer

router = APIRouter(tags=["Planogram"])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Model paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "onnx_models")
YOLO_PATH = os.path.join(MODELS_DIR, "Detect50.onnx")
RESNET_PATH = os.path.join(MODELS_DIR, "JuiceBottles.onnx")

# Singleton PlanogramAnalyzer instance
planogram_analyzer = None
import asyncio
analyzer_lock = asyncio.Lock()

async def get_planogram_analyzer():
    global planogram_analyzer
    async with analyzer_lock:
        if planogram_analyzer is None:
            if not os.path.exists(YOLO_PATH) or not os.path.exists(RESNET_PATH):
                raise HTTPException(
                    status_code=500,
                    detail="Model files not found"
                )
            planogram_analyzer = PlanogramAnalyzer(
                # yolo_model_path=YOLO_PATH,
                resnet_model_path=RESNET_PATH
            )
            await planogram_analyzer.initialize()
    return planogram_analyzer

@router.post("/planogram")
async def get_planogram(org_id: str = Form(...), image: UploadFile = File(...)):
    if org_id != "test":
        return JSONResponse(
            status_code=400,
            content={"detail": "Invalid organization ID"}
        )
    try:
        # Validate image
        if not image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="File must be an image"
            )
        try:
            planogram_analyzer = PlanogramAnalyzer(
                # yolo_model_path=YOLO_PATH,
                resnet_model_path=RESNET_PATH
            )
            # analyzer = await get_planogram_analyzer()
            await planogram_analyzer.initialize()
            analyzer = planogram_analyzer
            logger.info("ML")
            # Read the image content
            content = await image.read()
            # Convert to PIL Image
            pil_image = Image.open(io.BytesIO(content))
            # Process the image
            result = await analyzer.results(pil_image)
            # Force cleanup to free memory
            del pil_image
            del content
            return JSONResponse(
                status_code=200,
                content={
                    "data":{
                        "result": result
                    }
                }
            )
        except HTTPException as http_ex:
            raise http_ex
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing file: {str(e)}"
            )
        finally:
            gc.collect()
    except Exception as e:
        logger.error(f"Error in planogram API: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )