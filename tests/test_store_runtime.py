from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.store import MemoryStore


class StoreRuntimeTests(unittest.TestCase):
    def test_audit_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "memory.db"
            store = MemoryStore(db)
            store.log_audit("a", "x", {"k": 1}, "ok")
            store.log_audit("b", "y", {"k": 2}, "ok")
            out = store.verify_audit_chain()
            self.assertTrue(out["ok"])

    def test_sessions_jobs_webhooks(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "memory.db"
            store = MemoryStore(db)
            store.create_session("s1", "Session 1")
            self.assertTrue(any(s["session_id"] == "s1" for s in store.list_sessions()))

            store.upsert_job("j1", "job", "0 * * * * *", True, {"kind": "heartbeat"})
            self.assertEqual(len(store.list_jobs()), 1)

            store.record_webhook("manual", {"x": 1})
            self.assertEqual(len(store.recent_webhooks()), 1)


if __name__ == "__main__":
    unittest.main()
