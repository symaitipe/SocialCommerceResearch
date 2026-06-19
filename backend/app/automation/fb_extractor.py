import asyncio
import os
import concurrent.futures
from playwright.async_api import async_playwright
from dotenv import load_dotenv
from app.automation.fb_locators import FBLocators
from app.automation.fb_steps.step_load_post import load_post
from app.automation.fb_steps.step_open_comments import open_comments
from app.automation.fb_steps.step_select_all import select_all_comments
from app.automation.fb_steps.step_expand import expand_all_comments
from app.automation.fb_steps.step_extract import extract_comments

load_dotenv()

FB_EMAIL     = os.getenv("FB_EMAIL")
FB_PASSWORD  = os.getenv("FB_PASSWORD")
SESSION_PATH = os.path.join(os.path.dirname(__file__), '../../../fb_session')
SESSION_FILE = os.path.join(SESSION_PATH, 'state.json')


async def run_extraction(post_url: str, post_title: str) -> list:
    """
    Main entry point for Facebook comment extraction.
    Coordinates all steps in order.
    """
    comments = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=300
        )

        if os.path.exists(SESSION_FILE):
            context = await browser.new_context(storage_state=SESSION_FILE)
            print("✅ Using saved session")
        else:
            context = await browser.new_context()
            print("🔐 No saved session — logging in...")
            await _login(context)

        page = await context.new_page()

        try:
            try:
                await load_post(page, post_url, post_title)
            except Exception as e:
                if "SESSION_EXPIRED" in str(e):
                    print("🔄 Session expired — logging in again...")
                    await _login(context)
                    await load_post(page, post_url, post_title)
                else:
                    raise

            await open_comments(page)
            await select_all_comments(page)
            await expand_all_comments(page)
            comments = await extract_comments(page, post_url)

            os.makedirs(SESSION_PATH, exist_ok=True)
            await context.storage_state(path=SESSION_FILE)
            print("💾 Session saved")

        except Exception as e:
            print(f"❌ Extraction failed: {str(e)}")

        finally:
            await browser.close()

    return comments


async def _login(context):
    """Handle Facebook login with manual CAPTCHA support"""
    page = await context.new_page()

    print("🌐 Opening Facebook login...")
    await page.goto('https://www.facebook.com/login', timeout=60000)
    await asyncio.sleep(3)

    try:
        await FBLocators.login_email(page).fill(FB_EMAIL, timeout=30000)
        await FBLocators.login_password(page).fill(FB_PASSWORD, timeout=30000)
        await FBLocators.login_button(page).click(timeout=30000)
    except Exception as e:
        print(f"⚠️  Auto-fill failed ({str(e)}) — please log in manually in the browser.")

    await asyncio.sleep(2)

    print("\n" + "="*50)
    print("⚠️  ACTION REQUIRED:")
    print("   Log in manually if not already done.")
    print("   If CAPTCHA or 2FA appeared — complete it now")
    print("   Once fully logged in, come back here and")
    print("   press Enter to continue...")
    print("="*50)
    await asyncio.get_event_loop().run_in_executor(None, input)

    await page.close()


def run_extraction_sync(post_url: str, post_title: str) -> list:
    """
    Runs async extraction in a separate thread with its own event loop.
    Solves Windows asyncio subprocess limitation.
    """
    def _run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(run_extraction(post_url, post_title))
        finally:
            loop.close()

    with concurrent.futures.ThreadPoolExecutor() as pool:
        future = pool.submit(_run)
        return future.result()