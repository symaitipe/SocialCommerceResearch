from fastapi import APIRouter
from app.models import CommentInput
from app.rules.language_detector import detect_language
from app.rules.sentiment_analyzer import analyze_sentiment

router = APIRouter(prefix="/sentiment", tags=["Sentiment"])

@router.post("/analyze")
def analyze(comment: CommentInput):
    language = detect_language(comment.text)
    sentiment = analyze_sentiment(comment.text, language)
    return {
        "text": comment.text,
        "language": language,
        "sentiment": sentiment
    }