from __future__ import annotations

import os
import shlex
from pathlib import Path
from typing import Any


DESTRUCTIVE_TOKENS = {"rm", "mv", "dd", "mkfs", "shutdown", "reboot", "poweroff"}


def _norm(path: str) -> str:
    return str(Path(path).resolve())


def is_path_allowed(path: str, allowed_paths: list[str]) -> bool:
    target = _norm(path)
    for raw in allowed_paths:
        root = _norm(raw)
        if target == root or target.startswith(root + os.sep):
            return True
    return False


def check_file_access(path: str, allowed_paths: list[str]) -> tuple[bool, str]:
    if is_path_allowed(path, allowed_paths):
        return True, "allowed"
    return False, "path outside whitelist"


def check_shell_command(cmd: str, sandbox_mode: bool) -> tuple[bool, str]:
    try:
        parts = shlex.split(cmd)
    except Exception:
        return False, "invalid shell syntax"

    if not parts:
        return False, "empty command"

    if sandbox_mode and parts[0] in DESTRUCTIVE_TOKENS:
        return False, f"command blocked in sandbox: {parts[0]}"

    return True, "allowed"


def policy_status(config: dict[str, Any]) -> dict[str, Any]:
    sec = config.get("security", {})
    return {
        "sandbox_mode": bool(sec.get("sandbox_mode", True)),
        "allowed_paths": sec.get("allowed_paths", []),
        "tailnet_only": bool(sec.get("tailnet_only", False)),
    }
