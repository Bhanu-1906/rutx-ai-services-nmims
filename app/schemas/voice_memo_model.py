from pydantic import BaseModel

class AnalyzeResponse(BaseModel):
    status: str
    summary: str