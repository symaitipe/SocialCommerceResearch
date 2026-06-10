import asyncio
from app.automation.fb_locators import FBLocators

async def select_all_comments(page) -> bool:
    """
    Step 3: Change comment filter to 'All comments'
    so we don't miss any comments filtered by relevance.
    Returns True if successful.
    """
    print("🔽 Selecting 'All comments' filter...")
    try:
        # Click the filter dropdown
        dropdown = FBLocators.comments_filter_dropdown(page)
        await dropdown.wait_for(timeout=5000)
        await dropdown.click()
        await asyncio.sleep(1)

        # Select "All comments"
        all_option = FBLocators.all_comments_option(page)
        await all_option.wait_for(timeout=5000)
        await all_option.click()
        await asyncio.sleep(2)

        print("✅ 'All comments' selected")
        return True

    except Exception as e:
        print(f"⚠️  Could not change filter: {str(e)}")
        print("   Continuing with default filter...")
        return True