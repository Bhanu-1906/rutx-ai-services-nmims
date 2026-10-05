from app.core.config import settings
from livekit import api
import json
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

class LivekitServerService:
    def __init__(self, user_id: str, salesforce_access_token: str,  url: str, room:str = "my-room") -> None:
        self.user_id = user_id
        self.salesforce_access_token = salesforce_access_token
        self.room = room
        self.url = url
        # Pre-initialize the API key and secret for better performance
        self._api_key = settings.LIVEKIT_API_KEY_RTX
        self._api_secret = settings.LIVEKIT_API_SECRET_RTX

    def generate_access_token(self):
        """Generate a LiveKit access token with caching for better performance"""
        try:
            # Create the token with all required information
            token = (
                api.AccessToken(self._api_key, self._api_secret)
                .with_identity(self.user_id)
                .with_name("LiveKit User")
                .with_metadata(
                    json.dumps(
                        {"user_id": self.user_id, "access_token": self.salesforce_access_token, "url": self.url}
                    )
                )
                .with_grants(api.VideoGrants(room_join=True, room=self.room))
            )
            return token.to_jwt()
        except Exception as e:
            logger.error(f"Error generating token: {e}")
            raise

# Create a cached version of the token generator for frequently used rooms
@lru_cache(maxsize=100)
def get_cached_room_token(room_name: str):
    """Get a cached room token for system use"""
    service = LivekitServerService("system", "system-token", room=room_name)
    return service.generate_access_token()
