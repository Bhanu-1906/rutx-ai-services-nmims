from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas.voice_memo_model import AnalyzeResponse
from app.services.audio_service import transcribe_audio, summarize_transcript

router = APIRouter(prefix="/voice_memo", tags=["Voice memo Analysis"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(file: UploadFile = File(...)):
    try:
        if not file.filename.lower().endswith(".mp3"):
            raise HTTPException(status_code=400, detail="Only MP3 files supported")

        audio_bytes = await file.read()

        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Empty file uploaded")

        transcript = transcribe_audio(audio_bytes)

        if not transcript.strip():
            raise HTTPException(status_code=400, detail="No speech detected")

        summary = summarize_transcript(transcript)

        print(summary)

        return AnalyzeResponse(status="success", summary=summary)

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))