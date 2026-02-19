from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


UTC = timezone.utc


def _parse_cron_6(cron_expr: str) -> CronTrigger:
    parts = cron_expr.split()
    if len(parts) != 6:
        raise ValueError("cron must have 6 fields: sec min hour day month weekday")
    sec, minute, hour, day, month, weekday = parts
    return CronTrigger(
        second=sec,
        minute=minute,
        hour=hour,
        day=day,
        month=month,
        day_of_week=weekday,
        timezone=UTC,
    )


@dataclass
class JobPayload:
    kind: str
    session_id: str | None = None
    text: str | None = None
    channel: str | None = None


class SchedulerManager:
    def __init__(
        self,
        list_jobs: Callable[[], list[dict[str, Any]]],
        upsert_job: Callable[[str, str, str, bool, dict[str, Any]], None],
        delete_job: Callable[[str], None],
        set_job_enabled: Callable[[str, bool], None],
        run_chat: Callable[[str, str], dict[str, Any]],
        heartbeat_fn: Callable[[str], None],
        audit_fn: Callable[[str, dict[str, Any], str], None],
    ):
        self._scheduler = BackgroundScheduler(timezone=UTC)
        self._list_jobs = list_jobs
        self._upsert_job = upsert_job
        self._delete_job = delete_job
        self._set_job_enabled = set_job_enabled
        self._run_chat = run_chat
        self._heartbeat_fn = heartbeat_fn
        self._audit = audit_fn

    def start(self) -> None:
        if not self._scheduler.running:
            self._scheduler.start()
        self.reload()

    def shutdown(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    def reload(self) -> None:
        for j in self._scheduler.get_jobs():
            self._scheduler.remove_job(j.id)

        for job in self._list_jobs():
            if not job.get("enabled", True):
                continue
            self._schedule_existing_job(job)

    def _schedule_existing_job(self, job: dict[str, Any]) -> None:
        payload = job.get("payload", {})
        trigger = _parse_cron_6(job["cron"])
        self._scheduler.add_job(
            self._execute_job,
            trigger=trigger,
            id=job["job_id"],
            replace_existing=True,
            args=[job["job_id"], payload],
            max_instances=1,
            coalesce=True,
        )

    def create_job(self, name: str, cron: str, payload: dict[str, Any], enabled: bool = True) -> dict[str, Any]:
        _parse_cron_6(cron)
        job_id = f"j-{uuid.uuid4().hex[:10]}"
        self._upsert_job(job_id, name, cron, enabled, payload)
        self.reload()
        return {"job_id": job_id, "name": name, "cron": cron, "enabled": enabled, "payload": payload}

    def update_job(self, job_id: str, name: str, cron: str, payload: dict[str, Any], enabled: bool) -> None:
        _parse_cron_6(cron)
        self._upsert_job(job_id, name, cron, enabled, payload)
        self.reload()

    def delete_job(self, job_id: str) -> None:
        self._delete_job(job_id)
        try:
            self._scheduler.remove_job(job_id)
        except Exception:
            pass

    def pause_job(self, job_id: str) -> None:
        self._set_job_enabled(job_id, False)
        try:
            self._scheduler.pause_job(job_id)
        except Exception:
            pass

    def resume_job(self, job_id: str) -> None:
        self._set_job_enabled(job_id, True)
        self.reload()

    def _execute_job(self, job_id: str, payload: dict[str, Any]) -> None:
        kind = str(payload.get("kind", "chat_message"))
        try:
            if kind == "chat_message":
                session_id = str(payload.get("session_id", "scheduler"))
                text = str(payload.get("text", "Geplante Aufgabe"))
                self._run_chat(session_id, text)
            elif kind == "heartbeat":
                channel = str(payload.get("channel", "web-ui"))
                self._heartbeat_fn(channel)
            self._audit("scheduler", "execute_job", {"job_id": job_id, "kind": kind}, "ok")
        except Exception as exc:  # noqa: BLE001
            self._audit("scheduler", "execute_job", {"job_id": job_id, "kind": kind, "error": str(exc)}, "error")


def default_heartbeat_message() -> str:
    return f"Heartbeat @ {datetime.now(tz=UTC).isoformat()}"
