import asyncio
from app.graph.fb_graph_fetcher import fetch_post_comments, extract_post_id_from_url
from app.rules.classifier import classify
from app.rules.ai_fallback import ai_fallback
from app.database import (
    comment_exists,
    save_comment,
    update_post_fetched
)


async def run_pipeline(post_id: int, facebook_url: str, post_title: str = ""):
    print(f"\n🚀 Pipeline started for post {post_id}")
    print(f"📎 URL: {facebook_url}")

    # Step 1: Extract FB post ID from URL
    fb_post_id = await extract_post_id_from_url(facebook_url)

    if not fb_post_id:
        print(f"❌ Could not extract Facebook post ID from URL: {facebook_url}")
        print("   Please use a direct post URL (e.g. facebook.com/page/posts/123)")
        return

    print(f"📌 Facebook post ID: {fb_post_id}")

    # Step 2: Fetch comments via Graph API
    print("⏳ Fetching comments from Graph API...")
    try:
        raw_comments = await fetch_post_comments(fb_post_id)
    except Exception as e:
        print(f"❌ Graph API fetch failed: {str(e)}")
        return

    if not raw_comments:
        print("❌ No comments returned from Graph API")
        return

    print(f"✅ Fetched {len(raw_comments)} comments")

    # Step 3: Incremental pipeline — classify only new comments
    new_count     = 0
    skipped_count = 0
    ai_count      = 0

    for raw in raw_comments:
        fb_comment_id = raw.get('comment_id')

        # Skip if already in DB — incremental pipeline
        if fb_comment_id and comment_exists(post_id, fb_comment_id):
            skipped_count += 1
            continue

        text = raw.get('text', '').strip()
        if not text:
            continue

        # Step 4: Classify using new hybrid engine
        result = classify(text)

        # Step 5: AI fallback based on evidence-based routing
        if result.route in ('ai_only', 'rules_ai_verify'):
            try:
                fallback    = await ai_fallback(text, result.language)
                if result.route == 'ai_only':
                    intent    = fallback.get('intent',    'general')
                    sentiment = fallback.get('sentiment', 'neutral')
                else:
                    intent    = _map_intent(result.primary_intent)
                    sentiment = fallback.get('sentiment', _map_sentiment(result.sentiment))
                ai_assisted = fallback.get('ai_assisted', False)
                ai_count   += 1
            except Exception as e:
                print(f"⚠️  AI fallback error: {str(e)}")
                intent      = _map_intent(result.primary_intent)
                sentiment   = _map_sentiment(result.sentiment)
                ai_assisted = False
        else:
            intent      = _map_intent(result.primary_intent)
            sentiment   = _map_sentiment(result.sentiment)
            ai_assisted = False

        # Step 6: Save to database
        comment_data = {
            'text':        text,
            'language':    result.language,
            'intent':      intent,
            'sentiment':   sentiment,
            'emoji_only':  result.language == 'emoji',
            'ai_assisted': ai_assisted,
        }

        save_comment(
            result=comment_data,
            post_id=post_id,
            facebook_comment_id=fb_comment_id,
            facebook_comment_url=raw.get('comment_url'),
            commenter_name=raw.get('commenter_name'),
            product_category='general'
        )
        new_count += 1

    # Step 7: Update post stats
    update_post_fetched(post_id, len(raw_comments))

    print(f"\n📊 Pipeline complete:")
    print(f"   ✅ New comments processed : {new_count}")
    print(f"   🤖 AI assisted            : {ai_count}")
    print(f"   ⏭️  Skipped (exist)        : {skipped_count}")
    print(f"   📦 Total fetched          : {len(raw_comments)}")


def _map_intent(intent: str | None) -> str:
    if not intent:
        return 'general'
    mapping = {
        'Purchase Intent':             'purchase_intent',
        'Product Inquiry':             'product_inquiry',
        'Price Inquiry':               'price_inquiry',
        'Delivery Inquiry':            'delivery_inquiry',
        'Location/Availability':       'location_availability',
        'Payment Method Inquiry':      'payment_method',
        'Order/Purchase Confirmation': 'order_confirmation',
        'Positive Feedback':           'positive_feedback',
        'Negative Feedback/Complaint': 'negative_feedback',
        'Noise/Off-topic':             'noise',
    }
    return mapping.get(intent, 'general')


def _map_sentiment(sentiment: str | None) -> str:
    if not sentiment:
        return 'neutral'
    return sentiment.lower()