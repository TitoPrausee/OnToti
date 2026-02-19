from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class SecretsStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("{}", encoding="utf-8")
            self._lock_permissions()

    def _lock_permissions(self) -> None:
        try:
            os.chmod(self.path, 0o600)
        except Exception:
            pass

    def _load(self) -> dict[str, str]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items()}
        except Exception:
            pass
        return {}

    def _save(self, data: dict[str, str]) -> None:
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self._lock_permissions()

    def set_secret(self, key: str, value: str) -> None:
        data = self._load()
        data[key] = value
        self._save(data)

    def get_secret(self, key: str) -> str | None:
        return self._load().get(key)

    def has_secret(self, key: str) -> bool:
        val = self.get_secret(key)
        return bool(val)

    def set_many(self, payload: dict[str, str]) -> list[str]:
        data = self._load()
        changed: list[str] = []
        for key, value in payload.items():
            if value:
                data[key] = value
                changed.append(key)
        self._save(data)
        return changed

    def public_summary(self) -> dict[str, Any]:
        data = self._load()
        return {
            "keys": sorted(data.keys()),
            "count": len(data),
        }
