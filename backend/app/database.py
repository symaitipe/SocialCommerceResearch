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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            language TEXT,
            intent TEXT,
            sentiment TEXT,
            emoji_only BOOLEAN DEFAULT 0,
            ai_assisted BOOLEAN DEFAULT 0,
            status TEXT DEFAULT 'new',
            product_category TEXT DEFAULT 'general',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_comment(result: dict, product_category: str = 'general'):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO comments 
        (text, language, intent, sentiment, emoji_only, ai_assisted, status, product_category, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, 'new', ?, ?, ?)
    ''', (
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

def get_all_comments():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM comments 
        ORDER BY 
            CASE status 
                WHEN 'new' THEN 1 
                WHEN 'pending' THEN 2 
                WHEN 'done' THEN 3 
            END,
            created_at DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

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

def get_comments_by_intent(intent: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM comments 
        WHERE intent = ?
        ORDER BY
            CASE status 
                WHEN 'new' THEN 1 
                WHEN 'pending' THEN 2 
                WHEN 'done' THEN 3 
            END,
            created_at DESC
    ''', (intent,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_summary():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT intent, COUNT(*) as count FROM comments GROUP BY intent')
    intent_counts = {row['intent']: row['count'] for row in cursor.fetchall()}

    cursor.execute('SELECT sentiment, COUNT(*) as count FROM comments GROUP BY sentiment')
    sentiment_counts = {row['sentiment']: row['count'] for row in cursor.fetchall()}

    cursor.execute('SELECT language, COUNT(*) as count FROM comments GROUP BY language')
    language_counts = {row['language']: row['count'] for row in cursor.fetchall()}

    cursor.execute('SELECT status, COUNT(*) as count FROM comments GROUP BY status')
    status_counts = {row['status']: row['count'] for row in cursor.fetchall()}

    cursor.execute('SELECT COUNT(*) as total FROM comments')
    total = cursor.fetchone()['total']

    conn.close()
    return {
        'total': total,
        'intent_counts': intent_counts,
        'sentiment_counts': sentiment_counts,
        'language_counts': language_counts,
        'status_counts': status_counts
    }


def get_comments_by_category(category: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM comments 
        WHERE product_category = ?
        ORDER BY
            CASE status 
                WHEN 'new' THEN 1 
                WHEN 'pending' THEN 2 
                WHEN 'done' THEN 3 
            END,
            created_at DESC
    ''', (category,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_summary_by_category(category: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT intent, COUNT(*) as count FROM comments WHERE product_category = ? GROUP BY intent', (category,))
    intent_counts = {row['intent']: row['count'] for row in cursor.fetchall()}

    cursor.execute('SELECT sentiment, COUNT(*) as count FROM comments WHERE product_category = ? GROUP BY sentiment', (category,))
    sentiment_counts = {row['sentiment']: row['count'] for row in cursor.fetchall()}

    cursor.execute('SELECT language, COUNT(*) as count FROM comments WHERE product_category = ? GROUP BY language', (category,))
    language_counts = {row['language']: row['count'] for row in cursor.fetchall()}

    cursor.execute('SELECT status, COUNT(*) as count FROM comments WHERE product_category = ? GROUP BY status', (category,))
    status_counts = {row['status']: row['count'] for row in cursor.fetchall()}

    cursor.execute('SELECT COUNT(*) as total FROM comments WHERE product_category = ?', (category,))
    total = cursor.fetchone()['total']

    conn.close()
    return {
        'total': total,
        'intent_counts': intent_counts,
        'sentiment_counts': sentiment_counts,
        'language_counts': language_counts,
        'status_counts': status_counts
    }