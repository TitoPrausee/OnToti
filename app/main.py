from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import persona as persona_mod
from .config_manager import ConfigManager
from .message_bus import create_message_bus
from .orchestrator import Orchestrator
from .provider import ProviderRouter
from .secrets_store import SecretsStore
from .security import is_client_allowed
from .store import MemoryStore, default_paths


app = FastAPI(title="OnToti", version="0.5.0")
paths = default_paths("data")
config_path = Path("config.json")
config_manager = ConfigManager(config_path)
store = MemoryStore(paths.db)
secrets = SecretsStore(paths.root / "secrets.json")
provider = ProviderRouter(config_path, secrets=secrets)
bus = create_message_bus(config_manager.load())
orchestrator = Orchestrator(store=store, paths=paths, provider=provider, config_path=config_path, bus=bus)

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


class ChatIn(BaseModel):
    session_id: str = Field(default="default")
    text: str


class SkillDraftIn(BaseModel):
    name: str
    description: str


class SkillApproveIn(BaseModel):
    skill_id: str


class ConfigUpdateIn(BaseModel):
    config: dict[str, Any]


class CopilotSetupIn(BaseModel):
    token: str
    token_env: str = Field(default="GITHUB_TOKEN")
    activate_provider: bool = Field(default=True)


class SetupApplyIn(BaseModel):
    bot_name: str | None = None
    bot_tone: str | None = None
    provider_active: str | None = None
    provider_base_url: str | None = None
    provider_model: str | None = None
    provider_api_key_env: str | None = None
    provider_api_key_value: str | None = None
    sandbox_mode: bool | None = None
    allowed_paths: list[str] | None = None
    tailnet_only: bool | None = None
    tailscale_cidrs: list[str] | None = None
    tailscale_node_allowlist: list[str] | None = None
    pipeline_mode: str | None = None
    pipeline_max_retries: int | None = None
    bus_backend: str | None = None
    bus_redis_url: str | None = None
    max_active_agents: int | None = None
    use_copilot: bool = False
    copilot_token: str | None = None


class ProviderTestIn(BaseModel):
    prompt: str = "Antworte kurz mit: setup ok"


@app.middleware("http")
async def tailnet_guard(request: Request, call_next):
    if request.url.path in {"/health", "/diagnostics"}:
        return await call_next(request)

    cfg = config_manager.load()
    security_cfg = cfg.get("security", {})
    client_ip = request.client.host if request.client else ""
    node_id = request.headers.get("x-tailscale-node")
    allowed, reason = is_client_allowed(client_ip=client_ip, security_cfg=security_cfg, node_id=node_id)

    if not allowed:
        return JSONResponse(status_code=403, content={"detail": f"access denied: {reason}"})

    return await call_next(request)


@app.get("/")
def ui():
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse(
        """
        <html><body style='font-family:sans-serif;padding:20px'>
        <h2>OnToti läuft, aber UI-Datei fehlt.</h2>
        <p>Prüfe: <code>app/static/index.html</code></p>
        <p><a href='/docs'>API Docs</a></p>
        </body></html>
        """
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/diagnostics")
def diagnostics() -> dict[str, Any]:
    return {
        "cwd": str(Path.cwd()),
        "static_dir": str(static_dir),
        "static_exists": static_dir.exists(),
        "index_exists": (static_dir / "index.html").exists(),
        "config_exists": config_path.exists(),
    }


@app.get("/security/status")
def security_status() -> dict[str, Any]:
    cfg = config_manager.load()
    security_cfg = cfg.get("security", {})
    return {
        "tailnet_only": bool(security_cfg.get("tailnet_only", False)),
        "tailscale_cidrs": security_cfg.get("tailscale_cidrs", ["100.64.0.0/10"]),
        "tailscale_node_allowlist": security_cfg.get("tailscale_node_allowlist", []),
    }


@app.get("/provider")
def provider_info() -> dict[str, Any]:
    return provider.describe_active()


@app.post("/provider/test")
def provider_test(payload: ProviderTestIn) -> dict[str, Any]:
    text = provider.generate(system_prompt="You are a setup test.", user_prompt=payload.prompt)
    return {"result": text}


@app.get("/setup/state")
def setup_state() -> dict[str, Any]:
    cfg = config_manager.load()
    return {
        "config": cfg,
        "persona": persona_mod.load_or_create(paths.persona),
        "provider": provider.describe_active(),
        "secrets": secrets.public_summary(),
        "bus": {
            "backend": cfg.get("bus", {}).get("backend", "local"),
            "recent_messages": len(bus.recent(limit=1000)),
        },
        "diagnostics": diagnostics(),
    }


@app.post("/setup/apply")
def setup_apply(payload: SetupApplyIn) -> dict[str, Any]:
    global bus, orchestrator

    cfg = config_manager.load()
    persona = persona_mod.load_or_create(paths.persona)

    if payload.bot_name:
        persona["name"] = payload.bot_name
    if payload.bot_tone:
        persona["tone"] = payload.bot_tone
    persona_mod.save(paths.persona, persona)

    provider_cfg = cfg.setdefault("provider", {})
    options = provider_cfg.setdefault("options", {})

    active = payload.provider_active or provider_cfg.get("active", "openai")
    active_settings = options.setdefault(active, {})
    if payload.provider_base_url:
        active_settings["base_url"] = payload.provider_base_url.strip()
    if payload.provider_model:
        active_settings["model"] = payload.provider_model.strip()

    token_env = payload.provider_api_key_env or active_settings.get("api_key_env")
    if token_env:
        active_settings["api_key_env"] = token_env

    if payload.provider_api_key_value and token_env:
        secrets.set_secret(token_env, payload.provider_api_key_value)

    provider_cfg["active"] = active

    security_cfg = cfg.setdefault("security", {})
    if payload.sandbox_mode is not None:
        security_cfg["sandbox_mode"] = payload.sandbox_mode
    if payload.allowed_paths is not None:
        security_cfg["allowed_paths"] = payload.allowed_paths
    if payload.tailnet_only is not None:
        security_cfg["tailnet_only"] = payload.tailnet_only
    if payload.tailscale_cidrs is not None:
        security_cfg["tailscale_cidrs"] = payload.tailscale_cidrs
    if payload.tailscale_node_allowlist is not None:
        security_cfg["tailscale_node_allowlist"] = payload.tailscale_node_allowlist

    agents_cfg = cfg.setdefault("agents", {})
    if payload.max_active_agents is not None:
        agents_cfg["max_active"] = max(1, int(payload.max_active_agents))

    pipelines_cfg = cfg.setdefault("pipelines", {})
    if payload.pipeline_mode:
        pipelines_cfg["mode"] = payload.pipeline_mode
    if payload.pipeline_max_retries is not None:
        pipelines_cfg["max_retries"] = max(0, int(payload.pipeline_max_retries))

    bus_cfg = cfg.setdefault("bus", {})
    if payload.bus_backend:
        bus_cfg["backend"] = payload.bus_backend
    if payload.bus_redis_url:
        bus_cfg["redis_url"] = payload.bus_redis_url

    if payload.use_copilot:
        if not payload.copilot_token:
            raise HTTPException(status_code=400, detail="copilot_token is required when use_copilot=true")
        verification = provider.verify_github_token(payload.copilot_token)
        if not verification.get("ok"):
            raise HTTPException(status_code=400, detail=verification.get("error", "token verification failed"))

        env_name = payload.provider_api_key_env or "GITHUB_TOKEN"
        os.environ[env_name] = payload.copilot_token
        secrets.set_secret(env_name, payload.copilot_token)

        gh = options.setdefault("github_models", {})
        gh["base_url"] = gh.get("base_url", "https://models.inference.ai.azure.com")
        gh["model"] = gh.get("model", "gpt-5-mini")
        gh["api_key_env"] = env_name
        provider_cfg["active"] = "github_models"

        cfg.setdefault("copilot", {})
        cfg["copilot"]["connected"] = True
        cfg["copilot"]["github_login"] = verification.get("login")
        cfg["copilot"]["token_env"] = env_name

    ok, msg = config_manager.validate(cfg)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    config_manager.save(cfg)

    bus = create_message_bus(cfg)
    orchestrator = Orchestrator(store=store, paths=paths, provider=provider, config_path=config_path, bus=bus)

    store.log_audit(
        actor="setup",
        action="apply",
        payload={
            "provider_active": cfg.get("provider", {}).get("active"),
            "secrets_count": secrets.public_summary().get("count"),
            "tailnet_only": cfg.get("security", {}).get("tailnet_only", False),
            "pipeline_mode": cfg.get("pipelines", {}).get("mode", "sequential"),
            "bus_backend": cfg.get("bus", {}).get("backend", "local"),
        },
        result="ok",
    )
    return {
        "status": "ok",
        "provider_active": cfg.get("provider", {}).get("active"),
        "secrets": secrets.public_summary(),
    }


@app.get("/config")
def config_get() -> dict[str, Any]:
    return config_manager.load()


@app.put("/config")
def config_put(payload: ConfigUpdateIn) -> dict[str, Any]:
    ok, msg = config_manager.validate(payload.config)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    config_manager.save(payload.config)
    store.log_audit(actor="config", action="update", payload={"keys": list(payload.config.keys())}, result="ok")
    return {"status": "ok"}


@app.post("/copilot/setup")
def copilot_setup(payload: CopilotSetupIn) -> dict[str, Any]:
    verification = provider.verify_github_token(payload.token)
    if not verification.get("ok"):
        raise HTTPException(status_code=400, detail=verification.get("error", "token verification failed"))

    os.environ[payload.token_env] = payload.token
    secrets.set_secret(payload.token_env, payload.token)

    cfg = config_manager.load()
    provider_cfg = cfg.setdefault("provider", {})
    options = provider_cfg.setdefault("options", {})
    gh = options.setdefault("github_models", {})
    gh["base_url"] = gh.get("base_url", "https://models.inference.ai.azure.com")
    gh["model"] = gh.get("model", "gpt-5-mini")
    gh["api_key_env"] = payload.token_env
    if payload.activate_provider:
        provider_cfg["active"] = "github_models"
    cfg.setdefault("copilot", {})
    cfg["copilot"]["connected"] = True
    cfg["copilot"]["github_login"] = verification.get("login")
    cfg["copilot"]["token_env"] = payload.token_env

    ok, msg = config_manager.validate(cfg)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    config_manager.save(cfg)
    store.log_audit(
        actor="copilot",
        action="setup",
        payload={"github_login": verification.get("login"), "token_env": payload.token_env},
        result="ok",
    )
    return {
        "status": "connected",
        "github_login": verification.get("login"),
        "provider_active": cfg.get("provider", {}).get("active"),
    }


@app.get("/context")
def context() -> dict[str, Any]:
    return orchestrator.context_snapshot()


@app.get("/agents")
def agents() -> dict[str, Any]:
    return {"agents": orchestrator.agents_snapshot()}


@app.get("/topology")
def topology() -> dict[str, Any]:
    return orchestrator.topology_snapshot()


@app.get("/bus/messages")
def bus_messages(limit: int = 200) -> dict[str, Any]:
    return {"messages": bus.recent(limit=limit)}


@app.get("/interactions")
def interactions(session_id: str | None = None, limit: int = 50) -> dict[str, Any]:
    return {"events": store.recent_interactions(session_id=session_id, limit=limit)}


@app.post("/chat")
def chat(payload: ChatIn) -> dict[str, Any]:
    return orchestrator.process_user_message(payload.session_id, payload.text)


@app.post("/reflect")
def reflect() -> dict[str, Any]:
    return orchestrator.reflect()


@app.post("/skills/propose")
def propose(payload: SkillDraftIn) -> dict[str, Any]:
    return orchestrator.propose_skill(payload.name, payload.description)


@app.post("/skills/approve")
def approve(payload: SkillApproveIn) -> dict[str, Any]:
    return orchestrator.approve_skill(payload.skill_id)


@app.get("/audit")
def audit(limit: int = 50) -> dict[str, Any]:
    return {"events": store.recent_audit(limit=limit)}
