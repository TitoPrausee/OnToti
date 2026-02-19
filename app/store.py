from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


UTC = timezone.utc


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


@dataclass
class StorePaths:
    root: Path
    db: Path
    persona: Path
    style: Path
    skill_registry: Path


def default_paths(root: str = "data") -> StorePaths:
    root_path = Path(root)
    root_path.mkdir(parents=True, exist_ok=True)
    return StorePaths(
        root=root_path,
        db=root_path / "memory.db",
        persona=root_path / "persona.json",
        style=root_path / "style_profile.json",
        skill_registry=root_path / "skill_registry.json",
    )


class MemoryStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._migrate()

    def _migrate(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                confidence REAL NOT NULL,
                last_seen TEXT NOT NULL,
                ttl_days INTEGER NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS interaction_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_text TEXT NOT NULL,
                bot_text TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                payload TEXT NOT NULL,
                result TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def log_audit(self, actor: str, action: str, payload: dict[str, Any], result: str) -> None:
        self.conn.execute(
            "INSERT INTO audit_events(timestamp, actor, action, payload, result) VALUES(?,?,?,?,?)",
            (utc_now().isoformat(), actor, action, json.dumps(payload), result),
        )
        self.conn.commit()

    def record_interaction(self, session_id: str, user_text: str, bot_text: str | None = None) -> None:
        self.conn.execute(
            "INSERT INTO interaction_signals(session_id, user_text, bot_text, created_at) VALUES(?,?,?,?)",
            (session_id, user_text, bot_text, utc_now().isoformat()),
        )
        self.conn.commit()

    def recent_interactions(self, session_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        if session_id:
            rows = self.conn.execute(
                """
                SELECT id, session_id, user_text, bot_text, created_at
                FROM interaction_signals
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                """
                SELECT id, session_id, user_text, bot_text, created_at
                FROM interaction_signals
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def upsert_preference(self, key: str, value: str, confidence: float, ttl_days: int = 180) -> None:
        self.conn.execute(
            """
            INSERT INTO preferences(key, value, confidence, last_seen, ttl_days)
            VALUES(?,?,?,?,?)
            ON CONFLICT(key) DO UPDATE SET
                value=excluded.value,
                confidence=excluded.confidence,
                last_seen=excluded.last_seen,
                ttl_days=excluded.ttl_days
            """,
            (key, value, confidence, utc_now().isoformat(), ttl_days),
        )
        self.conn.commit()

    def relevant_preferences(self) -> list[dict[str, Any]]:
        rows = self.conn.execute("SELECT key, value, confidence, last_seen, ttl_days FROM preferences").fetchall()
        out: list[dict[str, Any]] = []
        for row in rows:
            last_seen = datetime.fromisoformat(row["last_seen"])
            expires = last_seen + timedelta(days=row["ttl_days"])
            if expires >= utc_now():
                out.append(dict(row))
        return out

    def recent_audit(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT id, timestamp, actor, action, payload, result FROM audit_events ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
