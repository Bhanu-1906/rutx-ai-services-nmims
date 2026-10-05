from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import os
import logging

router = APIRouter(tags=["Health"])

logger = logging.getLogger(__name__)

@router.get("/health")
async def health_check():
    return {"status":"ok"}


@router.get("/health/planogram")
async def check_planogram_health():
    """
    Health check endpoint for the planogram service.
    Verifies that the ONNX model files exist and are accessible.
    """
    try:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        MODELS_DIR = os.path.join(BASE_DIR, "onnx_models")
        
        yolo_path = os.path.join(MODELS_DIR, "Detect50.onnx")
        resnet_path = os.path.join(MODELS_DIR, "resnetCigarClass.onnx")
        
        # Check if model files exist
        models_exist = os.path.exists(yolo_path) and os.path.exists(resnet_path)
        
        # Check if model files are readable
        models_readable = False
        if models_exist:
            try:
                with open(yolo_path, 'rb') as f:
                    f.read(1024)  # Read first 1KB to check access
                with open(resnet_path, 'rb') as f:
                    f.read(1024)  # Read first 1KB to check access
                models_readable = True
            except IOError as e:
                logger.error(f"Model files not readable: {str(e)}")
        
        if not models_exist:
            return JSONResponse(
                status_code=503,  # Service Unavailable
                content={
                    "status": "error",
                    "message": "Model files not found"
                }
            )
        
        if not models_readable:
            return JSONResponse(
                status_code=503,  # Service Unavailable
                content={
                    "status": "error",
                    "message": "Model files not readable"
                }
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "ok",
                "message": "Planogram service is healthy"
            }
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )