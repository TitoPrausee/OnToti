from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from typing import Any


@dataclass
class BusMessage:
    message_id: str
    sender_id: str
    receiver_id: str
    task_id: str
    payload: dict[str, Any]
    priority: int
    timestamp: float


class LocalMessageBus:
    def __init__(self, max_messages: int = 1000):
        self.max_messages = max_messages
        self._messages: list[BusMessage] = []

    def publish(self, sender_id: str, receiver_id: str, task_id: str, payload: dict[str, Any], priority: int = 5) -> BusMessage:
        msg = BusMessage(
            message_id=f"m-{uuid.uuid4().hex[:10]}",
            sender_id=sender_id,
            receiver_id=receiver_id,
            task_id=task_id,
            payload=payload,
            priority=priority,
            timestamp=time.time(),
        )
        self._messages.append(msg)
        if len(self._messages) > self.max_messages:
            self._messages = self._messages[-self.max_messages :]
        return msg

    def recent(self, limit: int = 200) -> list[dict[str, Any]]:
        return [
            {
                "message_id": m.message_id,
                "sender_id": m.sender_id,
                "receiver_id": m.receiver_id,
                "task_id": m.task_id,
                "payload": m.payload,
                "priority": m.priority,
                "timestamp": m.timestamp,
            }
            for m in self._messages[-limit:]
        ]


class RedisStreamBus(LocalMessageBus):
    def __init__(self, redis_url: str, stream_key: str = "ontoti:bus", max_messages: int = 1000):
        super().__init__(max_messages=max_messages)
        self.redis_url = redis_url
        self.stream_key = stream_key
        try:
            import redis  # type: ignore

            self._redis = redis.from_url(redis_url, decode_responses=True)
        except Exception:
            self._redis = None

    def publish(self, sender_id: str, receiver_id: str, task_id: str, payload: dict[str, Any], priority: int = 5) -> BusMessage:
        msg = super().publish(sender_id, receiver_id, task_id, payload, priority)
        if self._redis is not None:
            try:
                self._redis.xadd(
                    self.stream_key,
                    {
                        "message_id": msg.message_id,
                        "sender_id": sender_id,
                        "receiver_id": receiver_id,
                        "task_id": task_id,
                        "payload": json.dumps(payload),
                        "priority": str(priority),
                        "timestamp": str(msg.timestamp),
                    },
                    maxlen=self.max_messages,
                    approximate=True,
                )
            except Exception:
                pass
        return msg


def create_message_bus(config: dict[str, Any]) -> LocalMessageBus:
    bus_cfg = config.get("bus", {}) if isinstance(config, dict) else {}
    backend = str(bus_cfg.get("backend", "local")).lower()
    max_messages = int(bus_cfg.get("max_messages", 1000))

    if backend == "redis":
        redis_url = str(bus_cfg.get("redis_url", "redis://localhost:6379/0"))
        stream_key = str(bus_cfg.get("stream_key", "ontoti:bus"))
        return RedisStreamBus(redis_url=redis_url, stream_key=stream_key, max_messages=max_messages)

    return LocalMessageBus(max_messages=max_messages)
