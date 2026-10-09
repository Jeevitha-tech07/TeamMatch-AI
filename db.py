"""
db.py
Handles all SQLite storage for the Feedback Bot.
Feedback is stored WITHOUT any user-identifying information, so it is
genuinely anonymous by design (no username/email/session id is ever saved).
"""

import sqlite3
from datetime import datetime
from contextlib import contextmanager

DB_PATH = "feedback_bot.db"


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create tables if they don't already exist."""
    with get_conn() as conn:
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,          -- 'Class', 'Lab', 'Facility'
                subject TEXT,                    -- e.g. course name / lab name / facility name
                rating INTEGER,                  -- 1-5 stars
                comment TEXT,
                sentiment TEXT,                  -- 'Positive', 'Neutral', 'Negative'
                sentiment_score REAL,
                created_at TEXT
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS polls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                option_a TEXT NOT NULL,
                option_b TEXT NOT NULL,
                option_c TEXT,
                option_d TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS poll_votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                poll_id INTEGER NOT NULL,
                choice TEXT NOT NULL,
                created_at TEXT,
                FOREIGN KEY (poll_id) REFERENCES polls (id)
            )
        """)


# ---------- Feedback ----------

def add_feedback(category, subject, rating, comment, sentiment, sentiment_score):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO feedback (category, subject, rating, comment, sentiment, sentiment_score, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (category, subject, rating, comment, sentiment, sentiment_score,
             datetime.now().isoformat(timespec="seconds")),
        )


def get_all_feedback():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM feedback ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]


# ---------- Polls ----------

def create_poll(question, option_a, option_b, option_c=None, option_d=None):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO polls (question, option_a, option_b, option_c, option_d, is_active, created_at)
               VALUES (?, ?, ?, ?, ?, 1, ?)""",
            (question, option_a, option_b, option_c, option_d,
             datetime.now().isoformat(timespec="seconds")),
        )


def get_active_polls():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM polls WHERE is_active = 1 ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]


def get_all_polls():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM polls ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]


def close_poll(poll_id):
    with get_conn() as conn:
        conn.execute("UPDATE polls SET is_active = 0 WHERE id = ?", (poll_id,))


def cast_vote(poll_id, choice):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO poll_votes (poll_id, choice, created_at) VALUES (?, ?, ?)",
            (poll_id, choice, datetime.now().isoformat(timespec="seconds")),
        )


def get_poll_results(poll_id):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT choice, COUNT(*) as votes FROM poll_votes WHERE poll_id = ? GROUP BY choice",
            (poll_id,),
        ).fetchall()
        return {r["choice"]: r["votes"] for r in rows}
