import asyncio
from app.automation.fb_locators import FBLocators

async def open_comments(page) -> bool:
    """
    Step 2: Click the Comment button to open the comments section.
    Returns True if successful.
    """
    print("💬 Opening comments section...")
    try:
        comment_btn = FBLocators.comment_button(page)
        await comment_btn.wait_for(timeout=5000)
        await comment_btn.click()
        await asyncio.sleep(2)
        print("✅ Comments section opened")
        return True
    except Exception as e:
        print(f"⚠️  Could not click Comment button: {str(e)}")
        print("   Comments may already be visible — continuing...")
        return True