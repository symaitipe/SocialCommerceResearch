from fastapi import APIRouter
from app.models import CommentInput
from app.rules.language_detector import detect_language
from app.rules.intent_classifier import classify_intent

router = APIRouter(prefix="/intent", tags=["Intent"])

@router.post("/classify")
def classify(comment: CommentInput):
    language = detect_language(comment.text)
    intent = classify_intent(comment.text, language)
    return {
        "text": comment.text,
        "language": language,
        "intent": intent
    }