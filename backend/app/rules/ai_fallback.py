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
   Customer submits an order by providing all three:
   - customer or recipient name,
   - one or more phone numbers,
   - delivery address or sufficiently clear delivery details.

   These details may appear in any order. A structured submission
   of all three can indicate an implicit order without an explicit
   purchase phrase.

   A phone number alone or incomplete details do not establish
   an order. The details must indicate an order submission rather
   than an unrelated request or statement.

10. positive_feedback
    Customer gives praise, recommendation, satisfaction, or a positive review.

11. negative_feedback_complaint
    Customer complains about product quality, damage, failure, seller response,
    delivery failure, or another negative experience.

12. suggestion
    Customer gives an idea or recommendation for how the seller/product/service
    could be improved.

13. contact_request
    Asks for phone/WhatsApp/contact info, reports a broken contact channel,
    or sends a bare greeting ("hi"/"hello") with no other content.

14. noise_off_topic
    Comment has no meaningful product/customer intent for this taxonomy.

Important distinctions:

Classification boundaries:
- Determine the primary intent from the customer's actual request
  or statement, not from isolated keywords. If multiple intents
  occur, select the one emphasized by the main request.

- Price Inquiry asks about the product's price, even when product
  attributes are mentioned. Product Inquiry asks about features,
  variants, suitability, quality, or specifications, even when
  price is mentioned incidentally. Delivery charges belong to
  Delivery Inquiry.

- Price Complaint expresses dissatisfaction with the price or
  a price increase. Other product, delivery, or seller-service
  complaints belong to Negative Feedback/Complaint.

- Distinguish product-quality questions from Positive Feedback.
  Suggestions propose improvements; positive remarks accompanying
  a suggestion do not automatically make it Positive Feedback.

- Contact Request concerns obtaining contact details, problems
  with contact channels, or context-free greetings. A bare phone
  number without a discernible request is Noise/Off-topic.

- Order/Purchase Confirmation may be implicit when the customer
  provides a name, one or more phone numbers, and delivery
  details together as an order submission. Field order is
  irrelevant. Do not infer an order from incomplete details
  or unrelated contact information.



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

        intent = _clean_intent(result.get("intent", ""))

        if intent not in VALID_INTENTS:
            raise ValueError(f"Gemini returned unsupported intent: {intent!r}")

        return {
            "intent": intent,
            "ai_assisted": True,
        }

    except Exception as e:
        print(f"⚠️  Gemini fallback failed: {str(e)}")
        return {
            "intent": "noise_off_topic",
            "ai_assisted": False,
            "error": str(e),
        }