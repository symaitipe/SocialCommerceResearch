import asyncio
from app.graph.fb_graph_fetcher import fetch_post_comments, extract_post_id_from_url
from app.rules.classifier import classify
from app.rules.ai_fallback import ai_fallback
from app.database import (
    comment_exists,
    save_comment,
    save_order,
    update_post_fetched,
    is_order_request_comment
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
    order_count   = 0

    for raw in raw_comments:
        fb_comment_id = raw.get('comment_id')

        # Skip if already in DB — incremental pipeline
        if fb_comment_id and comment_exists(post_id, fb_comment_id):
            skipped_count += 1
            continue

        text = raw.get('text', '').strip()
        if not text:
            continue

        parent_id = raw.get('parent_id')

        # Step 4: Check if this is a reply to an order request
        if parent_id and is_order_request_comment(parent_id):
            # This is customer's order detail reply
            # Hide it on Facebook to protect privacy
            try:
                from app.graph.fb_graph_fetcher import hide_comment
                hide_result = await hide_comment(fb_comment_id)
                if hide_result['success']:
                    print(f"🔒 Hidden order detail comment from: {raw.get('commenter_name')}")
                else:
                    print(f"⚠️  Could not hide comment: {hide_result.get('error')}")
            except Exception as e:
                print(f"⚠️  Hide comment error: {str(e)}")

            # Save as order_details intent
            comment_data = {
                'text':        text,
                'language':    'english',
                'intent':      'order_details',
                'confidence':  'high',
                'route':       'rules_only',
                'emoji_only':  False,
                'ai_assisted': False,
            }

            saved_id = save_comment(
                result=comment_data,
                post_id=post_id,
                facebook_comment_id=fb_comment_id,
                facebook_comment_url=raw.get('comment_url'),
                commenter_name=raw.get('commenter_name'),
                commenter_fb_id=raw.get('commenter_fb_id'),
                parent_comment_id=parent_id,
                product_category='general'
            )

            # Save to orders table
            save_order(
                post_id=post_id,
                comment_id=saved_id,
                order_request_comment_id=parent_id,
                commenter_name=raw.get('commenter_name', ''),
                commenter_fb_id=raw.get('commenter_fb_id', ''),
                raw_details_text=text,
                facebook_comment_url=raw.get('comment_url', '')
            )

            order_count += 1
            new_count   += 1
            continue

        # Step 5: Classify using new hybrid engine
        result = classify(text)

        # Step 6: AI fallback / verification based on routing
        if result.route in ("ai_only", "rules_ai_verify"):
            try:
                fallback = await ai_fallback(text, result.language)
                fallback_intent = fallback.get("intent")

                if result.route == "ai_only":
                    # Rule layer explicitly declined to decide.
                    intent = fallback_intent or "noise_off_topic"
                else:
                    # TRUE verification:
                    # let the AI return the final taxonomy label instead of
                    # calling AI and then ignoring its intent.
                    intent = fallback_intent or _map_intent(result.primary_intent)

                ai_assisted = fallback.get("ai_assisted", False)
                ai_count += 1

            except Exception as e:
                print(f"⚠️  AI fallback error: {str(e)}")
                # Fail safely to the rule guess only when one exists.
                intent = _map_intent(result.primary_intent)
                ai_assisted = False
        else:
            intent      = _map_intent(result.primary_intent)
            ai_assisted = False

        # Step 7: Save to database
        comment_data = {
            'text':        text,
            'language':    result.language,
            'intent':      intent,
            'confidence':  result.confidence,
            'route':       result.route,
            'emoji_only':  result.language == 'emoji',
            'ai_assisted': ai_assisted,
        }

        save_comment(
            result=comment_data,
            post_id=post_id,
            facebook_comment_id=fb_comment_id,
            facebook_comment_url=raw.get('comment_url'),
            commenter_name=raw.get('commenter_name'),
            commenter_fb_id=raw.get('commenter_fb_id'),
            parent_comment_id=parent_id,
            product_category='general'
        )
        new_count += 1

    # Step 8: Update post stats
    update_post_fetched(post_id, len(raw_comments), new_count)

    print(f"\n📊 Pipeline complete:")
    print(f"   ✅ New comments processed : {new_count}")
    print(f"   📦 Order details captured : {order_count}")
    print(f"   🤖 AI assisted            : {ai_count}")
    print(f"   ⏭️  Skipped (exist)        : {skipped_count}")
    print(f"   📦 Total fetched          : {len(raw_comments)}")


def _map_intent(intent: str | None) -> str:
    if not intent:
        return "noise_off_topic"

    mapping = {
        "Purchase Intent": "purchase_intent",
        "Product Inquiry": "product_inquiry",
        "Price Inquiry": "price_inquiry",
        "Price Complaint": "price_complaint",
        "Delivery Inquiry": "delivery_inquiry",
        "Location/Availability": "location_availability",
        "Payment Method Inquiry": "payment_method_inquiry",
        "Warranty/Service Inquiry": "warranty_service_inquiry",
        "Order/Purchase Confirmation": "order_purchase_confirmation",
        "Positive Feedback": "positive_feedback",
        "Negative Feedback/Complaint": "negative_feedback_complaint",
        "Suggestion": "suggestion",
        "Contact Request": "contact_request",
        "Noise/Off-topic": "noise_off_topic",
    }

    # If AI already returns the normalized API label, preserve it.
    normalized_values = set(mapping.values())
    if intent in normalized_values:
        return intent

    return mapping.get(intent, "noise_off_topic")