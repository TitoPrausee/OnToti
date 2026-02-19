from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


DEFAULT_REGISTRY = {
    "skills": [],
}


def load_or_create(path: Path) -> dict[str, Any]:
    if not path.exists():
        path.write_text(json.dumps(DEFAULT_REGISTRY, indent=2), encoding="utf-8")
        return DEFAULT_REGISTRY
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower()).strip("-")
    return slug or "skill"


def propose_skill(registry: dict[str, Any], name: str, description: str) -> tuple[dict[str, Any], dict[str, Any]]:
    skill_id = slugify(name)
    draft = {
        "id": skill_id,
        "name": name,
        "description": description,
        "version": "0.1.0",
        "status": "draft",
        "allowed_tools": ["read", "write"],
    }
    registry = dict(registry)
    skills = list(registry.get("skills", []))
    skills = [s for s in skills if s.get("id") != skill_id]
    skills.append(draft)
    registry["skills"] = skills
    return registry, draft


def approve_skill(registry: dict[str, Any], skill_id: str) -> dict[str, Any]:
    registry = dict(registry)
    updated = []
    for skill in registry.get("skills", []):
        if skill.get("id") == skill_id:
            skill = dict(skill)
            skill["status"] = "active"
        updated.append(skill)
    registry["skills"] = updated
    return registry


def write_skill_markdown(skills_dir: Path, skill: dict[str, Any]) -> Path:
    skill_path = skills_dir / skill["id"]
    skill_path.mkdir(parents=True, exist_ok=True)
    md = skill_path / "SKILL.md"
    md.write_text(
        "\n".join(
            [
                f"# {skill['name']}",
                "",
                "## Purpose",
                skill["description"],
                "",
                "## Allowed Tools",
                *[f"- {tool}" for tool in skill.get("allowed_tools", [])],
                "",
                f"## Status: {skill.get('status', 'draft')}",
            ]
        ),
        encoding="utf-8",
    )
    return md
