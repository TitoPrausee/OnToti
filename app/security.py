from __future__ import annotations

import ipaddress
from typing import Any

LOCAL_ALLOWED = {"127.0.0.1", "::1", "localhost"}


def is_ip_in_cidrs(ip: str, cidrs: list[str]) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False

    for raw in cidrs:
        try:
            net = ipaddress.ip_network(raw, strict=False)
        except ValueError:
            continue
        if addr in net:
            return True
    return False


def is_client_allowed(client_ip: str, security_cfg: dict[str, Any], node_id: str | None = None) -> tuple[bool, str]:
    if client_ip in LOCAL_ALLOWED:
        return True, "local"

    tailnet_only = bool(security_cfg.get("tailnet_only", False))
    if not tailnet_only:
        return True, "tailnet disabled"

    cidrs = security_cfg.get("tailscale_cidrs", ["100.64.0.0/10"])
    if not isinstance(cidrs, list) or not is_ip_in_cidrs(client_ip, [str(c) for c in cidrs]):
        return False, "client ip not in allowed tailnet cidrs"

    allowlist = security_cfg.get("tailscale_node_allowlist", [])
    if isinstance(allowlist, list) and allowlist:
        if not node_id or node_id not in allowlist:
            return False, "tailscale node id not allowed"

    return True, "allowed"
