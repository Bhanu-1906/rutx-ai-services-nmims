from fastapi import APIRouter, Depends, Query, HTTPException
from livekit import api
from app.services.livekit_server_service import LivekitServerService
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/livekit", tags=["LiveKit Token"])


@router.get("/token", response_class=JSONResponse)
async def get_livekit_token(
    user_id: str = Query(..., description="User ID for token generation"),
    salesforce_access_token: str = Query(..., description="Salesforce access token"),
    room_name: str = Query(..., description="Room name"),
    url: str = Query(..., description="Instance URL from salesforce access token")
):
    """
    Generate a LiveKit access token for the user.
    """
    try:
        livekit_service = LivekitServerService(
            user_id, salesforce_access_token, url, room=room_name,
        )
        token = livekit_service.generate_access_token()
        return {"token": token}
    except Exception as e:
        logger.error(f"Error generating LiveKit token: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate token: {str(e)}"
        )
