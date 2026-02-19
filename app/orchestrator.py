from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import persona as persona_mod
from . import skills as skills_mod
from . import style as style_mod
from .provider import ProviderRouter
from .store import MemoryStore, StorePaths


UTC = timezone.utc


def now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


@dataclass
class AgentStatus:
    agent_id: str
    parent_id: str | None
    role: str
    task: str
    status: str
    output: str | None = None
    started_at: str = field(default_factory=now_iso)
    ended_at: str | None = None


@dataclass
class Orchestrator:
    store: MemoryStore
    paths: StorePaths
    provider: ProviderRouter
    config_path: Path
    _agents: dict[str, AgentStatus] = field(default_factory=dict)

    def context_snapshot(self) -> dict[str, Any]:
        persona = persona_mod.load_or_create(self.paths.persona)
        style = style_mod.load_or_create(self.paths.style)
        memory = self.store.relevant_preferences()
        registry = skills_mod.load_or_create(self.paths.skill_registry)
        active_skills = [s for s in registry.get("skills", []) if s.get("status") == "active"]
        return {
            "persona": persona,
            "style_profile": style,
            "preferences": memory,
            "active_skills": active_skills,
            "agents": self.agents_snapshot(),
        }

    def process_user_message(self, session_id: str, text: str) -> dict[str, Any]:
        signal = style_mod.analyze_text(text)
        style = style_mod.load_or_create(self.paths.style)
        updated_style = style_mod.blend_style(style, signal)
        style_mod.save(self.paths.style, updated_style)

        if "du" in text.lower() and "bitte" in text.lower():
            self.store.upsert_preference("preferred_tone", "freundlich-direkt", confidence=0.74)

        snapshot = self.context_snapshot()
        system_prompt = self._system_prompt(snapshot)

        root = self._start_agent(parent_id=None, role="orchestrator", task=text)
        sub_results: list[dict[str, Any]] = []
        if self._should_delegate(text):
            sub_results = self._run_sub_agents(root.agent_id, text, system_prompt)
            combined = "\n".join(s["output"] for s in sub_results if s.get("output"))
            final_prompt = f"Konsolidiere die folgenden Teilantworten:\n{combined}\n\nNutzerfrage:\n{text}"
            reply = self.provider.generate(system_prompt=system_prompt, user_prompt=final_prompt)
        else:
            reply = self.provider.generate(system_prompt=system_prompt, user_prompt=text)

        self._finish_agent(root.agent_id, reply)

        self.store.record_interaction(session_id=session_id, user_text=text, bot_text=reply)
        self.store.log_audit(
            actor="orchestrator",
            action="process_message",
            payload={
                "session_id": session_id,
                "text": text[:400],
                "delegated": bool(sub_results),
                "sub_agents": len(sub_results),
            },
            result="ok",
        )

        return {
            "reply": reply,
            "signal": signal,
            "sub_agents": sub_results,
            "context_used": {
                "preferences_count": len(snapshot["preferences"]),
                "active_skills_count": len(snapshot["active_skills"]),
            },
        }

    def _system_prompt(self, snapshot: dict[str, Any]) -> str:
        persona = snapshot["persona"]
        style = snapshot["style_profile"]
        return (
            f"Du bist {persona.get('name', 'Assistant')} mit Ton: {persona.get('tone', 'direkt')}. "
            f"Sprache-Hinweis: {style.get('language_hint', 'de')}. "
            f"Direktheit: {style.get('directness', 0.5):.2f}. "
            f"Aktive Skills: {len(snapshot['active_skills'])}."
        )

    def _should_delegate(self, text: str) -> bool:
        return len(text) > 180 or " und " in text.lower() or ";" in text

    def _run_sub_agents(self, root_id: str, text: str, system_prompt: str) -> list[dict[str, Any]]:
        parts = self._split_task(text)
        max_agents = self._max_active_agents()
        parts = parts[: max(1, max_agents - 1)]

        results: list[dict[str, Any]] = []
        for index, part in enumerate(parts, start=1):
            agent = self._start_agent(parent_id=root_id, role=f"worker-{index}", task=part)
            output = self.provider.generate(system_prompt=system_prompt, user_prompt=part)
            self._finish_agent(agent.agent_id, output)
            results.append({"agent_id": agent.agent_id, "task": part, "output": output})
        return results

    def _split_task(self, text: str) -> list[str]:
        chunks = [c.strip() for c in text.replace(";", ".").split(".") if c.strip()]
        if len(chunks) <= 1 and " und " in text.lower():
            chunks = [c.strip() for c in text.split(" und ") if c.strip()]
        return chunks[:4] if chunks else [text]

    def _max_active_agents(self) -> int:
        try:
            cfg = json.loads(self.config_path.read_text(encoding="utf-8"))
            return int(cfg.get("agents", {}).get("max_active", 4))
        except Exception:  # noqa: BLE001
            return 4

    def _start_agent(self, parent_id: str | None, role: str, task: str) -> AgentStatus:
        agent = AgentStatus(
            agent_id=f"a-{uuid.uuid4().hex[:8]}",
            parent_id=parent_id,
            role=role,
            task=task[:280],
            status="running",
        )
        self._agents[agent.agent_id] = agent
        return agent

    def _finish_agent(self, agent_id: str, output: str) -> None:
        agent = self._agents[agent_id]
        agent.status = "done"
        agent.output = output[:500]
        agent.ended_at = now_iso()

    def agents_snapshot(self) -> list[dict[str, Any]]:
        return [
            {
                "agent_id": a.agent_id,
                "parent_id": a.parent_id,
                "role": a.role,
                "task": a.task,
                "status": a.status,
                "started_at": a.started_at,
                "ended_at": a.ended_at,
            }
            for a in self._agents.values()
        ]

    def reflect(self) -> dict[str, Any]:
        persona = persona_mod.load_or_create(self.paths.persona)
        style = style_mod.load_or_create(self.paths.style)

        if style.get("directness", 0.5) > 0.7:
            persona["tone"] = "sehr direkt und fokussiert"
        elif style.get("formality", 0.5) > 0.6:
            persona["tone"] = "formell und strukturiert"
        else:
            persona["tone"] = "direkt und respektvoll"

        persona["self_reflection"]["last_update"] = now_iso()
        persona_mod.save(self.paths.persona, persona)
        self.store.log_audit(actor="orchestrator", action="reflect", payload={"tone": persona["tone"]}, result="ok")
        return {"updated_persona": persona}

    def propose_skill(self, name: str, description: str) -> dict[str, Any]:
        registry = skills_mod.load_or_create(self.paths.skill_registry)
        registry, draft = skills_mod.propose_skill(registry, name, description)
        skills_mod.save(self.paths.skill_registry, registry)
        md_path = skills_mod.write_skill_markdown(self.paths.root.parent / "skills", draft)
        self.store.log_audit(actor="orchestrator", action="propose_skill", payload=draft, result="ok")
        return {"draft": draft, "skill_markdown": str(md_path)}

    def approve_skill(self, skill_id: str) -> dict[str, Any]:
        registry = skills_mod.load_or_create(self.paths.skill_registry)
        registry = skills_mod.approve_skill(registry, skill_id)
        skills_mod.save(self.paths.skill_registry, registry)

        active = [s for s in registry.get("skills", []) if s.get("id") == skill_id and s.get("status") == "active"]
        if active:
            skills_mod.write_skill_markdown(self.paths.root.parent / "skills", active[0])

        self.store.log_audit(actor="orchestrator", action="approve_skill", payload={"skill_id": skill_id}, result="ok")
        return {"approved": bool(active), "skill_id": skill_id}
