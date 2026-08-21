from fastapi import APIRouter, BackgroundTasks
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
    get_connection
)
from app.graph.pipeline import run_pipeline
from app.graph.fb_graph_fetcher import post_comment_reply

router = APIRouter(prefix="/posts", tags=["Posts"])

class PostInput(BaseModel):
    facebook_url: str
    title: Optional[str] = None

class StatusUpdate(BaseModel):
    status: str

class ReplyInput(BaseModel):
    message: str


class BulkReplyInput(BaseModel):
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
    """SSE endpoint — streams pipeline progress to frontend."""
    async def event_stream():
        prev_count = 0
        attempts   = 0
        while attempts < 40:
            await asyncio.sleep(3)
            post = get_post_by_id(post_id)
            if not post:
                break
            current_count = post.get('total_comments', 0)
            status = {
                "total":        current_count,
                "last_fetched": post.get('last_fetched_at'),
                "new_count":    post.get('last_sync_new_count', 0),
                "done":         post.get('last_fetched_at') is not None
            }
            yield f"data: {json.dumps(status)}\n\n"
            if status['done'] and current_count == prev_count and attempts > 2:
                break
            prev_count = current_count
            attempts  += 1
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":      "no-cache",
            "X-Accel-Buffering":  "no"
        }
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


#----------------------------------------- post routes ------------------
@router.post("/{post_id}/mark-read")
def mark_read(post_id: int):
    affected = mark_post_comments_read(post_id)
    return {"post_id": post_id, "marked_read": affected}

@router.post("/fetch")
async def fetch_post(data: PostInput, background_tasks: BackgroundTasks):
    post = create_or_get_post(data.facebook_url, data.title)
    background_tasks.add_task(
        run_pipeline, post['id'], data.facebook_url, data.title or ""
    )
    return {
        "post_id": post['id'],
        "status":  "fetching",
        "message": "Comment extraction started in background"
    }

@router.patch("/comments/{comment_id}/status")
def update_status(comment_id: int, body: StatusUpdate):
    allowed = ['unread', 'read_not_replied', 'replied']
    if body.status not in allowed:
        return {"error": f"Status must be one of {allowed}"}
    update_comment_status(comment_id, body.status)
    return {"id": comment_id, "status": body.status, "updated": True}

@router.post("/comments/{comment_id}/reply")
async def reply_to_comment(comment_id: int, body: ReplyInput):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT facebook_comment_id FROM comments WHERE id = ?', (comment_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"success": False, "error": "Comment not found"}

    fb_comment_id = row['facebook_comment_id']
    result = await post_comment_reply(fb_comment_id, body.message)

    if result['success']:
        update_comment_status(comment_id, 'replied')

    return result

@router.post("/comments/bulk-reply")
async def bulk_reply(body: BulkReplyInput):
    results = []

    for comment_id in body.comment_ids:
        fb_comment_id = get_facebook_comment_id(comment_id)

        if not fb_comment_id:
            results.append({
                "comment_id": comment_id,
                "success": False,
                "error": "Comment not found"
            })
            continue

        result = await post_comment_reply(fb_comment_id, body.message)

        if result.get('success'):
            update_comment_status(comment_id, 'replied')

        results.append({
            "comment_id": comment_id,
            "success": result.get('success', False),
            "error": result.get('error')
        })

    success_count = sum(1 for r in results if r['success'])

    return {
        "results": results,
        "success_count": success_count,
        "fail_count": len(results) - success_count,
    }