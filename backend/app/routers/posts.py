from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import asyncio
import json

from app.database import (
    create_or_get_post,
    get_all_posts,
    get_post_by_id,
    get_comments_by_post,
    get_comments_by_post_and_intent,
    get_summary_by_post,
    get_activity_by_day,
    update_comment_status,
    mark_post_comments_read,
    get_facebook_comment_id,
    get_connection,
)
from app.graph.pipeline import run_pipeline
from app.graph.fb_graph_fetcher import post_comment_reply

router = APIRouter(prefix="/posts", tags=["Posts"])
_bulk_reply_lock = asyncio.Lock()
MAX_BULK_REPLIES = 25


class PostInput(BaseModel):
    facebook_url: str
    title: Optional[str] = None


class StatusUpdate(BaseModel):
    status: str


class ReplyInput(BaseModel):
    message: str


class BulkReplyInput(BaseModel):
    post_id: int
    comment_ids: list[int]
    message: str


@router.get("/")
def list_posts():
    return get_all_posts()


@router.get("/{post_id}/comments")
def post_comments(post_id: int):
    return get_comments_by_post(post_id)


@router.get("/{post_id}/summary")
def post_summary(post_id: int):
    return get_summary_by_post(post_id)


@router.get("/{post_id}/progress")
async def post_progress(post_id: int):
    async def event_stream():
        prev_count = 0
        attempts = 0
        while attempts < 40:
            await asyncio.sleep(3)
            post = get_post_by_id(post_id)
            if not post:
                break
            current_count = post.get("total_comments", 0)
            status = {
                "total": current_count,
                "last_fetched": post.get("last_fetched_at"),
                "new_count": post.get("last_sync_new_count", 0),
                "done": post.get("last_fetched_at") is not None,
            }
            yield f"data: {json.dumps(status)}\n\n"
            if status["done"] and current_count == prev_count and attempts > 2:
                break
            prev_count = current_count
            attempts += 1
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/{post_id}")
def get_post(post_id: int):
    return get_post_by_id(post_id)


@router.get("/{post_id}/activity")
def post_activity(post_id: int):
    return get_activity_by_day(post_id, days=7)


@router.get("/{post_id}/comments/{intent}")
def post_comments_by_intent(post_id: int, intent: str):
    return get_comments_by_post_and_intent(post_id, intent)


@router.post("/{post_id}/mark-read")
def mark_read(post_id: int):
    affected = mark_post_comments_read(post_id)
    return {"post_id": post_id, "marked_read": affected}


@router.post("/fetch")
async def fetch_post(data: PostInput, background_tasks: BackgroundTasks):
    post = create_or_get_post(data.facebook_url, data.title)
    background_tasks.add_task(run_pipeline, post["id"], data.facebook_url, data.title or "")
    return {
        "post_id": post["id"],
        "status": "fetching",
        "message": "Comment extraction started in background",
    }


@router.patch("/comments/{comment_id}/status")
def update_status(comment_id: int, body: StatusUpdate):
    allowed = ["unread", "read_not_replied", "replied"]
    if body.status not in allowed:
        return {"error": f"Status must be one of {allowed}"}
    update_comment_status(comment_id, body.status)
    return {"id": comment_id, "status": body.status, "updated": True}


def _read_comment(comment_id: int):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, post_id, facebook_comment_id, status, is_order_request "
            "FROM comments WHERE id = ?",
            (comment_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def _reply_failure(comment_id: int, error: str, **extra):
    return {"comment_id": comment_id, "success": False, "error": error, **extra}


async def _reply_to_saved_comment(comment_id: int, message: str, post_id: int | None = None):
    comment = _read_comment(comment_id)
    if comment is None:
        return _reply_failure(comment_id, "Comment not found")
    if post_id is not None and comment["post_id"] != post_id:
        return _reply_failure(comment_id, "Comment does not belong to this post")
    if comment["status"] == "replied":
        return _reply_failure(comment_id, "Already marked as replied; not sent again", skipped=True)
    if comment["is_order_request"]:
        return _reply_failure(comment_id, "Seller order-request template cannot be bulk-replied to")
    if not comment["facebook_comment_id"]:
        return _reply_failure(comment_id, "No Facebook comment ID (local test row)")

    response = await post_comment_reply(comment["facebook_comment_id"], message)
    if not response.get("success"):
        return _reply_failure(
            comment_id,
            response.get("error", "Facebook rejected the reply"),
            outcome_uncertain=response.get("outcome_uncertain", False),
            facebook_error_code=response.get("facebook_error_code"),
        )

    try:
        updated = update_comment_status(comment_id, "replied")
        if updated is False:
            raise RuntimeError("Database status update returned false")
    except Exception:
        return {
            "comment_id": comment_id,
            "success": True,
            "facebook_reply_id": response["comment_id"],
            "db_updated": False,
            "warning": "Reply was published on Facebook but the local status update failed; reconcile before sending again",
        }

    return {
        "comment_id": comment_id,
        "success": True,
        "facebook_reply_id": response["comment_id"],
        "db_updated": True,
    }


@router.post("/comments/{comment_id}/reply")
async def reply_to_comment(comment_id: int, body: ReplyInput):
    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="Reply message cannot be empty")
    if len(message) > 2000:
        raise HTTPException(status_code=422, detail="Reply message must be 2000 characters or fewer")
    async with _bulk_reply_lock:
        return await _reply_to_saved_comment(comment_id, message)


@router.post("/comments/bulk-reply")
async def bulk_reply(body: BulkReplyInput):
    message = body.message.strip()
    if body.post_id <= 0:
        raise HTTPException(status_code=422, detail="A valid post_id is required")
    if not message or len(message) > 2000:
        raise HTTPException(status_code=422, detail="Reply message must contain 1–2000 characters")
    if not body.comment_ids:
        raise HTTPException(status_code=422, detail="Select at least one comment")
    unique_ids = list(dict.fromkeys(body.comment_ids))
    if len(unique_ids) > MAX_BULK_REPLIES:
        raise HTTPException(status_code=422, detail=f"Select at most {MAX_BULK_REPLIES} comments per batch")
    if any(comment_id <= 0 for comment_id in unique_ids):
        raise HTTPException(status_code=422, detail="Invalid comment ID")
    if not get_post_by_id(body.post_id):
        raise HTTPException(status_code=404, detail="Post not found")

    # Serialize replies in this development server to prevent concurrent duplicate sends.
    async with _bulk_reply_lock:
        results = []
        for comment_id in unique_ids:
            results.append(await _reply_to_saved_comment(comment_id, message, body.post_id))

    success_count = sum(1 for item in results if item["success"])
    return {
        "results": results,
        "success_count": success_count,
        "fail_count": len(results) - success_count,
        "requested_count": len(unique_ids),
    }
