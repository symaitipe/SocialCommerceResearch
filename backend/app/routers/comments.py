from fastapi import APIRouter
from app.database import (
    get_all_comments,
    update_comment_status,
    get_comments_by_intent,
    get_summary
)
from pydantic import BaseModel

router = APIRouter(prefix="/comments", tags=["Comments"])

class StatusUpdate(BaseModel):
    status: str  # 'new', 'pending', 'done'

@router.get("/")
def list_comments():
    return get_all_comments()

@router.get("/summary")
def comments_summary():
    return get_summary()

@router.get("/intent/{intent}")
def comments_by_intent(intent: str):
    return get_comments_by_intent(intent)

@router.patch("/{comment_id}/status")
def update_status(comment_id: int, body: StatusUpdate):
    allowed = ['new', 'pending', 'done']
    if body.status not in allowed:
        return {"error": f"Status must be one of {allowed}"}
    update_comment_status(comment_id, body.status)
    return {"id": comment_id, "status": body.status, "updated": True}