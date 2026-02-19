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
from .message_bus import LocalMessageBus
from .provider import ProviderRouter
from .store import MemoryStore, StorePaths


UTC = timezone.utc


def now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def estimate_tokens(text: str | None) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)


@dataclass
class AgentStatus:
    agent_id: str
    parent_id: str | None
    role: str
    task: str
    status: str
    task_id: str
    output: str | None = None
    token_usage: int = 0
    started_at: str = field(default_factory=now_iso)
    ended_at: str | None = None


@dataclass
class Orchestrator:
    store: MemoryStore
    paths: StorePaths
    provider: ProviderRouter
    config_path: Path
    bus: LocalMessageBus
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
        task_id = f"t-{uuid.uuid4().hex[:10]}"
        signal = style_mod.analyze_text(text)
        style = style_mod.load_or_create(self.paths.style)
        updated_style = style_mod.blend_style(style, signal)
        style_mod.save(self.paths.style, updated_style)

        if "du" in text.lower() and "bitte" in text.lower():
            self.store.upsert_preference("preferred_tone", "freundlich-direkt", confidence=0.74)

        snapshot = self.context_snapshot()
        system_prompt = self._system_prompt(snapshot)

        root = self._start_agent(parent_id=None, role="orchestrator", task=text, task_id=task_id)
        self.bus.publish(sender_id="user", receiver_id=root.agent_id, task_id=task_id, payload={"text": text}, priority=7)

        sub_results: list[dict[str, Any]] = []
        if self._should_delegate(text):
            sub_results = self._run_pipeline(root.agent_id, text, system_prompt, task_id)
            combined = "\n".join(s["output"] for s in sub_results if s.get("output"))
            final_prompt = f"Konsolidiere die folgenden Teilantworten:\n{combined}\n\nNutzerfrage:\n{text}"
            reply = self.provider.generate(system_prompt=system_prompt, user_prompt=final_prompt)
        else:
            reply = self.provider.generate(system_prompt=system_prompt, user_prompt=text)

        self._finish_agent(root.agent_id, reply)
        self.bus.publish(
            sender_id=root.agent_id,
            receiver_id="user",
            task_id=task_id,
            payload={"reply": reply[:300]},
            priority=7,
        )

        self.store.record_interaction(session_id=session_id, user_text=text, bot_text=reply)
        self.store.log_audit(
            actor="orchestrator",
            action="process_message",
            payload={
                "session_id": session_id,
                "task_id": task_id,
                "text": text[:400],
                "delegated": bool(sub_results),
                "sub_agents": len(sub_results),
            },
            result="ok",
        )

        return {
            "reply": reply,
            "task_id": task_id,
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

    def _run_pipeline(self, root_id: str, text: str, system_prompt: str, task_id: str) -> list[dict[str, Any]]:
        parts = self._split_task(text)
        max_agents = self._max_active_agents()
        parts = parts[: max(1, max_agents - 1)]

        pipeline_cfg = self._pipeline_config()
        mode = str(pipeline_cfg.get("mode", "sequential")).lower()
        max_retries = int(pipeline_cfg.get("max_retries", 1))

        stage_ids = [f"s{i + 1}" for i in range(len(parts))]
        graph = {sid: [] for sid in stage_ids}

        if mode == "sequential":
            for idx in range(1, len(stage_ids)):
                graph[stage_ids[idx]].append(stage_ids[idx - 1])

        if self._has_cycle(graph):
            self.store.log_audit(actor="orchestrator", action="pipeline_cycle_detected", payload={"graph": graph}, result="blocked")
            return []

        order = self._topological_order(graph)
        order_index = {sid: i for i, sid in enumerate(stage_ids)}

        results: dict[str, dict[str, Any]] = {}
        for sid in order:
            idx = order_index[sid]
            part = parts[idx]
            role = f"worker-{idx + 1}"
            agent = self._start_agent(parent_id=root_id, role=role, task=part, task_id=task_id)

            deps = graph.get(sid, [])
            dep_text = "\n".join(results[d]["output"] for d in deps if d in results and results[d].get("output"))
            user_prompt = part if not dep_text else f"Kontext aus vorherigen Stufen:\n{dep_text}\n\nAufgabe:\n{part}"

            output = ""
            for attempt in range(max_retries + 1):
                output = self.provider.generate(system_prompt=system_prompt, user_prompt=user_prompt)
                if output:
                    break
                if attempt == max_retries:
                    output = "Fehler: keine Ausgabe"

            self._finish_agent(agent.agent_id, output)
            self.bus.publish(
                sender_id=agent.agent_id,
                receiver_id=root_id,
                task_id=task_id,
                payload={"stage": sid, "role": role, "output": output[:300]},
                priority=5,
            )
            results[sid] = {"agent_id": agent.agent_id, "task": part, "output": output, "stage": sid, "depends_on": deps}

        return [results[sid] for sid in order if sid in results]

    def _split_task(self, text: str) -> list[str]:
        chunks = [c.strip() for c in text.replace(";", ".").split(".") if c.strip()]
        if len(chunks) <= 1 and " und " in text.lower():
            chunks = [c.strip() for c in text.split(" und ") if c.strip()]
        return chunks[:8] if chunks else [text]

    def _pipeline_config(self) -> dict[str, Any]:
        try:
            cfg = json.loads(self.config_path.read_text(encoding="utf-8"))
            pipelines = cfg.get("pipelines", {})
            if isinstance(pipelines, dict):
                return pipelines
        except Exception:
            pass
        return {"mode": "sequential", "max_retries": 1}

    def _has_cycle(self, graph: dict[str, list[str]]) -> bool:
        visiting: set[str] = set()
        visited: set[str] = set()

        def dfs(node: str) -> bool:
            if node in visiting:
                return True
            if node in visited:
                return False
            visiting.add(node)
            for dep in graph.get(node, []):
                if dfs(dep):
                    return True
            visiting.remove(node)
            visited.add(node)
            return False

        return any(dfs(node) for node in graph)

    def _topological_order(self, graph: dict[str, list[str]]) -> list[str]:
        indegree = {n: 0 for n in graph}
        reverse: dict[str, list[str]] = {n: [] for n in graph}

        for node, deps in graph.items():
            indegree[node] = len(deps)
            for dep in deps:
                reverse.setdefault(dep, []).append(node)

        queue = [n for n, deg in indegree.items() if deg == 0]
        ordered: list[str] = []

        while queue:
            node = queue.pop(0)
            ordered.append(node)
            for nxt in reverse.get(node, []):
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    queue.append(nxt)

        return ordered if len(ordered) == len(graph) else list(graph.keys())

    def _max_active_agents(self) -> int:
        try:
            cfg = json.loads(self.config_path.read_text(encoding="utf-8"))
            return int(cfg.get("agents", {}).get("max_active", 4))
        except Exception:
            return 4

    def _start_agent(self, parent_id: str | None, role: str, task: str, task_id: str) -> AgentStatus:
        agent = AgentStatus(
            agent_id=f"a-{uuid.uuid4().hex[:8]}",
            parent_id=parent_id,
            role=role,
            task=task[:280],
            status="running",
            task_id=task_id,
        )
        self._agents[agent.agent_id] = agent
        return agent

    def _finish_agent(self, agent_id: str, output: str) -> None:
        agent = self._agents[agent_id]
        agent.status = "done"
        agent.output = output[:500]
        agent.token_usage = estimate_tokens(agent.task) + estimate_tokens(output)
        agent.ended_at = now_iso()

    def agents_snapshot(self) -> list[dict[str, Any]]:
        return [
            {
                "agent_id": a.agent_id,
                "task_id": a.task_id,
                "parent_id": a.parent_id,
                "role": a.role,
                "task": a.task,
                "status": a.status,
                "token_usage": a.token_usage,
                "started_at": a.started_at,
                "ended_at": a.ended_at,
            }
            for a in self._agents.values()
        ]

    def topology_snapshot(self) -> dict[str, Any]:
        agents = self.agents_snapshot()
        edges = []
        for a in agents:
            if a["parent_id"]:
                edges.append({"from": a["parent_id"], "to": a["agent_id"], "task_id": a["task_id"]})
        return {"nodes": agents, "edges": edges}

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
