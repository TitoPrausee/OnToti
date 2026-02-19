from __future__ import annotations

import hashlib
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
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_active TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS scheduled_jobs (
                job_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                cron TEXT NOT NULL,
                enabled INTEGER NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS webhook_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                payload TEXT NOT NULL,
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

        cols = {r["name"] for r in cur.execute("PRAGMA table_info(audit_events)").fetchall()}
        if "prev_hash" not in cols:
            cur.execute("ALTER TABLE audit_events ADD COLUMN prev_hash TEXT")
        if "event_hash" not in cols:
            cur.execute("ALTER TABLE audit_events ADD COLUMN event_hash TEXT")

        self.conn.commit()

    def _compute_hash(self, timestamp: str, actor: str, action: str, payload: str, result: str, prev_hash: str) -> str:
        src = "|".join([timestamp, actor, action, payload, result, prev_hash])
        return hashlib.sha256(src.encode("utf-8")).hexdigest()

    def log_audit(self, actor: str, action: str, payload: dict[str, Any], result: str) -> None:
        timestamp = utc_now().isoformat()
        payload_raw = json.dumps(payload)

        row = self.conn.execute(
            "SELECT event_hash FROM audit_events ORDER BY id DESC LIMIT 1"
        ).fetchone()
        prev_hash = row["event_hash"] if row and row["event_hash"] else "GENESIS"
        event_hash = self._compute_hash(timestamp, actor, action, payload_raw, result, prev_hash)

        self.conn.execute(
            "INSERT INTO audit_events(timestamp, actor, action, payload, result, prev_hash, event_hash) VALUES(?,?,?,?,?,?,?)",
            (timestamp, actor, action, payload_raw, result, prev_hash, event_hash),
        )
        self.conn.commit()

    def verify_audit_chain(self) -> dict[str, Any]:
        rows = self.conn.execute(
            "SELECT id, timestamp, actor, action, payload, result, prev_hash, event_hash FROM audit_events ORDER BY id ASC"
        ).fetchall()
        prev = "GENESIS"
        for row in rows:
            calc = self._compute_hash(
                row["timestamp"], row["actor"], row["action"], row["payload"], row["result"], prev
            )
            if row["prev_hash"] != prev or row["event_hash"] != calc:
                return {"ok": False, "broken_at": row["id"]}
            prev = row["event_hash"]
        return {"ok": True, "count": len(rows)}

    def record_interaction(self, session_id: str, user_text: str, bot_text: str | None = None) -> None:
        self.conn.execute(
            "INSERT INTO interaction_signals(session_id, user_text, bot_text, created_at) VALUES(?,?,?,?)",
            (session_id, user_text, bot_text, utc_now().isoformat()),
        )
        self.touch_session(session_id)
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

    def create_session(self, session_id: str, display_name: str | None = None) -> dict[str, Any]:
        now = utc_now().isoformat()
        name = display_name or session_id
        self.conn.execute(
            "INSERT OR REPLACE INTO sessions(session_id, display_name, created_at, last_active) VALUES(?,?,COALESCE((SELECT created_at FROM sessions WHERE session_id=?),?),?)",
            (session_id, name, session_id, now, now),
        )
        self.conn.commit()
        return {"session_id": session_id, "display_name": name, "created_at": now, "last_active": now}

    def touch_session(self, session_id: str) -> None:
        now = utc_now().isoformat()
        self.conn.execute(
            "INSERT OR IGNORE INTO sessions(session_id, display_name, created_at, last_active) VALUES(?,?,?,?)",
            (session_id, session_id, now, now),
        )
        self.conn.execute("UPDATE sessions SET last_active=? WHERE session_id=?", (now, session_id))

    def list_sessions(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT session_id, display_name, created_at, last_active FROM sessions ORDER BY last_active DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def delete_session(self, session_id: str) -> None:
        self.conn.execute("DELETE FROM sessions WHERE session_id=?", (session_id,))
        self.conn.commit()

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
            "SELECT id, timestamp, actor, action, payload, result, prev_hash, event_hash FROM audit_events ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def upsert_job(self, job_id: str, name: str, cron: str, enabled: bool, payload: dict[str, Any]) -> None:
        now = utc_now().isoformat()
        self.conn.execute(
            """
            INSERT INTO scheduled_jobs(job_id, name, cron, enabled, payload, created_at, updated_at)
            VALUES(?,?,?,?,?,?,?)
            ON CONFLICT(job_id) DO UPDATE SET
                name=excluded.name,
                cron=excluded.cron,
                enabled=excluded.enabled,
                payload=excluded.payload,
                updated_at=excluded.updated_at
            """,
            (job_id, name, cron, 1 if enabled else 0, json.dumps(payload), now, now),
        )
        self.conn.commit()

    def list_jobs(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT job_id, name, cron, enabled, payload, created_at, updated_at FROM scheduled_jobs ORDER BY created_at DESC"
        ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["enabled"] = bool(d["enabled"])
            d["payload"] = json.loads(d["payload"])
            out.append(d)
        return out

    def delete_job(self, job_id: str) -> None:
        self.conn.execute("DELETE FROM scheduled_jobs WHERE job_id=?", (job_id,))
        self.conn.commit()

    def set_job_enabled(self, job_id: str, enabled: bool) -> None:
        self.conn.execute(
            "UPDATE scheduled_jobs SET enabled=?, updated_at=? WHERE job_id=?",
            (1 if enabled else 0, utc_now().isoformat(), job_id),
        )
        self.conn.commit()

    def record_webhook(self, source: str, payload: dict[str, Any]) -> None:
        self.conn.execute(
            "INSERT INTO webhook_events(source, payload, created_at) VALUES(?,?,?)",
            (source, json.dumps(payload), utc_now().isoformat()),
        )
        self.conn.commit()

    def recent_webhooks(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT id, source, payload, created_at FROM webhook_events ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["payload"] = json.loads(d["payload"])
            out.append(d)
        return out
