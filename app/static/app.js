const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => [...document.querySelectorAll(sel)];

function setTab(target) {
  $$(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === target));
  $$(".panel").forEach((p) => p.classList.toggle("active", p.id === target));
}

$$(".tab").forEach((btn) => btn.addEventListener("click", () => setTab(btn.dataset.tab)));

async function api(url, options = {}) {
  const resp = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const text = await resp.text();
  let json;
  try {
    json = JSON.parse(text);
  } catch {
    json = { raw: text };
  }
  if (!resp.ok) throw new Error(json.detail || json.raw || resp.statusText);
  return json;
}

function appendMsg(role, text) {
  const node = document.createElement("div");
  node.className = `msg ${role}`;
  node.textContent = `${role.toUpperCase()}: ${text}`;
  $("#chat-log").appendChild(node);
  $("#chat-log").scrollTop = $("#chat-log").scrollHeight;
}

function splitCsv(value) {
  return value
    .split(",")
    .map((v) => v.trim())
    .filter(Boolean);
}

function renderTopology(topology) {
  const root = $("#topology-canvas");
  root.innerHTML = "";
  const nodes = topology.nodes || [];
  const edges = topology.edges || [];

  if (!nodes.length) {
    root.textContent = "Noch keine Agenten aktiv.";
    return;
  }

  const edgeWrap = document.createElement("div");
  edges.forEach((e) => {
    const el = document.createElement("div");
    el.className = "edge-line";
    el.textContent = `${e.from} -> ${e.to} (${e.task_id})`;
    edgeWrap.appendChild(el);
  });
  root.appendChild(edgeWrap);

  const childrenByParent = {};
  nodes.forEach((n) => {
    const p = n.parent_id || "root";
    childrenByParent[p] = childrenByParent[p] || [];
    childrenByParent[p].push(n);
  });

  const levels = [];
  let current = childrenByParent.root || [];
  let visited = new Set();
  while (current.length) {
    levels.push(current);
    const next = [];
    current.forEach((n) => {
      visited.add(n.agent_id);
      (childrenByParent[n.agent_id] || []).forEach((c) => {
        if (!visited.has(c.agent_id)) next.push(c);
      });
    });
    current = next;
  }

  levels.forEach((lvl) => {
    const row = document.createElement("div");
    row.className = "topo-row";
    lvl.forEach((n) => {
      const card = document.createElement("div");
      card.className = "topo-node";
      card.innerHTML = `
        <strong>${n.role}</strong><br>
        <small>${n.agent_id}</small><br>
        <small>Task: ${n.task_id}</small><br>
        <small>Status: ${n.status}</small><br>
        <small>Token: ${n.token_usage || 0}</small>
      `;
      row.appendChild(card);
    });
    root.appendChild(row);
  });
}

async function refreshSessions() {
  const out = await api("/sessions");
  const sessions = out.sessions || [];
  $("#sessions-view").textContent = JSON.stringify(out, null, 2);

  const select = $("#session-id");
  const current = select.value || "default";
  select.innerHTML = "";
  if (!sessions.length) {
    const op = document.createElement("option");
    op.value = "default";
    op.textContent = "default";
    select.appendChild(op);
    return;
  }

  sessions.forEach((s) => {
    const op = document.createElement("option");
    op.value = s.session_id;
    op.textContent = `${s.display_name} (${s.session_id})`;
    if (s.session_id === current) op.selected = true;
    select.appendChild(op);
  });
}

async function refreshAgents() {
  const out = await api("/agents");
  $("#agents-view").textContent = JSON.stringify(out, null, 2);
}

async function refreshTopology() {
  const out = await api("/topology");
  renderTopology(out);
}

async function refreshBus() {
  const out = await api("/bus/messages?limit=200");
  $("#bus-view").textContent = JSON.stringify(out, null, 2);
}

async function refreshAudit() {
  const out = await api("/audit?limit=100");
  $("#policy-view").textContent = JSON.stringify(out, null, 2);
}

async function refreshJobs() {
  const out = await api("/jobs");
  $("#jobs-view").textContent = JSON.stringify(out, null, 2);
}

async function refreshWebhooks() {
  const out = await api("/webhooks?limit=50");
  $("#webhooks-view").textContent = JSON.stringify(out, null, 2);
}

function fillSetupForm(state) {
  const cfg = state.config || {};
  const persona = state.persona || {};
  const provider = cfg.provider || {};
  const security = cfg.security || {};
  const pipelines = cfg.pipelines || {};
  const bus = cfg.bus || {};

  const active = provider.active || "github_models";
  const activeCfg = (provider.options || {})[active] || {};

  $("#setup-bot-name").value = persona.name || "";
  $("#setup-bot-tone").value = persona.tone || "";
  $("#setup-provider-active").value = active;
  $("#setup-provider-base-url").value = activeCfg.base_url || "";
  $("#setup-provider-model").value = activeCfg.model || "";
  $("#setup-provider-key-env").value = activeCfg.api_key_env || "GITHUB_TOKEN";
  $("#setup-sandbox-mode").checked = !!security.sandbox_mode;
  $("#setup-tailnet-only").checked = !!security.tailnet_only;
  $("#setup-tailscale-cidrs").value = (security.tailscale_cidrs || ["100.64.0.0/10"]).join(", ");
  $("#setup-node-allowlist").value = (security.tailscale_node_allowlist || []).join(", ");
  $("#setup-allowed-paths").value = (security.allowed_paths || []).join(", ");
  $("#setup-max-agents").value = (cfg.agents || {}).max_active || 4;
  $("#setup-pipeline-mode").value = pipelines.mode || "sequential";
  $("#setup-pipeline-retries").value = pipelines.max_retries ?? 1;
  $("#setup-bus-backend").value = bus.backend || "local";
  $("#setup-bus-redis-url").value = bus.redis_url || "redis://localhost:6379/0";

  $("#setup-state-view").textContent = JSON.stringify(state, null, 2);
}

async function loadSetupState() {
  const state = await api("/setup/state");
  fillSetupForm(state);
  $("#config-editor").value = JSON.stringify(state.config || {}, null, 2);
}

$("#chat-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const session_id = $("#session-id").value || "default";
  const text = $("#chat-input").value.trim();
  if (!text) return;
  appendMsg("user", `[${session_id}] ${text}`);
  $("#chat-input").value = "";
  try {
    const out = await api("/chat", { method: "POST", body: JSON.stringify({ session_id, text }) });
    appendMsg("bot", out.reply || "(leer)");
    await Promise.all([refreshTopology(), refreshBus(), refreshAgents(), refreshSessions()]);
  } catch (err) {
    appendMsg("bot", `Fehler: ${err.message}`);
  }
});

$("#refresh-agents").addEventListener("click", refreshAgents);
$("#refresh-topology").addEventListener("click", refreshTopology);
$("#refresh-bus").addEventListener("click", refreshBus);

$("#reload-sessions").addEventListener("click", refreshSessions);
$("#create-session").addEventListener("click", async () => {
  const session_id = $("#new-session-id").value.trim();
  const display_name = $("#new-session-name").value.trim() || null;
  if (!session_id) return;
  await api("/sessions", { method: "POST", body: JSON.stringify({ session_id, display_name }) });
  $("#new-session-id").value = "";
  $("#new-session-name").value = "";
  await refreshSessions();
});

$("#reload-jobs").addEventListener("click", refreshJobs);
$("#create-job").addEventListener("click", async () => {
  const kind = $("#job-kind").value;
  const session = $("#job-session").value.trim() || "default";
  const text = $("#job-text").value.trim() || "";
  const payload = kind === "heartbeat" ? { kind, channel: text || "web-ui" } : { kind, session_id: session, text };

  await api("/jobs", {
    method: "POST",
    body: JSON.stringify({
      name: $("#job-name").value.trim() || `job-${Date.now()}`,
      cron: $("#job-cron").value.trim(),
      enabled: true,
      payload,
    }),
  });
  await refreshJobs();
});

$("#reload-webhooks").addEventListener("click", refreshWebhooks);
$("#send-webhook").addEventListener("click", async () => {
  const source = $("#webhook-source").value.trim() || "manual";
  const text = $("#webhook-text").value.trim() || "Webhook";
  await api(`/webhooks/${encodeURIComponent(source)}`, {
    method: "POST",
    body: JSON.stringify({ payload: { text } }),
  });
  await refreshWebhooks();
});

$("#check-path").addEventListener("click", async () => {
  const out = await api("/policy/file-check", { method: "POST", body: JSON.stringify({ path: $("#policy-path").value }) });
  $("#policy-view").textContent = JSON.stringify(out, null, 2);
});

$("#check-cmd").addEventListener("click", async () => {
  const out = await api("/policy/shell-check", { method: "POST", body: JSON.stringify({ command: $("#policy-cmd").value }) });
  $("#policy-view").textContent = JSON.stringify(out, null, 2);
});

$("#verify-audit").addEventListener("click", async () => {
  const out = await api("/audit/verify");
  $("#policy-view").textContent = JSON.stringify(out, null, 2);
});

$("#reload-audit").addEventListener("click", refreshAudit);

$("#setup-load").addEventListener("click", async () => {
  await loadSetupState();
  $("#setup-status").textContent = "Setup geladen.";
});

$("#setup-apply").addEventListener("click", async () => {
  const payload = {
    bot_name: $("#setup-bot-name").value.trim() || null,
    bot_tone: $("#setup-bot-tone").value.trim() || null,
    provider_active: $("#setup-provider-active").value,
    provider_base_url: $("#setup-provider-base-url").value.trim() || null,
    provider_model: $("#setup-provider-model").value.trim() || null,
    provider_api_key_env: $("#setup-provider-key-env").value.trim() || null,
    provider_api_key_value: $("#setup-provider-key-value").value.trim() || null,
    sandbox_mode: $("#setup-sandbox-mode").checked,
    tailnet_only: $("#setup-tailnet-only").checked,
    tailscale_cidrs: splitCsv($("#setup-tailscale-cidrs").value),
    tailscale_node_allowlist: splitCsv($("#setup-node-allowlist").value),
    allowed_paths: splitCsv($("#setup-allowed-paths").value),
    max_active_agents: Number($("#setup-max-agents").value || 4),
    pipeline_mode: $("#setup-pipeline-mode").value,
    pipeline_max_retries: Number($("#setup-pipeline-retries").value || 1),
    bus_backend: $("#setup-bus-backend").value,
    bus_redis_url: $("#setup-bus-redis-url").value.trim() || null,
    use_copilot: $("#setup-use-copilot").checked,
    copilot_token: $("#setup-copilot-token").value.trim() || null,
  };

  $("#setup-status").textContent = "Wende Setup an...";
  try {
    const out = await api("/setup/apply", { method: "POST", body: JSON.stringify(payload) });
    $("#setup-provider-key-value").value = "";
    $("#setup-copilot-token").value = "";
    $("#setup-status").textContent = `Setup gespeichert. Provider: ${out.provider_active}`;
    await loadSetupState();
  } catch (err) {
    $("#setup-status").textContent = `Fehler: ${err.message}`;
  }
});

$("#setup-test-provider").addEventListener("click", async () => {
  $("#setup-status").textContent = "Teste Provider...";
  try {
    const out = await api("/provider/test", { method: "POST", body: JSON.stringify({}) });
    $("#setup-status").textContent = `Provider-Test: ${out.result.slice(0, 140)}`;
  } catch (err) {
    $("#setup-status").textContent = `Provider-Test Fehler: ${err.message}`;
  }
});

$("#load-config").addEventListener("click", async () => {
  const out = await api("/config");
  $("#config-editor").value = JSON.stringify(out, null, 2);
});

$("#save-config").addEventListener("click", async () => {
  let cfg;
  try {
    cfg = JSON.parse($("#config-editor").value);
  } catch {
    alert("Ungueltiges JSON");
    return;
  }
  await api("/config", { method: "PUT", body: JSON.stringify({ config: cfg }) });
  alert("Config gespeichert");
  await loadSetupState();
});

(async function init() {
  try {
    await loadSetupState();
    await Promise.all([refreshTopology(), refreshBus(), refreshAgents(), refreshSessions(), refreshJobs(), refreshWebhooks(), refreshAudit()]);
    const interactions = await api("/interactions?limit=20");
    interactions.events.reverse().forEach((evt) => {
      appendMsg("user", evt.user_text);
      if (evt.bot_text) appendMsg("bot", evt.bot_text);
    });
  } catch (err) {
    appendMsg("bot", `Init-Fehler: ${err.message}`);
  }
})();
