EMOJI_SENTIMENT = {
    "positive": [
        "❤️", "😍", "👍", "🥰", "😊", "💯", "🔥", "✅", "👌", "😁",
        "🤩", "💕", "💖", "💗", "💓", "💞", "🙏", "😃", "😄", "🥳",
        "👏", "💪", "⭐", "🌟", "✨", "😘", "🤗"
    ],
    "negative": [
        "😡", "🤮", "👎", "😤", "🤬", "❌", "💔", "😠", "🖕", "😒",
        "🙄", "😑", "😞", "😟", "😣", "😖", "😩", "😫", "💀", "🤢"
    ],
    "neutral": [
        "😐", "🤔", "😶", "🤷", "😑"
    ]
}

EMOJI_INTENT = {
    "price_inquiry": ["💰", "💵", "🤑", "💲"],
    "delivery_inquiry": ["🚚", "📦", "🛵", "🚴", "🏍️"],
    "purchase_intent": ["🛒", "🛍️", "💳"],
    "feedback": ["⭐", "🌟", "💯", "👍", "👎"]
}

def analyze_emoji_sentiment(text: str) -> str | None:
    positive_score = sum(1 for e in EMOJI_SENTIMENT["positive"] if e in text)
    negative_score = sum(1 for e in EMOJI_SENTIMENT["negative"] if e in text)
    neutral_score  = sum(1 for e in EMOJI_SENTIMENT["neutral"]  if e in text)

    if positive_score == 0 and negative_score == 0 and neutral_score == 0:
        return None  # no emojis found, don't override text sentiment

    if positive_score > negative_score:
        return "positive"
    if negative_score > positive_score:
        return "negative"
    return "neutral"

def analyze_emoji_intent(text: str) -> str | None:
    for intent, emojis in EMOJI_INTENT.items():
        for emoji in emojis:
            if emoji in text:
                return intent
    return None  # no intent emoji found

def has_only_emojis(text: str) -> bool:
    # Check if comment is emoji-only (no letters or digits)
    import re
    stripped = re.sub(r'\s+', '', text)
    return bool(stripped) and not bool(re.search(r'[a-zA-Z0-9\u0D80-\u0DFF]', stripped))