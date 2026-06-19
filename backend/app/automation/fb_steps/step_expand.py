import random
import asyncio

async def expand_all_comments(page, max_scroll_attempts: int = 50):
    """
    Scrolls the comments section repeatedly until no new comments load.
    Uses human-like randomized timing to reduce bot-detection risk.
    Customer top-level comments only — does not expand seller reply threads.
    """
    print("📜 Loading all comments via scroll...")

    previous_count = 0
    stable_rounds = 0
    attempts = 0

    while attempts < max_scroll_attempts and stable_rounds < 3:
        # Scroll by a randomized distance — not always straight to the bottom
        scroll_amount = random.randint(600, 1400)
        await page.evaluate(f'window.scrollBy(0, {scroll_amount})')

        # Randomized human-like wait between scrolls
        wait_time = random.uniform(1.2, 2.8)
        await asyncio.sleep(wait_time)

        # Occasionally pause longer, like a human reading comments
        if attempts > 0 and attempts % 5 == 0:
            reading_pause = random.uniform(2.5, 5.0)
            await asyncio.sleep(reading_pause)

        # Count current top-level comments
        current_elements = await page.query_selector_all('[aria-label*="Comment by"]')
        current_count = len(current_elements)

        if current_count == previous_count:
            stable_rounds += 1
        else:
            stable_rounds = 0
            print(f"   Loaded {current_count} comments so far...")

        previous_count = current_count
        attempts += 1

    print(f"✅ Comment loading stable at {previous_count} comments ({attempts} scroll attempts)")
    return previous_count