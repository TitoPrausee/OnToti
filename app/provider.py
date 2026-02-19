from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .secrets_store import SecretsStore


@dataclass
class ProviderConfig:
    active: str
    options: dict[str, dict[str, Any]]


class ProviderRouter:
    def __init__(self, config_path: Path, secrets: SecretsStore):
        self.config_path = config_path
        self.secrets = secrets

    def load_config(self) -> ProviderConfig:
        data = json.loads(self.config_path.read_text(encoding="utf-8"))
        provider = data.get("provider", {})
        return ProviderConfig(
            active=provider.get("active", "openai"),
            options=provider.get("options", {}),
        )

    def describe_active(self) -> dict[str, Any]:
        cfg = self.load_config()
        settings = dict(cfg.options.get(cfg.active, {}))
        token_env = settings.get("api_key_env")
        if token_env:
            settings["api_key_present"] = bool(os.getenv(token_env) or self.secrets.get_secret(token_env))
        return {
            "active": cfg.active,
            "settings": settings,
        }

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        cfg = self.load_config()
        active = cfg.active
        settings = cfg.options.get(active, {})
        model = settings.get("model", "unknown-model")

        try:
            if active in {"openai", "github_models", "ollama", "lmstudio", "gemini"}:
                return self._openai_compatible_chat(settings, system_prompt, user_prompt)
            if active == "anthropic":
                return self._anthropic_chat(settings, system_prompt, user_prompt)
            return f"[{active}:{model}] Provider not implemented yet. Prompt: {user_prompt[:200]}"
        except Exception as exc:  # noqa: BLE001
            return f"[{active}:{model}] Provider call failed: {exc}"

    def verify_github_token(self, token: str) -> dict[str, Any]:
        req = urllib.request.Request(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "ontoti",
            },
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
                return {
                    "ok": True,
                    "login": payload.get("login"),
                    "id": payload.get("id"),
                }
        except urllib.error.HTTPError as exc:
            return {"ok": False, "error": f"GitHub HTTP {exc.code}"}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)}

    def _get_token(self, settings: dict[str, Any]) -> tuple[str | None, str | None]:
        token_env = settings.get("api_key_env")
        token = None
        if token_env:
            token = os.getenv(token_env) or self.secrets.get_secret(token_env)
        return token_env, token

    def _openai_compatible_chat(self, settings: dict[str, Any], system_prompt: str, user_prompt: str) -> str:
        base_url = settings.get("base_url", "").rstrip("/")
        model = settings.get("model", "unknown-model")
        token_env, token = self._get_token(settings)

        if not base_url:
            raise ValueError("missing base_url in provider settings")
        if token_env and not token:
            raise ValueError(f"missing API key in env/secrets for {token_env}")

        url = f"{base_url}/chat/completions"
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.4,
        }

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "ontoti",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))

        try:
            return payload["choices"][0]["message"]["content"]
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"invalid provider response: {payload}") from exc

    def _anthropic_chat(self, settings: dict[str, Any], system_prompt: str, user_prompt: str) -> str:
        base_url = settings.get("base_url", "https://api.anthropic.com/v1").rstrip("/")
        model = settings.get("model", "claude-3-5-sonnet-20241022")
        token_env, token = self._get_token(settings)
        if token_env and not token:
            raise ValueError(f"missing API key in env/secrets for {token_env}")
        if not token:
            raise ValueError("missing anthropic api key")

        url = f"{base_url}/messages"
        body = {
            "model": model,
            "max_tokens": 512,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        headers = {
            "Content-Type": "application/json",
            "x-api-key": token,
            "anthropic-version": "2023-06-01",
            "User-Agent": "ontoti",
        }
        req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))

        try:
            return payload["content"][0]["text"]
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"invalid anthropic response: {payload}") from exc
