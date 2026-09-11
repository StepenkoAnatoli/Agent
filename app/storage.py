"""SQLite storage for conversations, messages and settings-safe persistence."""

import json
import sqlite3
import threading
import time
import uuid

from config import DB_FILE, DATA_DIR

_lock = threading.RLock()
_conn = None


def _db() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(str(DB_FILE), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT DEFAULT 'New chat',
                created_at REAL,
                updated_at REAL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conv_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL DEFAULT '',
                meta TEXT NOT NULL DEFAULT '{}',
                created_at REAL
            );
            CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conv_id);
            """
        )
        _conn.commit()
    return _conn


def now() -> float:
    return time.time()


def create_conversation(title: str = "New chat") -> dict:
    cid = uuid.uuid4().hex[:16]
    t = now()
    with _lock:
        _db().execute(
            "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?,?,?,?)",
            (cid, title, t, t),
        )
        _db().commit()
    return {"id": cid, "title": title, "updated_at": t}


def list_conversations() -> list:
    with _lock:
        rows = _db().execute(
            "SELECT id, title, updated_at FROM conversations ORDER BY updated_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_conversation(cid: str) -> dict | None:
    with _lock:
        row = _db().execute(
            "SELECT id, title, updated_at FROM conversations WHERE id=?", (cid,)
        ).fetchone()
    return dict(row) if row else None


def rename_conversation(cid: str, title: str) -> None:
    with _lock:
        _db().execute("UPDATE conversations SET title=? WHERE id=?", (title, cid))
        _db().commit()


def touch_conversation(cid: str) -> None:
    with _lock:
        _db().execute("UPDATE conversations SET updated_at=? WHERE id=?", (now(), cid))
        _db().commit()


def delete_conversation(cid: str) -> None:
    with _lock:
        _db().execute("DELETE FROM messages WHERE conv_id=?", (cid,))
        _db().execute("DELETE FROM conversations WHERE id=?", (cid,))
        _db().commit()


def add_message(cid: str, role: str, content: str, meta: dict | None = None) -> int:
    t = now()
    with _lock:
        cur = _db().execute(
            "INSERT INTO messages (conv_id, role, content, meta, created_at) VALUES (?,?,?,?,?)",
            (cid, role, content, json.dumps(meta or {}, ensure_ascii=False), t),
        )
        _db().execute("UPDATE conversations SET updated_at=? WHERE id=?", (t, cid))
        _db().commit()
        return cur.lastrowid


def get_messages(cid: str) -> list:
    with _lock:
        rows = _db().execute(
            "SELECT id, conv_id, role, content, meta, created_at FROM messages WHERE conv_id=? ORDER BY id",
            (cid,),
        ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        try:
            d["meta"] = json.loads(d["meta"])
        except Exception:
            d["meta"] = {}
        out.append(d)
    return out


def model_history(cid: str) -> list:
    """History in canonical form for the provider, excluding the last user turn if told to."""
    msgs = get_messages(cid)
    return [
        {
            "role": m["role"],
            "content": m["content"],
            "tool_calls": (m.get("meta") or {}).get("tool_calls", []),
            "tool_call_id": (m.get("meta") or {}).get("tool_call_id", ""),
        }
        for m in msgs
    ]


def set_first_title(cid: str, first_user_text: str) -> None:
    title = " ".join(first_user_text.split())[:60] or "New chat"
    with _lock:
        row = _db().execute(
            "SELECT COUNT(*) AS n FROM messages WHERE conv_id=?", (cid,)
        ).fetchone()
        if row["n"] <= 2:
            # Inline update (not rename_conversation) — the lock is already held.
            _db().execute("UPDATE conversations SET title=? WHERE id=?", (title, cid))
            _db().commit()
