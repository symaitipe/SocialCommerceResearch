import os
import httpx
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")
API_VERSION  = os.getenv("FB_API_VERSION", "v25.0")
BASE_URL     = f"https://graph.facebook.com/{API_VERSION}"


async def fetch_post_comments(post_id: str) -> list[dict]:
    """
    Fetch all comments for a Facebook post using Graph API.
    Handles pagination automatically — fetches every page until done.
    Returns list of dicts with: comment_id, commenter_name, text, created_time
    """
    comments = []
    url = f"{BASE_URL}/{post_id}/comments"
    params = {
    "fields":       "id,message,from,created_time,parent",
    "access_token": ACCESS_TOKEN,
    "limit":        100,
    "filter":       "stream",
}

    async with httpx.AsyncClient(timeout=30.0) as client:
        while url:
            response = await client.get(url, params=params)

            if response.status_code != 200:
                print(f"❌ Graph API error: {response.status_code} — {response.text}")
                break

            data = response.json()

            for item in data.get("data", []):
                message = item.get("message", "").strip()
                if not message:
                    continue

                sender = item.get("from", {})
                comments.append({
                    "comment_id":      item.get("id"),
                    "commenter_name":  sender.get("name", "Unknown"),
                    "commenter_fb_id": sender.get("id"),
                    "text":            message,
                    "created_time":    item.get("created_time"),
                    "comment_url":     f"https://www.facebook.com/{item.get('id')}",
                    "parent_id":       item.get("parent", {}).get("id")
                })

            # Pagination — follow next page if exists
            paging = data.get("paging", {})
            next_url = paging.get("next")

            if next_url:
                url    = next_url
                params = {}  # next URL already has all params baked in
            else:
                break

    print(f"✅ Graph API fetched {len(comments)} comments")
    return comments


async def extract_post_id_from_url(post_url: str) -> str | None:
    import re

    # Already a compound numeric ID
    if re.match(r'^\d+_\d+$', post_url.strip()):
        return post_url.strip()

    # Numeric story_fbid + numeric id → compound ID
    fbid = re.search(r'story_fbid=(\d+)', post_url)
    pgid = re.search(r'[?&]id=(\d+)', post_url)
    if fbid and pgid:
        return f"{pgid.group(1)}_{fbid.group(1)}"

    # /posts/POST_ID
    match = re.search(r'/posts/(\d+)', post_url)
    if match:
        return match.group(1)

    # All other formats (pfbid, share links) → resolve via Graph API
    return await _resolve_share_link(post_url)


#Hide comments for customer confirmations with personal data
async def hide_comment(comment_id: str) -> dict:
    """
    Hide a Facebook comment from public view.
    Used to protect customer personal details.
    Comment remains visible to commenter and page admin only.
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            f"{BASE_URL}/{comment_id}",
            params={
                "is_hidden":    "true",
                "access_token": ACCESS_TOKEN,
            }
        )
        data = response.json()
        if response.status_code != 200:
            return {
                "success": False,
                "error":   data.get("error", {}).get("message", "Unknown error")
            }
        return {"success": True}

async def _resolve_share_link(share_url: str) -> str | None:
    """
    Resolves a Facebook share link by fetching the URL object from Graph API.
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # First try: resolve URL to object
            response = await client.get(
                f"{BASE_URL}/",
                params={
                    "id":           share_url,
                    "fields":       "id,object_id",
                    "access_token": ACCESS_TOKEN,
                }
            )

            data = response.json()
            print(f"🔍 Share link resolution response: {data}")

            # Try object_id first (actual post ID)
            if data.get("object_id"):
                print(f"✅ Resolved to object_id: {data['object_id']}")
                return data["object_id"]

            # Try id field
            if data.get("id") and data["id"] != share_url:
                print(f"✅ Resolved to id: {data['id']}")
                return data["id"]

            print("❌ Could not resolve share link to a post ID")
            return None

    except Exception as e:
        print(f"❌ Share link resolution error: {str(e)}")
        return None
    

async def post_comment_reply(comment_id: str, message: str) -> dict:
    """
    Post a reply to a Facebook comment as the Page.
    Requires pages_manage_engagement permission.
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            f"{BASE_URL}/{comment_id}/replies",
            params={
                "message":      message,
                "access_token": ACCESS_TOKEN,
            }
        )
        data = response.json()
        if response.status_code != 200:
            return {
                "success": False,
                "error":   data.get("error", {}).get("message", "Unknown error")
            }
        return {
            "success":    True,
            "comment_id": data.get("id")
        }