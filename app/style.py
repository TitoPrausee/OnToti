from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


DEFAULT_STYLE = {
    "formality": 0.5,
    "avg_sentence_length": 12.0,
    "emoji_usage": 0.0,
    "directness": 0.5,
    "language_hint": "de",
    "samples_seen": 0,
}


def load_or_create(path: Path) -> dict[str, Any]:
    if not path.exists():
        path.write_text(json.dumps(DEFAULT_STYLE, indent=2), encoding="utf-8")
        return DEFAULT_STYLE
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def analyze_text(text: str) -> dict[str, float | str]:
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    words = re.findall(r"\w+", text, flags=re.UNICODE)
    avg_sentence_length = (len(words) / len(sentences)) if sentences else float(len(words))

    emoji_count = len(re.findall(r"[\U0001F300-\U0001FAFF]", text))
    emoji_usage = emoji_count / max(len(words), 1)

    direct_words = sum(1 for w in words if w.lower() in {"mach", "tu", "jetzt", "direkt", "bitte"})
    directness = min(1.0, direct_words / max(len(words), 1) * 10)

    formal_words = sum(1 for w in words if w.lower() in {"bitte", "danke", "koennten", "waere"})
    formality = min(1.0, formal_words / max(len(words), 1) * 8)

    language_hint = "de" if re.search(r"\b(ich|und|der|die|das|bitte)\b", text.lower()) else "en"

    return {
        "avg_sentence_length": avg_sentence_length,
        "emoji_usage": emoji_usage,
        "directness": directness,
        "formality": formality,
        "language_hint": language_hint,
    }


def blend_style(existing: dict[str, Any], signal: dict[str, float | str], alpha: float = 0.2) -> dict[str, Any]:
    updated = dict(existing)
    for key in ["avg_sentence_length", "emoji_usage", "directness", "formality"]:
        updated[key] = (1 - alpha) * float(existing.get(key, 0.5)) + alpha * float(signal[key])
    updated["language_hint"] = signal["language_hint"]
    updated["samples_seen"] = int(existing.get("samples_seen", 0)) + 1
    return updated
