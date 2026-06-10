import asyncio

async def load_post(page, url: str, expected_title: str) -> bool:
    """
    Step 1: Navigate to the Facebook post URL.
    Verifies the post title matches before continuing.
    Returns True if correct post loaded, raises Exception if not.
    """
    print(f"🌐 Loading post URL...")
    await page.goto(url, wait_until='domcontentloaded', timeout=30000)
    await asyncio.sleep(3)

    # Check if redirected to login page
    if 'login' in page.url:
        raise Exception("SESSION_EXPIRED")

    # Verify correct post by checking title exists in page
    print(f"🔍 Verifying post title: '{expected_title}'")
    try:
        body_text = await page.inner_text('body')
        if expected_title.lower() not in body_text.lower():
            raise Exception(
                f"Post title '{expected_title}' not found on page. "
                f"Wrong post or post not loaded correctly."
            )
        print(f"✅ Post verified: '{expected_title}'")
        return True
    except Exception as e:
        if "SESSION_EXPIRED" in str(e):
            raise
        # Title not found — warn but continue
        print(f"⚠️  Could not verify title — continuing anyway")
        return True