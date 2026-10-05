from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from livekit import api
from typing import Optional
import json
import logging

from app.core.config import settings


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter(tags=["CallDispatch"])


LIVEKIT_URL = settings.LIVEKIT_URL
LIVEKIT_API_KEY = settings.LIVEKIT_API_KEY
LIVEKIT_API_SECRET = settings.LIVEKIT_API_SECRET


class MakeCallRequest(BaseModel):
    call_attempt_id: Optional[str] = None
    salesforce_record_id: str
    lead_name: str
    phone_number: str
    lead_type: str
    course_opted: str
    registration_deadline: str


@router.post("/make-call")
async def make_call(request: MakeCallRequest):
    agent_name = "salesforce-agent"

    if not all([
        LIVEKIT_URL,
        LIVEKIT_API_KEY,
        LIVEKIT_API_SECRET,
    ]):
        raise HTTPException(
            status_code=500,
            detail="LiveKit env variables are not set."
        )

    logger.info(
        "Inside make_call | salesforce_record_id=%s | "
        "lead_name=%s | phone_number=%s",
        request.salesforce_record_id,
        request.lead_name,
        request.phone_number,
    )

    lkapi = None

    try:
        lkapi = api.LiveKitAPI(
            url=LIVEKIT_URL,
            api_key=LIVEKIT_API_KEY,
            api_secret=LIVEKIT_API_SECRET,
        )

        # Use phone number as provided.
        # If country code is missing, prepend +91.
        phone_number = request.phone_number.strip()

        if not phone_number.startswith("+"):
            phone_number = f"+91{phone_number}"

        # Avoid using "+" in the room name
        safe_phone_number = phone_number.replace("+", "")

        room_name = f"{safe_phone_number}-{agent_name}-room"

        metadata = json.dumps({
            "call_attempt_id": request.call_attempt_id,
            "salesforce_record_id": request.salesforce_record_id,
            "lead_name": request.lead_name,
            "phone_number": phone_number,
            "lead_type": request.lead_type,
            "course_opted": request.course_opted,
            "registration_deadline": request.registration_deadline,
        })

        dispatch = await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name=agent_name,
                room=room_name,
                metadata=metadata,
            )
        )

        logger.info(
            "Dispatch created successfully | phone_number=%s | room=%s",
            phone_number,
            room_name,
        )

        return {
            "status": "Call initiated successfully",
            "salesforce_record_id": request.salesforce_record_id,
            "phone_number": phone_number,
            "room_name": room_name,
        }

    except Exception as e:
        logger.exception("Error making call")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    finally:
        if lkapi:
            await lkapi.aclose()