from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    GEMINI_API_KEY: str = ""
    ROBOFLOW_API_KEY: str = ""
    ROBOFLOW_API_URL: str = ""
    LIVEKIT_URL: str = ""
    LIVEKIT_API_SECRET: str = ""
    LIVEKIT_API_KEY: str = ""
    LIVEKIT_URL_RTX: str = ""
    LIVEKIT_API_SECRET_RTX: str = ""
    LIVEKIT_API_KEY_RTX: str = ""
    DEEPGRAM_API_KEY: str=""
    VOICE_MEMO_GEMINI_API_KEY: str=""
    PLANOGRAM_GEMINI_API_KEY: str=""
    OWNERSHIP_MATCH_THRESHOLD: int = 97
    OUR_PRODUCTS: list[str] = [
        "coca-cola",
        "coca-cola original taste",
        "coca-cola zero sugar",
        "diet coke",
        "coke",
        "sprite",
        "sprite zero sugar",
        "sprite zero",
        "fanta",
        "fanta orange",
        "thumbs up",
        "minute maid",
        "minute maid orange",
        "minute maid apple",
    ]
    
    
settings = Settings()   