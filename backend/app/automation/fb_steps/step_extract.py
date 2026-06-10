import asyncio
from app.automation.fb_locators import FBLocators

async def extract_comments(page, post_url: str) -> list:
    """
    Step 5: Extract all comments from the loaded page.
    For each comment element, extracts:
      - commenter_name
      - comment text
      - comment_id (from attribute or generated)
      - comment_url (direct link to comment)
    Returns list of comment dicts.
    """
    print("🔍 Extracting comments...")
    comments = []
    seen_ids = set()

    try:
        # Scroll down to ensure all comments are rendered
        for _ in range(3):
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(1)

        # Get all comment containers
        containers = FBLocators.all_comment_containers(page)
        count = await containers.count()
        print(f"   Found {count} comment containers")

        for i in range(count):
            try:
                comment_el = containers.nth(i)
                comment_data = await _extract_single_comment(
                    comment_el, post_url, seen_ids
                )
                if comment_data:
                    comments.append(comment_data)
                    seen_ids.add(comment_data['comment_id'])

            except Exception as e:
                print(f"   ⚠️  Skipped comment {i}: {str(e)}")
                continue

    except Exception as e:
        print(f"❌ Extraction error: {str(e)}")

    print(f"✅ Extracted {len(comments)} comments")
    return comments


async def _extract_single_comment(comment_el, post_url: str, seen_ids: set) -> dict:
    """
    Extract data from a single comment element.
    Returns dict or None if comment should be skipped.
    """
    # Get commenter name
    commenter_name = ""
    try:
        name_locator = FBLocators.commenter_name(comment_el)
        commenter_name = (await name_locator.inner_text()).strip()
    except Exception:
        pass

    # Get comment text
    comment_text = ""
    try:
        text_locator = FBLocators.comment_text(comment_el)
        comment_text = (await text_locator.inner_text()).strip()
    except Exception:
        pass

    # Skip if no text
    if not comment_text:
        return None

    # Skip very short meaningless text
    if len(comment_text) < 2:
        return None

    # Get comment ID from attribute
    comment_id = None
    try:
        comment_id = await comment_el.get_attribute(
            FBLocators.comment_id_attribute()
        )
    except Exception:
        pass

    # Generate ID if not found in DOM
    if not comment_id:
        comment_id = str(abs(hash(commenter_name + comment_text)))

    # Skip duplicates
    if comment_id in seen_ids:
        return None

    return {
        'comment_id':      comment_id,
        'commenter_name':  commenter_name,
        'text':            comment_text,
        'comment_url':     f"{post_url}&comment_id={comment_id}"
    }