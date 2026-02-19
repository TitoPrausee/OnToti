const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => [...document.querySelectorAll(sel)];

function setTab(target) {
  $$(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === target));
  $$(".panel").forEach((p) => p.classList.toggle("active", p.id === target));
}

$$(".tab").forEach((btn) => {
  btn.addEventListener("click", () => setTab(btn.dataset.tab));
});

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

function fillSetupForm(state) {
  const cfg = state.config || {};
  const persona = state.persona || {};
  const provider = cfg.provider || {};
  const active = provider.active || "github_models";
  const activeCfg = (provider.options || {})[active] || {};

  $("#setup-bot-name").value = persona.name || "";
  $("#setup-bot-tone").value = persona.tone || "";
  $("#setup-provider-active").value = active;
  $("#setup-provider-base-url").value = activeCfg.base_url || "";
  $("#setup-provider-model").value = activeCfg.model || "";
  $("#setup-provider-key-env").value = activeCfg.api_key_env || "GITHUB_TOKEN";
  $("#setup-sandbox-mode").checked = !!(cfg.security || {}).sandbox_mode;
  $("#setup-allowed-paths").value = ((cfg.security || {}).allowed_paths || []).join(", ");
  $("#setup-max-agents").value = (cfg.agents || {}).max_active || 4;

  $("#setup-state-view").textContent = JSON.stringify(state, null, 2);
}

async function loadSetupState() {
  const state = await api("/setup/state");
  fillSetupForm(state);
  $("#config-editor").value = JSON.stringify(state.config || {}, null, 2);
}

$("#chat-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const session_id = $("#session-id").value.trim() || "default";
  const text = $("#chat-input").value.trim();
  if (!text) return;
  appendMsg("user", text);
  $("#chat-input").value = "";
  try {
    const out = await api("/chat", { method: "POST", body: JSON.stringify({ session_id, text }) });
    appendMsg("bot", out.reply || "(leer)");
  } catch (err) {
    appendMsg("bot", `Fehler: ${err.message}`);
  }
});

$("#refresh-agents").addEventListener("click", async () => {
  const out = await api("/agents");
  $("#agents-view").textContent = JSON.stringify(out, null, 2);
});

$("#refresh-audit").addEventListener("click", async () => {
  const out = await api("/audit?limit=100");
  $("#audit-view").textContent = JSON.stringify(out, null, 2);
});

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
    allowed_paths: $("#setup-allowed-paths").value.split(",").map((v) => v.trim()).filter(Boolean),
    max_active_agents: Number($("#setup-max-agents").value || 4),
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
    $("#refresh-agents").click();
    $("#refresh-audit").click();
    const interactions = await api("/interactions?limit=20");
    interactions.events.reverse().forEach((evt) => {
      appendMsg("user", evt.user_text);
      if (evt.bot_text) appendMsg("bot", evt.bot_text);
    });
  } catch (err) {
    appendMsg("bot", `Init-Fehler: ${err.message}`);
  }
})();
