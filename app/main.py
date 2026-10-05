from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import (
    health_route,
    # invoice_route,
    # livekit_server_route,
    # planogram_route,
    call_dispatch_route,
    # voice_analyze,
    # menu_analyzer_route
)
from app.core.config import settings
import logging
import sys
import asyncio
from fastapi.responses import JSONResponse
from livekit import api
import json


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Global variable to track agent process
agent_process = None


app = FastAPI(
    title="Rutx AI Services",
    description="A collection of AI services for Rutx",
    version="1.0.0",
)

# CORS middleware to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

routes = [
    # health_route.router,
    # invoice_route.router,
    # livekit_server_route.router,
    # planogram_route.router,
    call_dispatch_route.router,
    # voice_analyze.router,
    # menu_analyzer_route.router

]

# Include all routes
for route in routes:
    app.include_router(route)


# Add a health check endpoint to verify agent status
# @app.get("/agent-status")
# async def get_agent_status():
#     global agent_process
#     if agent_process and agent_process.poll() is None:
#         return {"status": "running", "pid": agent_process.pid}
#     else:
#         return {"status": "not_running", "pid": None}


# @app.post("/promo-agent")
# async def dispatch_promo_agent(numbers: list[str]):
#     LIVEKIT_URL = settings.promo_LIVEKIT_URL
#     LIVEKIT_API_KEY = settings.promo_LIVEKIT_API_KEY
#     LIVEKIT_API_SECRET = settings.promo_LIVEKIT_API_SECRET
#     agent_name = "promotion-agent"
#     try:
#         lkapi = api.LiveKitAPI(url=LIVEKIT_URL,
#                 api_key=LIVEKIT_API_KEY,
#                 api_secret=LIVEKIT_API_SECRET)
#         for number in numbers:
#             print(f"Making call to {number}")
#             print("TRY")
#             print("Agent name", agent_name)
#             number = "+91" + number
#             room_name = f"{number}-{agent_name}-room"
#             room_name = room_name.encode("utf-8", errors="ignore").decode("utf-8")

#             # ensure metadata is clean
#             metadata = json.dumps({"phone_number": number})
#             dispatch = await lkapi.agent_dispatch.create_dispatch(
#                 api.CreateAgentDispatchRequest(
#                     agent_name=agent_name, room=room_name, metadata=metadata
#                 )
#             )
#             print("created dispatch", dispatch)

#             # dispatches = await lkapi.agent_dispatch.list_dispatch(room_name=room_name)
#         await lkapi.aclose()
#         return {"status": "Call initiated successfully"}
#     except Exception as e:
#         print("EXCEPTION", e)
#         return {"status": f"Call initiation failed: {e}"}


# @app.post("/retail-avail")
# async def dispatch_retail_avail_agent(numbers: list[str]):
#     LIVEKIT_URL = settings.retailer_avail_LIVEKIT_URL
#     LIVEKIT_API_KEY = settings.retailer_avail_LIVEKIT_API_KEY 
#     LIVEKIT_API_SECRET = settings.retailer_avail_LIVEKIT_API_SECRET
#     agent_name = "retailer-avail-agent"
#     try:
#         lkapi = api.LiveKitAPI(url=LIVEKIT_URL,
#                 api_key=LIVEKIT_API_KEY,
#                 api_secret=LIVEKIT_API_SECRET)
#         for number in numbers:
#             print(f"Making call to {number}")
#             print("TRY")
#             print("Agent name", agent_name)
#             number = "+91" + number
#             room_name = f"{number}-{agent_name}-room"
#             room_name = room_name.encode("utf-8", errors="ignore").decode("utf-8")

#             # ensure metadata is clean
#             metadata = json.dumps({"phone_number": number})
#             dispatch = await lkapi.agent_dispatch.create_dispatch(
#                 api.CreateAgentDispatchRequest(
#                     agent_name=agent_name, room=room_name, metadata=metadata
#                 )
#             )
#             print("created dispatch", dispatch)

#             # dispatches = await lkapi.agent_dispatch.list_dispatch(room_name=room_name)
#         await lkapi.aclose()
#         return {"status": "Call initiated successfully"}
#     except Exception as e:
#         print("EXCEPTION", e)
#         return {"status": f"Call initiation failed: {e}"}

