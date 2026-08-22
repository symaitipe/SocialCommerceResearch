"""
AI fallback using Google Gemini API.
Covers the 14-category intent taxonomy for Sri Lankan social commerce comments.
"""

import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()

_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
GEMINI_MODEL = "gemini-3.5-flash-lite"

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
- "gaththa / received" alone -> order_purchase_confirmation
- "gaththa eka wada na" -> negative_feedback_complaint
- "WhatsApp number wada na" -> contact_request
- "hodaida?" is a quality question -> product_inquiry, not positive_feedback

Detected language mode: {language}
Comment: {text}

Return JSON only — no explanation, no markdown, no extra text:
{{"intent":"<one valid intent>"}}"""


def _clean_intent(value: str) -> str:
    value = str(value or "").strip().lower().replace(" ", "_")
    aliases = {
        "payment_method":        "payment_method_inquiry",
        "warranty_service":      "warranty_service_inquiry",
        "order_confirmation":    "order_purchase_confirmation",
        "negative_feedback":     "negative_feedback_complaint",
        "noise":                 "noise_off_topic",
        "general":               "noise_off_topic",
        "feedback":              "positive_feedback",
    }
    return aliases.get(value, value)


async def ai_fallback(text: str, language: str) -> dict:
    try:
        prompt = PROMPT_TEMPLATE.format(text=text, language=language)

        # Gemini is synchronous — run in executor to avoid blocking event loop
        import asyncio
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: _client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
        )

        raw = response.text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(raw)

        intent    = _clean_intent(result.get("intent", ""))
    
        if intent not in VALID_INTENTS:
            raise ValueError(f"Gemini returned unsupported intent: {intent!r}")

        return {
            "intent":      intent,
            "ai_assisted": True,
        }

    except Exception as e:
        print(f"⚠️  Gemini fallback failed: {str(e)}")
        return {
            "intent":      "noise_off_topic",
            "ai_assisted": False,
            "error":       str(e),
        }