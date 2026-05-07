from fastapi import APIRouter
from app.models import CommentInput, BatchInput
from app.rules.language_detector import detect_language
from app.rules.intent_classifier import classify_intent
from app.rules.sentiment_analyzer import analyze_sentiment
from app.rules.emoji_analyzer import has_only_emojis
from app.rules.ai_fallback import ai_fallback
from app.database import save_comment

router = APIRouter(prefix="/analyze", tags=["Analyze"])

async def process_comment(text: str) -> dict:
    language  = detect_language(text)
    intent    = classify_intent(text, language)
    sentiment = analyze_sentiment(text, language)
    emoji_only = has_only_emojis(text)
    ai_assisted = False

    # If rule engine couldn't determine intent, use AI fallback
    if intent == "general":
        fallback = await ai_fallback(text, language)
        intent      = fallback.get("intent", "general")
        sentiment   = fallback.get("sentiment", sentiment)
        ai_assisted = fallback.get("ai_assisted", False)

    return {
        "text":        text,
        "language":    language,
        "intent":      intent,
        "sentiment":   sentiment,
        "emoji_only":  emoji_only,
        "ai_assisted": ai_assisted
    }

# Single comment
@router.post("/single")
async def analyze_single(comment: CommentInput):
    result = await process_comment(comment.text)
    save_comment(result, comment.product_category if hasattr(comment, 'product_category') else 'general')
    return result

# Batch comments
@router.post("/batch")
async def analyze_batch(batch: BatchInput):
    results = []
    for text in batch.comments:
        result = await process_comment(text)
        results.append(result)

    intents    = [r["intent"]    for r in results]
    sentiments = [r["sentiment"] for r in results]
    languages  = [r["language"]  for r in results]
    ai_count   = sum(1 for r in results if r["ai_assisted"])

    summary = {
        "total":            len(results),
        "ai_assisted_count": ai_count,
        "rule_based_count": len(results) - ai_count,
        "intent_counts":    {i: intents.count(i)    for i in set(intents)},
        "sentiment_counts": {s: sentiments.count(s) for s in set(sentiments)},
        "language_counts":  {l: languages.count(l)  for l in set(languages)},
    }

    return {
        "results": results,
        "summary": summary
    }