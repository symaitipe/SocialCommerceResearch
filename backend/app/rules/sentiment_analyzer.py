from app.rules.emoji_analyzer import analyze_emoji_sentiment

SENTIMENT_RULES = {
    "positive": {
        "english": ["good", "great", "excellent", "nice", "love", "perfect", "best", "happy", "thanks", "thank you"],
        "singlish": ["hodai", "lassanai", "niyamai", "superai", "wadagathui", "thank you", "thanks"],
        "sinhala": ["හොඳයි", "ලස්සනයි", "නියමයි", "සුපිරි", "ස්තූතියි"],
        "mixed": ["good", "හොඳයි", "nice", "නියමයි", "superai"]
    },
    "negative": {
        "english": ["bad", "worst", "poor", "hate", "terrible", "useless", "waste", "scam", "fraud", "disappointed"],
        "singlish": ["naragui", "pissu", "boru", "scam", "waste", "cheat", "disappointed"],
        "sinhala": ["නරකයි", "බොරු", "පිස්සු", "වේස්ට්", "කොල්ලකෑම"],
        "mixed": ["bad", "නරකයි", "waste", "බොරු", "scam"]
    }
}

def analyze_sentiment(text: str, language: str) -> str:
    text_lower = text.lower()
    lang_key = language if language in ["english", "singlish", "sinhala", "mixed"] else "english"

    positive_keywords = SENTIMENT_RULES["positive"].get(lang_key, [])
    negative_keywords = SENTIMENT_RULES["negative"].get(lang_key, [])

    positive_score = sum(1 for word in positive_keywords if word in text_lower)
    negative_score = sum(1 for word in negative_keywords if word in text_lower)

    # Get emoji sentiment as a secondary signal
    emoji_sentiment = analyze_emoji_sentiment(text)

    # If text has no clear sentiment, let emoji decide
    if positive_score == 0 and negative_score == 0:
        return emoji_sentiment if emoji_sentiment else "neutral"

    # If text has sentiment, emoji can boost it but not alone override
    if positive_score > negative_score:
        return "positive"
    if negative_score > positive_score:
        return "negative"

    # Tie — let emoji break it
    return emoji_sentiment if emoji_sentiment else "neutral"