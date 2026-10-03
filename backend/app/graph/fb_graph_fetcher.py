import os
import re
import httpx
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")
API_VERSION = os.getenv("FB_API_VERSION", "v25.0")
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"


async def fetch_post_comments(post_id: str) -> list[dict]:
    comments = []
    url = f"{BASE_URL}/{post_id}/comments"
    params = {
        "fields": "id,message,from,created_time,parent",
        "access_token": ACCESS_TOKEN,
        "limit": 100,
        "filter": "stream",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        while url:
            response = await client.get(url, params=params)
            if response.status_code != 200:
                print(f"Facebook fetch failed (HTTP {response.status_code})")
                break
            data = response.json()
            for item in data.get("data", []):
                message = item.get("message", "").strip()
                if not message:
                    continue
                sender = item.get("from") or {}
                comments.append({
                    "comment_id": item.get("id"),
                    "commenter_name": sender.get("name", "Unknown"),
                    "commenter_fb_id": sender.get("id"),
                    "text": message,
                    "created_time": item.get("created_time"),
                    "comment_url": f"https://www.facebook.com/{item.get('id')}",
                    "parent_id": (item.get("parent") or {}).get("id"),
                })
            next_url = data.get("paging", {}).get("next")
            url = next_url or None
            params = {} if url else params
    print(f"Facebook fetched {len(comments)} comments")
    return comments


async def extract_post_id_from_url(post_url: str) -> str | None:
    if re.fullmatch(r"\d+_\d+", post_url.strip()):
        return post_url.strip()
    fbid = re.search(r"story_fbid=(\d+)", post_url)
    pgid = re.search(r"[?&]id=(\d+)", post_url)
    if fbid and pgid:
        return f"{pgid.group(1)}_{fbid.group(1)}"
    match = re.search(r"/posts/(\d+)", post_url)
    if match:
        return match.group(1)
    return await _resolve_share_link(post_url)


async def hide_comment(comment_id: str) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            f"{BASE_URL}/{comment_id}",
            params={"is_hidden": "true", "access_token": ACCESS_TOKEN},
        )
        try:
            data = response.json()
        except ValueError:
            data = {}
        if response.status_code != 200:
            return {
                "success": False,
                "error": data.get("error", {}).get("message", "Facebook hide failed"),
            }
        return {"success": True}


async def _resolve_share_link(share_url: str) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{BASE_URL}/",
                params={
                    "id": share_url,
                    "fields": "id,object_id",
                    "access_token": ACCESS_TOKEN,
                },
            )
            data = response.json()
            if data.get("object_id"):
                return data["object_id"]
            if data.get("id") and data["id"] != share_url:
                return data["id"]
            return None
    except (httpx.RequestError, ValueError):
        return None


async def post_comment_reply(comment_id: str, message: str) -> dict:
    """Reply publicly as the Page; a successful response contains the new reply ID."""
    comment_id = str(comment_id or "").strip()
    message = str(message or "").strip()
    if not ACCESS_TOKEN:
        return {"success": False, "error": "FB_ACCESS_TOKEN is not configured"}
    if not re.fullmatch(r"[A-Za-z0-9_]+", comment_id):
        return {"success": False, "error": "Invalid Facebook comment ID"}
    if not message:
        return {"success": False, "error": "Reply message cannot be empty"}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{BASE_URL}/{comment_id}/comments",
                data={"message": message},
                params={"access_token": ACCESS_TOKEN},
            )
    except httpx.RequestError:
        return {
            "success": False,
            "error": "Facebook request failed or timed out; check Facebook before retrying",
            "outcome_uncertain": True,
        }

    try:
        data = response.json()
    except ValueError:
        return {
            "success": False,
            "error": f"Facebook returned an unreadable response (HTTP {response.status_code}); check before retrying",
            "outcome_uncertain": response.status_code == 200,
        }

    if response.status_code != 200 or data.get("error"):
        fb_error = data.get("error") or {}
        return {
            "success": False,
            "error": fb_error.get("message") or f"Facebook HTTP {response.status_code}",
            "facebook_error_code": fb_error.get("code"),
        }

    reply_id = data.get("id")
    if not reply_id:
        return {
            "success": False,
            "error": "Facebook returned success without a reply ID; check before retrying",
            "outcome_uncertain": True,
        }
    return {"success": True, "comment_id": str(reply_id)}
