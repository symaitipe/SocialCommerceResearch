import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'comments.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Posts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            facebook_url TEXT UNIQUE NOT NULL,
            title TEXT,
            last_fetched_at TIMESTAMP,
            total_comments INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Comments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            facebook_comment_id TEXT,
            facebook_comment_url TEXT,
            commenter_name TEXT,
            text TEXT NOT NULL,
            language TEXT,
            intent TEXT,
            sentiment TEXT,
            emoji_only BOOLEAN DEFAULT 0,
            ai_assisted BOOLEAN DEFAULT 0,
            status TEXT DEFAULT 'new',
            product_category TEXT DEFAULT 'general',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(id),
            UNIQUE(post_id, facebook_comment_id)
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
        SELECT p.*,
            COUNT(c.id) as total_comments,
            SUM(CASE WHEN c.status = 'new' THEN 1 ELSE 0 END) as new_count
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
    cursor.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_post_fetched(post_id: int, total: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE posts
        SET last_fetched_at = ?, total_comments = ?
        WHERE id = ?
    ''', (datetime.now().isoformat(), total, post_id))
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

def save_comment(result: dict, product_category: str = 'general',
                 post_id: int = None, facebook_comment_id: str = None,
                 facebook_comment_url: str = None, commenter_name: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO comments
        (post_id, facebook_comment_id, facebook_comment_url,
         commenter_name, text, language, intent, sentiment,
         emoji_only, ai_assisted, status, product_category,
         created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', ?, ?, ?)
    ''', (
        post_id,
        facebook_comment_id,
        facebook_comment_url,
        commenter_name,
        result['text'],
        result['language'],
        result['intent'],
        result['sentiment'],
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

def get_comments_by_post(post_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM comments
        WHERE post_id = ?
        ORDER BY
            CASE status
                WHEN 'new' THEN 1
                WHEN 'pending' THEN 2
                WHEN 'done' THEN 3
            END,
            created_at DESC
    ''', (post_id,))
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
        'total': total,
        'intent_counts': intent_counts,
        'sentiment_counts': sentiment_counts,
        'language_counts': language_counts,
        'status_counts': status_counts
    }

def update_comment_status(comment_id: int, status: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE comments
        SET status = ?, updated_at = ?
        WHERE id = ?
    ''', (status, datetime.now().isoformat(), comment_id))
    conn.commit()
    conn.close()

# ─── Keep old functions for backward compatibility ─────────────

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
        'total': total,
        'intent_counts': intent_counts,
        'sentiment_counts': sentiment_counts,
        'language_counts': language_counts if 'language_counts' in dir() else {},
        'status_counts': status_counts
    }

def get_comments_by_intent(intent: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM comments WHERE intent = ?', (intent,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]