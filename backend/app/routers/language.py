from fastapi import APIRouter
from app.models import CommentInput
from app.rules.language_detector import detect_language

router = APIRouter(prefix="/language", tags=["Language"])

@router.post("/detect")
def detect(comment: CommentInput):
    language = detect_language(comment.text)
    return {
        "text": comment.text,
        "language": language
    }