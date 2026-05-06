import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

PROMPT_TEMPLATE = """
You are a comment classification assistant for a Sri Lankan social media selling platform.
You will receive a customer comment written in Sinhala, Singlish, English, or a mix.

Classify the comment into:
1. intent - one of: price_inquiry, delivery_inquiry, purchase_intent, product_inquiry, feedback, general
2. sentiment - one of: positive, negative, neutral

Language detected: {language}
Comment: {text}

Respond ONLY in this exact JSON format with no explanation, no markdown, no extra text:
{{"intent": "...", "sentiment": "..."}}
"""

async def ai_fallback(text: str, language: str) -> dict:
    try:
        prompt = PROMPT_TEMPLATE.format(text=text, language=language)

        response = client.models.generate_content(
           model="gemini-2.0-flash-lite",
            contents=prompt
        )

        raw = response.text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(raw)

        return {
            "intent":      result.get("intent", "general"),
            "sentiment":   result.get("sentiment", "neutral"),
            "ai_assisted": True
        }

    except Exception as e:
        print(f"AI Fallback Error: {str(e)}")
        return {
            "intent":      "general",
            "sentiment":   "neutral",
            "ai_assisted": False,
            "error":       str(e)
        }