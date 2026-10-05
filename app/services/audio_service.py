import requests
from google import genai
from app.core.config import settings

DEEPGRAM_URL = "https://api.deepgram.com/v1/listen"

gemini = genai.Client(api_key=settings.VOICE_MEMO_GEMINI_API_KEY)

SUMMARY_PROMPT = """
You are an expert Field Sales Intelligence Assistant.

Your job is to analyze a conversation between a Field Sales Associate (FSA) and a Retailer,
understand its intent and context, then produce a clean, structured summary.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHAT TO IGNORE (skip completely):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Greetings, farewells, thank-yous
- Filler words and small talk
- Repeated acknowledgements ("okay", "sure", "got it", "hmm")
- Anything that carries zero business value

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HOW TO SUMMARIZE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1 — Understand the conversation:
Read the full transcript. Identify what topics were actually discussed
(e.g. stock issues, complaints, pricing, competitor activity, store feedback, etc.)

Step 2 — Create subheadings dynamically:
Do NOT use a fixed template. Instead, create subheadings based on ONLY what was
actually discussed in this conversation. Each subheading should represent a real
topic from the conversation.

Examples of subheadings you might create (only use if relevant):
  → Stock & Availability Issues
  → Pricing Concerns
  → Competitor Activity
  → Product Feedback
  → Retailer Requests
  → Sales Performance
  → Visibility & Merchandising
  → Distribution Problems
  → Promotions & Campaigns
  → Service Quality
  → Action Items
  ... or any other topic that fits this specific conversation

Step 3 — Write crisp bullet points under each subheading:
- Each point should be a single, clear, standalone fact or observation
- Bold the most critical words or phrases in each point
- No vague or generic points — be specific
- If something was mentioned with urgency or frustration, reflect that tone

OUTPUT FORMAT (example structure — yours will differ per conversation):

CONVERSATION SUMMARY

Intent: <One line — what this conversation was mainly about>

[SUBHEADING 1 — e.g. Stock & Availability]
- <crisp point>
- <crisp point>

[SUBHEADING 2 — e.g. Competitor Activity]
- <crisp point>
- <crisp point>

[SUBHEADING 3 — e.g. Action Items]
- <crisp point — who needs to do what>

... (only as many subheadings as needed)

RULES:
- Dynamic subheadings — based on what was actually discussed
- Every important business point must be captured
- Bold key terms, product names, numbers, issue keywords
- A reader should fully understand the conversation just from this summary
- No fixed template — structure must fit the conversation
- No filler, no fluff, no repetition
- Never invent information not present in the transcript
- No need to give suggestions or action items unless they were explicitly mentioned in the conversation

Transcript:
"""


def transcribe_audio(audio_bytes: bytes) -> str:
    try:
        headers = {
            "Authorization": f"Token {settings.DEEPGRAM_API_KEY}",
            "Content-Type": "audio/mpeg"
        }
        params = {
            "model": "nova-2",
            "smart_format": "true",
            "punctuate": "true",
            "diarize": "true",
            "detect_language": "true",
            "paragraphs": "true",
            "utterances": "true"
        }
        response = requests.post(
            DEEPGRAM_URL,
            headers=headers,
            params=params,
            data=audio_bytes,
            timeout=300
        )
        if response.status_code != 200:
            raise Exception(response.text)

        result = response.json()
        return result["results"]["channels"][0]["alternatives"][0]["transcript"]

    except Exception as e:
        raise Exception(f"Deepgram transcription failed: {str(e)}")


def summarize_transcript(transcript: str) -> str:
    try:
        response = gemini.models.generate_content(
            model="gemini-2.5-flash",
            contents=SUMMARY_PROMPT + transcript
        )
        return response.text

    except Exception as e:
        raise Exception(f"Gemini summarization failed: {str(e)}")