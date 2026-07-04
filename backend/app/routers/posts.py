from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from app.database import (
    create_or_get_post,
    get_all_posts,
    get_post_by_id,
    get_comments_by_post,
    get_summary_by_post,
    update_comment_status
)
from app.graph.pipeline import run_pipeline

router = APIRouter(prefix="/posts", tags=["Posts"])

class PostInput(BaseModel):
    facebook_url: str
    title: str = None

class StatusUpdate(BaseModel):
    status: str

@router.get("/")
def list_posts():
    return get_all_posts()

@router.get("/{post_id}")
def get_post(post_id: int):
    return get_post_by_id(post_id)

@router.get("/{post_id}/comments")
def post_comments(post_id: int):
    return get_comments_by_post(post_id)

@router.get("/{post_id}/summary")
def post_summary(post_id: int):
    return get_summary_by_post(post_id)

@router.post("/fetch")
async def fetch_post(data: PostInput, background_tasks: BackgroundTasks):
    post = create_or_get_post(data.facebook_url, data.title)
    background_tasks.add_task(run_pipeline, post['id'], data.facebook_url, data.title or "")
    return {
        "post_id": post['id'],
        "status": "fetching",
        "message": "Comment extraction started in background"
    }

@router.patch("/comments/{comment_id}/status")
def update_status(comment_id: int, body: StatusUpdate):
    allowed = ['new', 'pending', 'done']
    if body.status not in allowed:
        return {"error": f"Status must be one of {allowed}"}
    update_comment_status(comment_id, body.status)
    return {"id": comment_id, "status": body.status, "updated": True}