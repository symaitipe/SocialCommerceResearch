import re

INTENT_RULES = {
    "price_inquiry": {
        "english": ["price", "cost", "how much", "rate", "charge", "fee"],
        "singlish": ["ganak", "kiyadha", "priceka", "mila", "ගණන්", "ගාන"],
        "sinhala": ["මිල", "ගණන", "කීයද", "ගාන"],
        "mixed": ["price", "මිල", "ganak", "kiyadha"]
    },
    "delivery_inquiry": {
        "english": ["delivery", "deliver", "shipping", "ship", "courier", "arrive", "when"],
        "singlish": ["deliver", "yanawada", "enawada", "courier", "labenda"],
        "sinhala": ["ලැබෙනවද", "එනවද", "යවනවද", "කුරියර්"],
        "mixed": ["delivery", "ලැබෙනවද", "deliver", "yanawada"]
    },
    "purchase_intent": {
        "english": ["i want", "i need", "buy", "order", "purchase", "take", "ill take"],
        "singlish": ["gannawam", "onate", "order karannam", "ganna ona", "laba gannam"],
        "sinhala": ["ගන්නවම්", "ඕනේ", "ගන්න ඕනේ", "ඕඩර්"],
        "mixed": ["buy", "ගන්නවම්", "order", "ඕනේ"]
    },
    "product_inquiry": {
        "english": ["available", "size", "color", "colour", "material", "stock", "specification", "detail"],
        "singlish": ["available da", "tiyanawada", "size eka", "colour eka", "details denna"],
        "sinhala": ["තිබෙනවද", "සයිස්", "වර්ණ", "විස්තර", "ස්ටොක්"],
        "mixed": ["available", "තිබෙනවද", "size", "සයිස්"]
    },
    "feedback": {
        "english": ["good", "bad", "nice", "worst", "excellent", "poor", "love", "hate", "review", "quality"],
        "singlish": ["lassanai", "naragui", "hodai", "wadagath", "niyamai", "pissu"],
        "sinhala": ["ලස්සනයි", "නරකයි", "හොඳයි", "වාසිදායකයි"],
        "mixed": ["good", "හොඳයි", "bad", "නරකයි"]
    }
}

def classify_intent(text: str, language: str) -> str:
    text_lower = text.lower()
    lang_key = language if language in ["english", "singlish", "sinhala", "mixed"] else "english"

    for intent, lang_keywords in INTENT_RULES.items():
        keywords = lang_keywords.get(lang_key, [])
        for keyword in keywords:
            if keyword in text_lower:
                return intent

# fallback to emoji intent if text rules didn't match
    from app.rules.emoji_analyzer import analyze_emoji_intent
    emoji_intent = analyze_emoji_intent(text)
    return emoji_intent if emoji_intent else "general"