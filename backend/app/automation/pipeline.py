import asyncio
from concurrent.futures import ThreadPoolExecutor
from app.automation.fb_extractor import run_extraction_sync
from app.database import (
    comment_exists,
    save_comment,
    update_post_fetched
)
from app.rules.language_detector import detect_language
from app.rules.intent_classifier import classify_intent
from app.rules.sentiment_analyzer import analyze_sentiment
from app.rules.emoji_analyzer import has_only_emojis

async def run_pipeline(post_id: int, facebook_url: str, post_title: str = ""):
    print(f"\n🚀 Pipeline started for post {post_id}")
    print(f"📎 URL: {facebook_url}")
    print(f"📝 Title: {post_title}")

    # Step 1: Run extraction in separate thread
    print("⏳ Starting Facebook extraction...")
    try:
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            raw_comments = await loop.run_in_executor(
                pool,
                run_extraction_sync,
                facebook_url,
                post_title
            )
    except Exception as e:
        print(f"❌ Extraction failed: {str(e)}")
        return

    if not raw_comments:
        print("❌ No comments extracted")
        return

    print(f"✅ Extracted {len(raw_comments)} raw comments")

    # Step 2: Incremental processing
    new_count     = 0
    skipped_count = 0

    for raw in raw_comments:
        fb_comment_id = raw.get('comment_id')

        # Skip if already exists — incremental pipeline
        if fb_comment_id and comment_exists(post_id, fb_comment_id):
            skipped_count += 1
            continue

        text = raw.get('text', '').strip()
        if not text:
            continue

        # Classify
        language    = detect_language(text)
        intent      = classify_intent(text, language)
        sentiment   = analyze_sentiment(text, language)
        emoji_only  = has_only_emojis(text)
        ai_assisted = False

        if intent == 'general':
            from app.rules.ai_fallback import ai_fallback
            fallback    = await ai_fallback(text, language)
            intent      = fallback.get('intent', 'general')
            sentiment   = fallback.get('sentiment', sentiment)
            ai_assisted = fallback.get('ai_assisted', False)

        result = {
            'text':        text,
            'language':    language,
            'intent':      intent,
            'sentiment':   sentiment,
            'emoji_only':  emoji_only,
            'ai_assisted': ai_assisted
        }

        save_comment(
            result=result,
            post_id=post_id,
            facebook_comment_id=fb_comment_id,
            facebook_comment_url=raw.get('comment_url'),
            commenter_name=raw.get('commenter_name'),
            product_category='general'
        )
        new_count += 1

    # Update post stats
    update_post_fetched(post_id, len(raw_comments))

    print(f"\n📊 Pipeline complete:")
    print(f"   ✅ New comments processed: {new_count}")
    print(f"   ⏭️  Skipped (already exist): {skipped_count}")
    print(f"   📦 Total extracted: {len(raw_comments)}")