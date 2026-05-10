from fastapi import APIRouter, Query
from app.database import (
    get_all_comments,
    get_comments_by_category,
    update_comment_status,
    get_comments_by_intent,
    get_summary,
    get_summary_by_category
)
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/comments", tags=["Comments"])

class StatusUpdate(BaseModel):
    status: str

@router.get("/")
def list_comments(category: Optional[str] = Query(None)):
    if category:
        return get_comments_by_category(category)
    return get_all_comments()

@router.get("/summary")
def comments_summary(category: Optional[str] = Query(None)):
    if category:
        return get_summary_by_category(category)
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