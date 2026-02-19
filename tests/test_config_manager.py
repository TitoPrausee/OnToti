from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.config_manager import ConfigManager


class ConfigManagerTests(unittest.TestCase):
    def test_validate_minimal(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            mgr = ConfigManager(path)
            cfg = {
                "provider": {
                    "active": "openai",
                    "options": {"openai": {"base_url": "https://api.openai.com/v1", "model": "x"}},
                },
                "security": {
                    "allowed_paths": ["/tmp"],
                    "tailscale_cidrs": ["100.64.0.0/10"],
                    "tailscale_node_allowlist": [],
                },
                "agents": {"max_active": 3},
            }
            ok, _ = mgr.validate(cfg)
            self.assertTrue(ok)

    def test_validate_rejects_bad_types(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            mgr = ConfigManager(path)
            cfg = {
                "provider": {"active": "openai", "options": {"openai": {}}},
                "security": {"tailscale_cidrs": "100.64.0.0/10"},
            }
            ok, _ = mgr.validate(cfg)
            self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
