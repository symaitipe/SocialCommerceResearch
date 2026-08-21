import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'comments.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Posts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            facebook_url        TEXT UNIQUE NOT NULL,
            title               TEXT,
            last_fetched_at     TIMESTAMP,
            last_sync_new_count INTEGER DEFAULT 0,
            total_comments      INTEGER DEFAULT 0,
            created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Comments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id              INTEGER,
            facebook_comment_id  TEXT,
            facebook_comment_url TEXT,
            commenter_name       TEXT,
            commenter_fb_id      TEXT,
            parent_comment_id    TEXT,
            text                 TEXT NOT NULL,
            language             TEXT,
            intent               TEXT,
            sentiment            TEXT,
            confidence           TEXT DEFAULT 'none',
            route                TEXT DEFAULT 'ai_only',
            priority_score       INTEGER DEFAULT 0,
            emoji_only           BOOLEAN DEFAULT 0,
            ai_assisted          BOOLEAN DEFAULT 0,
            is_order_request     BOOLEAN DEFAULT 0,
            status               TEXT DEFAULT 'unread',
            product_category     TEXT DEFAULT 'general',
            created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(id),
            UNIQUE(post_id, facebook_comment_id)
        )
    ''')

    # Orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id                       INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id                  INTEGER,
            comment_id               INTEGER,
            order_request_comment_id TEXT,
            commenter_name           TEXT,
            commenter_fb_id          TEXT,
            raw_details_text         TEXT,
            facebook_comment_url     TEXT,
            lead_status              TEXT DEFAULT 'pending',
            confirmed_at             TIMESTAMP,
            notes                    TEXT,
            created_at               TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at               TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id)    REFERENCES posts(id),
            FOREIGN KEY (comment_id) REFERENCES comments(id)
        )
    ''')

    conn.commit()
    conn.close()

# ─── Post Functions ────────────────────────────────────────────

def create_or_get_post(facebook_url: str, title: str = None) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM posts WHERE facebook_url = ?', (facebook_url,))
    post = cursor.fetchone()
    if post:
        conn.close()
        return dict(post)
    cursor.execute('''
        INSERT INTO posts (facebook_url, title, created_at)
        VALUES (?, ?, ?)
    ''', (facebook_url, title or facebook_url, datetime.now().isoformat()))
    post_id = cursor.lastrowid
    conn.commit()
    cursor.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
    post = cursor.fetchone()
    conn.close()
    return dict(post)

def get_all_posts():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            p.*,
            COUNT(c.id) as total_comments,
            SUM(CASE WHEN c.status = 'unread'           THEN 1 ELSE 0 END) as unread_count,
            SUM(CASE WHEN c.status = 'read_not_replied' THEN 1 ELSE 0 END) as not_replied_count,
            SUM(CASE WHEN c.status = 'replied'          THEN 1 ELSE 0 END) as replied_count
        FROM posts p
        LEFT JOIN comments c ON c.post_id = p.id
        GROUP BY p.id
        ORDER BY p.created_at DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_post_by_id(post_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            p.*,
            COUNT(c.id) as total_comments,
            SUM(CASE WHEN c.status = 'unread'           THEN 1 ELSE 0 END) as unread_count,
            SUM(CASE WHEN c.status = 'read_not_replied' THEN 1 ELSE 0 END) as not_replied_count,
            SUM(CASE WHEN c.status = 'replied'          THEN 1 ELSE 0 END) as replied_count
        FROM posts p
        LEFT JOIN comments c ON c.post_id = p.id
        WHERE p.id = ?
        GROUP BY p.id
    ''', (post_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_post_fetched(post_id: int, total: int, new_count: int = 0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE posts
        SET last_fetched_at     = ?,
            total_comments      = ?,
            last_sync_new_count = ?
        WHERE id = ?
    ''', (datetime.now().isoformat(), total, new_count, post_id))
    conn.commit()
    conn.close()

# ─── Comment Functions ─────────────────────────────────────────

def comment_exists(post_id: int, facebook_comment_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id FROM comments
        WHERE post_id = ? AND facebook_comment_id = ?
    ''', (post_id, facebook_comment_id))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def is_order_request_comment(facebook_comment_id: str) -> bool:
    """Check if a comment ID belongs to a seller's order request template."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id FROM comments
        WHERE facebook_comment_id = ? AND is_order_request = 1
    ''', (facebook_comment_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def save_comment(result: dict, product_category: str = 'general',
                 post_id: int = None, facebook_comment_id: str = None,
                 facebook_comment_url: str = None, commenter_name: str = None,
                 commenter_fb_id: str = None, parent_comment_id: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO comments
        (post_id, facebook_comment_id, facebook_comment_url,
         commenter_name, commenter_fb_id, parent_comment_id,
         text, language, intent, sentiment,
         confidence, route, priority_score,
         emoji_only, ai_assisted, status, product_category,
         created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'unread', ?, ?, ?)
    ''', (
        post_id,
        facebook_comment_id,
        facebook_comment_url,
        commenter_name,
        commenter_fb_id,
        parent_comment_id,
        result['text'],
        result['language'],
        result['intent'],
        result['sentiment'],
        result.get('confidence', 'none'),
        result.get('route', 'ai_only'),
        result.get('priority_score', 0),
        result.get('emoji_only', False),
        result.get('ai_assisted', False),
        product_category,
        datetime.now().isoformat(),
        datetime.now().isoformat()
    ))
    comment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return comment_id

def mark_comment_as_order_request(comment_id: int):
    """Mark a comment as an order request template sent by seller."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE comments
        SET is_order_request = 1, updated_at = ?
        WHERE id = ?
    ''', (datetime.now().isoformat(), comment_id))
    conn.commit()
    conn.close()

def get_comments_by_post(post_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM comments
        WHERE post_id = ?
        ORDER BY
            CASE status
                WHEN 'unread'           THEN 1
                WHEN 'read_not_replied' THEN 2
                WHEN 'replied'          THEN 3
            END,
            priority_score DESC,
            created_at DESC
    ''', (post_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_comments_by_post_and_intent(post_id: int, intent: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM comments
        WHERE post_id = ? AND intent = ?
        ORDER BY
            CASE status
                WHEN 'unread'           THEN 1
                WHEN 'read_not_replied' THEN 2
                WHEN 'replied'          THEN 3
            END,
            created_at DESC
    ''', (post_id, intent))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_summary_by_post(post_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT intent, COUNT(*) as count FROM comments WHERE post_id = ? GROUP BY intent', (post_id,))
    intent_counts = {row['intent']: row['count'] for row in cursor.fetchall()}
    cursor.execute('SELECT sentiment, COUNT(*) as count FROM comments WHERE post_id = ? GROUP BY sentiment', (post_id,))
    sentiment_counts = {row['sentiment']: row['count'] for row in cursor.fetchall()}
    cursor.execute('SELECT language, COUNT(*) as count FROM comments WHERE post_id = ? GROUP BY language', (post_id,))
    language_counts = {row['language']: row['count'] for row in cursor.fetchall()}
    cursor.execute('SELECT status, COUNT(*) as count FROM comments WHERE post_id = ? GROUP BY status', (post_id,))
    status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
    cursor.execute('SELECT COUNT(*) as total FROM comments WHERE post_id = ?', (post_id,))
    total = cursor.fetchone()['total']
    conn.close()
    return {
        'total':            total,
        'intent_counts':    intent_counts,
        'sentiment_counts': sentiment_counts,
        'language_counts':  language_counts,
        'status_counts':    status_counts
    }


def get_activity_by_day(post_id: int, days: int = 7):
    """Comment counts per day for the last N days, for the activity chart."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DATE(created_at) as day, COUNT(*) as count
        FROM comments
        WHERE post_id = ?
          AND created_at >= DATE('now', ?)
        GROUP BY DATE(created_at)
        ORDER BY day ASC
    ''', (post_id, f'-{days} days'))
    rows = cursor.fetchall()
    conn.close()
    return [{'day': row['day'], 'count': row['count']} for row in rows]


def get_facebook_comment_id(comment_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT facebook_comment_id FROM comments WHERE id = ?', (comment_id,))
    row = cursor.fetchone()
    conn.close()
    return row['facebook_comment_id'] if row else None


def update_comment_status(comment_id: int, status: str):
    allowed = ['unread', 'read_not_replied', 'replied']
    if status not in allowed:
        return False
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE comments
        SET status = ?, updated_at = ?
        WHERE id = ?
    ''', (status, datetime.now().isoformat(), comment_id))
    conn.commit()
    conn.close()
    return True

def mark_post_comments_read(post_id: int):
    """Mark all unread comments in a post as read_not_replied."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE comments
        SET status = 'read_not_replied', updated_at = ?
        WHERE post_id = ? AND status = 'unread'
    ''', (datetime.now().isoformat(), post_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected


# ─── Order Functions ───────────────────────────────────────────

def save_order(post_id: int, comment_id: int, order_request_comment_id: str,
               commenter_name: str, commenter_fb_id: str,
               raw_details_text: str, facebook_comment_url: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO orders
        (post_id, comment_id, order_request_comment_id,
         commenter_name, commenter_fb_id, raw_details_text,
         facebook_comment_url, lead_status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
    ''', (
        post_id,
        comment_id,
        order_request_comment_id,
        commenter_name,
        commenter_fb_id,
        raw_details_text,
        facebook_comment_url,
        datetime.now().isoformat(),
        datetime.now().isoformat()
    ))
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return order_id

def get_orders_by_post(post_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM orders
        WHERE post_id = ?
        ORDER BY created_at DESC
    ''', (post_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_all_orders():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM orders ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_order_status(order_id: int, status: str, notes: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE orders
        SET lead_status = ?,
            notes       = COALESCE(?, notes),
            confirmed_at = CASE WHEN ? = 'confirmed' THEN ? ELSE confirmed_at END,
            updated_at  = ?
        WHERE id = ?
    ''', (status, notes, status, datetime.now().isoformat(),
          datetime.now().isoformat(), order_id))
    conn.commit()
    conn.close()

# ─── Backward compatibility ────────────────────────────────────

def get_all_comments():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM comments ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_comments_by_category(category: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM comments
        WHERE product_category = ?
        ORDER BY created_at DESC
    ''', (category,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_summary():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as total FROM comments')
    total = cursor.fetchone()['total']
    conn.close()
    return {'total': total}

def get_summary_by_category(category: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT intent, COUNT(*) as count FROM comments WHERE product_category = ? GROUP BY intent', (category,))
    intent_counts = {row['intent']: row['count'] for row in cursor.fetchall()}
    cursor.execute('SELECT sentiment, COUNT(*) as count FROM comments WHERE product_category = ? GROUP BY sentiment', (category,))
    sentiment_counts = {row['sentiment']: row['count'] for row in cursor.fetchall()}
    cursor.execute('SELECT status, COUNT(*) as count FROM comments WHERE product_category = ? GROUP BY status', (category,))
    status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
    cursor.execute('SELECT COUNT(*) as total FROM comments WHERE product_category = ?', (category,))
    total = cursor.fetchone()['total']
    conn.close()
    return {
        'total':            total,
        'intent_counts':    intent_counts,
        'sentiment_counts': sentiment_counts,
        'status_counts':    status_counts
    }

def get_comments_by_intent(intent: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM comments WHERE intent = ?', (intent,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]