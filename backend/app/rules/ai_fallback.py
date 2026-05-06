import json
import httpx

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:latest"

PROMPT_TEMPLATE = """You are a comment classification assistant for a Sri Lankan social media selling platform.
You will receive a customer comment written in Sinhala, Singlish, English, or a mix.

Intent definitions:
- price_inquiry: asking about price, cost, how much
- delivery_inquiry: asking about delivery, shipping, when it arrives
- purchase_intent: expressing desire to buy or order
- product_inquiry: asking about availability, size, color, material, details
- feedback: giving opinion, review, compliment or complaint about product
- general: casual conversation, greeting, unclear meaning

Sentiment definitions:
- positive: happy, satisfied, interested, enthusiastic
- negative: unhappy, complaining, disappointed
- neutral: no clear emotion, just asking a question

Language detected: {language}
Comment: {text}

Respond ONLY in this exact JSON format with no explanation, no markdown, no extra text:
{{"intent": "...", "sentiment": "..."}}"""

async def ai_fallback(text: str, language: str) -> dict:
    try:
        prompt = PROMPT_TEMPLATE.format(text=text, language=language)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False
                }
            )
        
        print(f"Ollama status code: {response.status_code}")
        print(f"Ollama raw response: {response.text}")

        data = response.json()
        raw = data.get("response", "").strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(raw)

        return {
            "intent":      result.get("intent", "general"),
            "sentiment":   result.get("sentiment", "neutral"),
            "ai_assisted": True
        }

    except Exception as e:
        import traceback
        print(f"AI Fallback Error: {str(e)}")
        print(traceback.format_exc())
        return {
            "intent":      "general",
            "sentiment":   "neutral",
            "ai_assisted": False,
            "error":       str(e)
        }