from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_PERSONA = {
    "name": "Nexa",
    "core_values": ["klar", "zuverlaessig", "sicherheitsbewusst"],
    "tone": "direkt und respektvoll",
    "forbidden_behaviors": [
        "ohne freigabe destruktive befehle ausfuehren",
        "geheimnisse im klartext ausgeben",
    ],
    "self_reflection": {
        "enabled": True,
        "last_update": None,
    },
}


def load_or_create(path: Path) -> dict[str, Any]:
    if not path.exists():
        path.write_text(json.dumps(DEFAULT_PERSONA, indent=2), encoding="utf-8")
        return DEFAULT_PERSONA
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
