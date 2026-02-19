from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ConfigManager:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> dict[str, Any]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def validate(self, data: dict[str, Any]) -> tuple[bool, str]:
        if not isinstance(data, dict):
            return False, "config must be a JSON object"

        if "provider" not in data or not isinstance(data["provider"], dict):
            return False, "missing provider section"
        provider = data["provider"]
        if "active" not in provider or "options" not in provider:
            return False, "provider.active and provider.options are required"
        if provider["active"] not in provider["options"]:
            return False, "provider.active must exist in provider.options"

        if "agents" in data and not isinstance(data["agents"].get("max_active", 1), int):
            return False, "agents.max_active must be int"

        security = data.get("security", {})
        if security and not isinstance(security, dict):
            return False, "security must be an object"

        if "allowed_paths" in security and not isinstance(security["allowed_paths"], list):
            return False, "security.allowed_paths must be a list"
        if "tailscale_cidrs" in security and not isinstance(security["tailscale_cidrs"], list):
            return False, "security.tailscale_cidrs must be a list"
        if "tailscale_node_allowlist" in security and not isinstance(security["tailscale_node_allowlist"], list):
            return False, "security.tailscale_node_allowlist must be a list"

        return True, "ok"
