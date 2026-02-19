from __future__ import annotations

import unittest

from app.security import is_client_allowed, is_ip_in_cidrs


class SecurityTests(unittest.TestCase):
    def test_ip_in_cidrs(self):
        self.assertTrue(is_ip_in_cidrs("100.75.10.2", ["100.64.0.0/10"]))
        self.assertFalse(is_ip_in_cidrs("192.168.1.10", ["100.64.0.0/10"]))

    def test_tailnet_only_denies_non_tailnet(self):
        allowed, reason = is_client_allowed(
            client_ip="192.168.0.10",
            security_cfg={"tailnet_only": True, "tailscale_cidrs": ["100.64.0.0/10"]},
            node_id=None,
        )
        self.assertFalse(allowed)
        self.assertIn("not in allowed", reason)

    def test_tailnet_only_allows_tailnet(self):
        allowed, reason = is_client_allowed(
            client_ip="100.80.1.5",
            security_cfg={"tailnet_only": True, "tailscale_cidrs": ["100.64.0.0/10"]},
            node_id=None,
        )
        self.assertTrue(allowed)
        self.assertEqual(reason, "allowed")

    def test_node_allowlist(self):
        allowed, _ = is_client_allowed(
            client_ip="100.80.1.5",
            security_cfg={
                "tailnet_only": True,
                "tailscale_cidrs": ["100.64.0.0/10"],
                "tailscale_node_allowlist": ["node-123"],
            },
            node_id="node-123",
        )
        self.assertTrue(allowed)

        denied, _ = is_client_allowed(
            client_ip="100.80.1.5",
            security_cfg={
                "tailnet_only": True,
                "tailscale_cidrs": ["100.64.0.0/10"],
                "tailscale_node_allowlist": ["node-123"],
            },
            node_id="node-999",
        )
        self.assertFalse(denied)


if __name__ == "__main__":
    unittest.main()
