from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.message_bus import LocalMessageBus, create_message_bus
from app.orchestrator import Orchestrator
from app.provider import ProviderRouter
from app.secrets_store import SecretsStore
from app.store import MemoryStore, default_paths


class MessageBusTests(unittest.TestCase):
    def test_local_bus_publish_and_recent(self):
        bus = LocalMessageBus(max_messages=10)
        bus.publish("a", "b", "t-1", {"x": 1}, 4)
        recent = bus.recent(limit=5)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0]["sender_id"], "a")

    def test_factory_local(self):
        bus = create_message_bus({"bus": {"backend": "local", "max_messages": 20}})
        self.assertIsInstance(bus, LocalMessageBus)

    def test_pipeline_cycle_detection_helper(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config.json").write_text(
                '{"provider":{"active":"openai","options":{"openai":{"base_url":"http://localhost","model":"x"}}}}',
                encoding="utf-8",
            )
            paths = default_paths(str(root / "data"))
            store = MemoryStore(paths.db)
            secrets = SecretsStore(paths.root / "secrets.json")
            provider = ProviderRouter(root / "config.json", secrets)
            orchestrator = Orchestrator(store=store, paths=paths, provider=provider, config_path=root / "config.json", bus=LocalMessageBus())

            graph_cycle = {"s1": ["s2"], "s2": ["s1"]}
            graph_ok = {"s1": [], "s2": ["s1"]}
            self.assertTrue(orchestrator._has_cycle(graph_cycle))
            self.assertFalse(orchestrator._has_cycle(graph_ok))


if __name__ == "__main__":
    unittest.main()
