import asyncio
from app.automation.fb_locators import FBLocators

async def expand_all_comments(page, max_clicks: int = 30) -> int:
    """
    Step 4: Repeatedly click 'View more comments' to load all comments.
    Returns total number of expansion clicks performed.
    """
    print("📜 Expanding all comments...")
    clicks = 0

    while clicks < max_clicks:
        expanded = False

        # Try 'View more comments'
        try:
            btn = FBLocators.view_more_comments_button(page)
            is_visible = await btn.is_visible()
            if is_visible:
                await btn.click()
                await asyncio.sleep(2)
                clicks += 1
                expanded = True
                print(f"   Loaded more comments ({clicks})")
                continue
        except Exception:
            pass

        # Try 'View previous comments'
        try:
            btn = FBLocators.view_previous_comments_button(page)
            is_visible = await btn.is_visible()
            if is_visible:
                await btn.click()
                await asyncio.sleep(2)
                clicks += 1
                expanded = True
                print(f"   Loaded previous comments ({clicks})")
                continue
        except Exception:
            pass

        # No more buttons found
        if not expanded:
            break

    print(f"✅ Expansion complete — {clicks} loads performed")
    return clicks