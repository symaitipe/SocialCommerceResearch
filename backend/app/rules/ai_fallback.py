"""
AI fallback for the SocialSell 14-category intent taxonomy.

This replacement keeps the current local Ollama/Qwen setup used in the
version2 repository, but fixes the biggest functional problem in the current
prompt: the old prompt exposes only 6 broad intents and therefore cannot
correctly return the four AI-only categories.

If the final implementation is Gemini instead of Ollama, keep this taxonomy
and JSON contract but replace only the API-call section.
"""

import json
import httpx

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:latest"

VALID_INTENTS = {
    "purchase_intent",
    "product_inquiry",
    "price_inquiry",
    "price_complaint",
    "delivery_inquiry",
    "location_availability",
    "payment_method_inquiry",
    "warranty_service_inquiry",
    "order_purchase_confirmation",
    "positive_feedback",
    "negative_feedback_complaint",
    "suggestion",
    "contact_request",
    "noise_off_topic",
}

PROMPT_TEMPLATE = """You classify customer comments from Sri Lankan product-selling social media posts.

The comment may be written in English, Sinhala, Singlish (romanised Sinhala),
or a mixture.

Choose exactly ONE primary intent from this 14-category taxonomy:

1. purchase_intent
   Customer shows a clear desire or plan to buy/order the product.

2. product_inquiry
   Customer asks about product features, variants, quality, use, size, colour,
   availability of a product option, or other product details.

3. price_inquiry
   Customer asks what the price/cost is.

4. price_complaint
   Customer is dissatisfied with the price, says it is too high/expensive,
   or complains about a price increase. This is NOT a normal price question.

5. delivery_inquiry
   Customer asks about delivery, courier, shipping, delivery charges,
   delivery time, or whether delivery is available.

6. location_availability
   Customer asks where the shop/showroom/branch is, where the product can be
   obtained, or about physical-location availability.

7. payment_method_inquiry
   Customer asks about card payment, Koko/installments, bank transfer,
   cash-on-delivery, or another payment method.

8. warranty_service_inquiry
   Customer asks about warranty, guarantee, repair, replacement, return,
   service centre, after-sales service, or a warranty claim.

9. order_purchase_confirmation
   Customer says they already ordered, bought, received, or obtained the
   product. If the same sentence mainly reports a fault/problem after receiving
   it, prefer negative_feedback_complaint.

10. positive_feedback
    Customer gives praise, recommendation, satisfaction, or a positive review.

11. negative_feedback_complaint
    Customer complains about product quality, damage, failure, seller response,
    delivery failure, or another negative experience.
    IMPORTANT: if the problem is specifically a broken contact channel such as
    WhatsApp/website/phone, consider contact_request instead.

12. suggestion
    Customer gives an idea or recommendation for how the seller/product/service
    could be improved.

13. contact_request
    Customer asks how to contact the seller, asks for a phone/WhatsApp/contact
    method, or reports that a seller contact channel is not working.

14. noise_off_topic
    Comment has no meaningful product/customer intent for this taxonomy.

Important distinctions:
- "price?" / "price kiyada?" -> price_inquiry
- "too much price" / "price is too high" -> price_complaint
- "gaththa / received" alone can be order_purchase_confirmation
- "gaththa eka wada na" / "received it but it does not work"
  -> negative_feedback_complaint
- "WhatsApp number wada na" -> contact_request, not product complaint
- A quality question such as "hodaida?" is product_inquiry, not positive_feedback

Detected language mode: {language}
Comment: {text}

Return JSON only:
{{"intent":"<one valid intent>","sentiment":"positive|negative|neutral"}}
"""


def _clean_intent(value: str) -> str:
    value = str(value or "").strip().lower().replace(" ", "_")
    aliases = {
        "payment_method": "payment_method_inquiry",
        "warranty_service": "warranty_service_inquiry",
        "order_confirmation": "order_purchase_confirmation",
        "negative_feedback": "negative_feedback_complaint",
        "noise": "noise_off_topic",
        "general": "noise_off_topic",
    }
    return aliases.get(value, value)


async def ai_fallback(text: str, language: str) -> dict:
    try:
        prompt = PROMPT_TEMPLATE.format(text=text, language=language)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    # Low temperature is preferable for repeatable classification.
                    "options": {"temperature": 0.1},
                },
            )
            response.raise_for_status()

        data = response.json()
        raw = data.get("response", "").strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(raw)

        intent = _clean_intent(result.get("intent"))
        sentiment = str(result.get("sentiment", "neutral")).strip().lower()

        if intent not in VALID_INTENTS:
            raise ValueError(f"LLM returned unsupported intent: {intent!r}")

        if sentiment not in {"positive", "negative", "neutral"}:
            sentiment = "neutral"

        return {
            "intent": intent,
            "sentiment": sentiment,
            "ai_assisted": True,
        }

    except Exception as e:
        # Do not silently pretend a failed AI call was a valid classification.
        return {
            "intent": "noise_off_topic",
            "sentiment": "neutral",
            "ai_assisted": False,
            "error": str(e),
        }