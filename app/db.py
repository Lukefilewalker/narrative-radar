import os
import sqlite3
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DATABASE_PATH", "data/narratives.db")


def connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    with connect() as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS category_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_date TEXT NOT NULL,
            category TEXT NOT NULL,
            count INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(snapshot_date, category)
        )
        """)

def save_item(source, title, url, summary="", published=""):
    seen_at = datetime.now(timezone.utc).isoformat()

    with connect() as con:
        cur = con.execute("""
        INSERT OR IGNORE INTO items
        (source, title, url, summary, published, seen_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (source, title, url, summary, published, seen_at))

        return cur.rowcount == 1

def get_recent_items(limit=100):
    with connect() as con:
        con.row_factory = sqlite3.Row
        rows = con.execute("""
        SELECT * FROM items
        ORDER BY seen_at DESC
        LIMIT ?
        """, (limit,)).fetchall()

    return [dict(row) for row in rows]

def get_items_since(hours=24):
    with connect() as con:
        con.row_factory = sqlite3.Row
        rows = con.execute("""
        SELECT *
        FROM items
        WHERE datetime(seen_at) >= datetime('now', ?)
        ORDER BY seen_at DESC
        """, (f"-{hours} hours",)).fetchall()

    return [dict(row) for row in rows]

def save_category_snapshot(snapshot_date, category_counts):
    created_at = datetime.now(timezone.utc).isoformat()

    with connect() as con:
        for category, count in category_counts:
            con.execute("""
            INSERT INTO category_snapshots
            (snapshot_date, category, count, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(snapshot_date, category)
            DO UPDATE SET
                count = excluded.count,
                created_at = excluded.created_at
            """, (snapshot_date, category, count, created_at))

def get_category_snapshot(snapshot_date):
    with connect() as con:
        con.row_factory = sqlite3.Row
        rows = con.execute("""
        SELECT category, count
        FROM category_snapshots
        WHERE snapshot_date = ?
        """, (snapshot_date,)).fetchall()

    return {row["category"]: row["count"] for row in rows}
