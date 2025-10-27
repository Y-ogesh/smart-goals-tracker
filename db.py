# db.py — SQLite helpers

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from datetime import date, timedelta
from typing import List, Dict, Optional

DB_PATH = Path(__file__).parent / "data.sqlite3"

@contextmanager
def _conn():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        yield conn

def init_db():
    with _conn() as conn:
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            deadline TEXT,
            created_at TEXT DEFAULT (DATE('now'))
        );""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_id INTEGER NOT NULL,
            order_index INTEGER DEFAULT 0,
            title TEXT NOT NULL,
            detail TEXT,
            metric TEXT,
            duration_min INTEGER,
            why TEXT,
            due_date TEXT,
            done INTEGER DEFAULT 0,
            FOREIGN KEY(goal_id) REFERENCES goals(id) ON DELETE CASCADE
        );""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_id INTEGER NOT NULL,
            day TEXT NOT NULL,
            UNIQUE(goal_id, day),
            FOREIGN KEY(goal_id) REFERENCES goals(id) ON DELETE CASCADE
        );""")
        conn.commit()

def create_goal(title: str, deadline: Optional[str]) -> int:
    with _conn() as conn:
        cur = conn.execute("INSERT INTO goals(title, deadline) VALUES (?,?)", (title, deadline))
        conn.commit()
        return cur.lastrowid

def list_goals() -> List[Dict]:
    with _conn() as conn:
        rows = conn.execute("SELECT id, title, deadline, created_at FROM goals ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]

def delete_goal(goal_id: int):
    with _conn() as conn:
        conn.execute("DELETE FROM goals WHERE id=?", (goal_id,))
        conn.execute("DELETE FROM steps WHERE goal_id=?", (goal_id,))
        conn.execute("DELETE FROM checkins WHERE goal_id=?", (goal_id,))
        conn.commit()

def add_steps(goal_id: int, steps: List[Dict], replace=False):
    with _conn() as conn:
        if replace:
            conn.execute("DELETE FROM steps WHERE goal_id=?", (goal_id,))
        for s in steps:
            conn.execute("""
            INSERT INTO steps(goal_id, order_index, title, detail, metric, duration_min, why, due_date, done)
            VALUES (?,?,?,?,?,?,?,?,?)
            """, (
                goal_id,
                int(s.get("order_index", 0)),
                s.get("title","").strip(),
                (s.get("detail") or "").strip(),
                (s.get("metric") or "").strip(),
                int(s["duration_min"]) if s.get("duration_min") not in (None,"") else None,
                (s.get("why") or "").strip(),
                s.get("due_date"),
                int(s.get("done",0))
            ))
        conn.commit()

def get_steps(goal_id: int) -> List[Dict]:
    with _conn() as conn:
        rows = conn.execute("""
        SELECT id, goal_id, order_index, title, detail, metric, duration_min, why, due_date, done
        FROM steps WHERE goal_id=?
        ORDER BY order_index, COALESCE(due_date, '9999-12-31') ASC
        """, (goal_id,)).fetchall()
        return [dict(r) for r in rows]

def update_step(step_id: int, goal_id: int, order_index: int, title: str, detail: str,
                metric: str, duration_min: Optional[int], why: str, due_date: Optional[str], done: int):
    with _conn() as conn:
        # Upsert-like behavior: if id missing, insert
        if step_id is None:
            conn.execute("""
            INSERT INTO steps(goal_id, order_index, title, detail, metric, duration_min, why, due_date, done)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (goal_id, order_index, title, detail, metric, duration_min, why, due_date, done))
        else:
            conn.execute("""
            UPDATE steps
               SET order_index=?, title=?, detail=?, metric=?, duration_min=?, why=?, due_date=?, done=?
             WHERE id=? AND goal_id=?""",
            (order_index, title, detail, metric, duration_min, why, due_date, done, step_id, goal_id))
        conn.commit()

# --- Check-ins / streaks ---
def checkin(goal_id: int, day: str):
    with _conn() as conn:
        conn.execute("INSERT OR IGNORE INTO checkins(goal_id, day) VALUES (?,?)", (goal_id, day))
        conn.commit()

def delete_checkin(goal_id: int, day: str):
    with _conn() as conn:
        conn.execute("DELETE FROM checkins WHERE goal_id=? AND day=?", (goal_id, day))
        conn.commit()

def get_checkins(goal_id: int) -> List[Dict]:
    with _conn() as conn:
        rows = conn.execute("SELECT day FROM checkins WHERE goal_id=? ORDER BY day ASC", (goal_id,)).fetchall()
        return [{"day": r["day"]} for r in rows]

def compute_streak_strict(goal_id: int) -> int:
    """Counts consecutive days up to today only (miss today => streak 0)."""
    days = [r["day"] for r in get_checkins(goal_id)]
    if not days:
        return 0
    s = set(days)
    cur = date.today()
    if cur.isoformat() not in s:
        return 0
    streak = 0
    while cur.isoformat() in s:
        streak += 1
        cur = cur - timedelta(days=1)
    return streak

def compute_streak_friendly(goal_id: int) -> int:
    """Allows yesterday as anchor if today is missing."""
    days = [r["day"] for r in get_checkins(goal_id)]
    if not days:
        return 0
    s = set(days)
    today = date.today()
    anchor = today if today.isoformat() in s else (today - timedelta(days=1) if (today - timedelta(days=1)).isoformat() in s else None)
    if not anchor:
        return 0
    streak = 0
    cur = anchor
    while cur.isoformat() in s:
        streak += 1
        cur = cur - timedelta(days=1)
    return streak
