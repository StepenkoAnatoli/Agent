/* Agent — frontend logic. Vanilla JS, no build step. */

"use strict";

const $ = (sel) => document.querySelector(sel);

const state = {
  config: null,
  convs: [],
  activeId: null,
  streaming: false,
  buffer: "",
  textEl: null,
  chipsEl: null,
  metaEl: null,
  abort: null,
  assistantMeta: null,
};

/* ------------------------------------------------ helpers */
function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

function renderMarkdown(md) {
  if (window.marked && window.DOMPurify) {
    return DOMPurify.sanitize(marked.parse(md));
  }
  if (window.marked) {
    return marked.parse(md);
  }
  return `<p>${esc(md)}</p>`;
}

function formatUsage(meta) {
  const parts = [];
  if (meta?.model) parts.push(esc(meta.model));
  const u = meta?.usage;
  if (u && (u.input || u.output)) parts.push(`${(u.input + u.output).toLocaleString()} tokens`);
  if (u && u.tools) parts.push(`${u.tools} tool${u.tools === 1 ? "" : "s"}`);
  if (meta?.cost) parts.push(`≈$${Number(meta.cost).toFixed(4)}`);
  return parts.join(" · ");
}

const TOOL_ICONS = { web_search: "🔍", read_file: "📄", list_dir: "📁" };

/* ------------------------------------------------ API */
async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) {
    let detail = "";
    try { detail = (await res.json()).detail || ""; } catch {}
    throw new Error(detail || `HTTP ${res.status}`);
  }
  return res.json();
}

/* ------------------------------------------------ config & theme */
async function loadConfig() {
  state.config = await api("/api/config");
  const c = state.config.current;
  $("#modelBadgeText").textContent = c.model || "…";
  const dot = $("#statusDot");
  dot.classList.toggle("ok", c.has_key || c.provider === "ollama");
  $("#statusText").textContent = c.has_key
    ? `${state.config.providers.find((p) => p.id === c.provider)?.label} ready`
    : c.provider === "ollama"
      ? "Ollama (local)"
      : "No API key — open Settings";
  document.body.dataset.theme = c.theme || "light";
  $("#themeIcon").textContent = { light: "◐", claude: "☀", dark: "◑" }[c.theme] || "◐";
  $("#themeLabel").textContent = { light: "Light", claude: "Claude", dark: "Dark" }[c.theme] || "Theme";
}

function applyTheme(theme) {
  document.body.dataset.theme = theme;
  $("#themeIcon").textContent = { light: "◐", claude: "☀", dark: "◑" }[theme] || "◐";
  $("#themeLabel").textContent = { light: "Light", claude: "Claude", dark: "Dark" }[theme] || "Theme";
  api("/api/settings", { method: "POST", body: JSON.stringify({ theme }) }).catch(() => {});
}

async function cycleTheme() {
  const order = ["light", "claude", "dark"];
  const next = order[(order.indexOf(document.body.dataset.theme) + 1) % order.length];
  applyTheme(next);
}

/* ------------------------------------------------ conversations */
async function loadConvs() {
  state.convs = (await api("/api/conversations")).conversations;
  renderConvList();
  if (state.convs.length === 0) {
    await newConversation();
  } else if (!state.activeId) {
    selectConversation(state.convs[0].id);
  }
}

function renderConvList() {
  const list = $("#convList");
  list.innerHTML = "";
  for (const conv of state.convs) {
    const item = document.createElement("div");
    item.className = "conv-item" + (conv.id === state.activeId ? " active" : "");
    const title = document.createElement("span");
    title.className = "conv-title";
    title.textContent = conv.title || "New chat";
    const del = document.createElement("button");
    del.className = "conv-del";
    del.textContent = "✕";
    del.title = "Delete chat";
    del.onclick = async (e) => {
      e.stopPropagation();
      await api(`/api/conversations/${conv.id}`, { method: "DELETE" });
      if (state.activeId === conv.id) state.activeId = null;
      await loadConvs();
    };
    item.append(title, del);
    item.onclick = () => selectConversation(conv.id);
    list.appendChild(item);
  }
}

async function newConversation() {
  const conv = await api("/api/conversations", { method: "POST" });
  state.convs.unshift(conv);
  selectConversation(conv.id, true);
  renderConvList();
}

async function selectConversation(id, fresh = false) {
  if (state.streaming) return;
  state.activeId = id;
  $("#messages").innerHTML = "";
  $("#emptyState")?.remove();
  const data = await api(`/api/conversations/${id}`);
  for (const m of data.messages) {
    if (m.role === "user") appendUser(m.content);
    else if (m.role === "assistant") appendAssistant(m.content, m.meta);
  }
  if (fresh || !data.messages.length) showEmptyState();
  renderConvList();
  scrollBottom();
}

function showEmptyState() {
  const div = document.createElement("div");
  div.className = "empty-state";
  div.id = "emptyState";
  div.innerHTML = `
    <div class="empty-logo">✦</div>
    <h1>How can I help you today?</h1>
    <div class="suggestions">
      <button class="suggestion">Research a current topic on the web</button>
      <button class="suggestion">List what's in my workspace and summarize a file</button>
      <button class="suggestion">Explain a concept, step by step</button>
    </div>`;
  div.querySelectorAll(".suggestion").forEach((b) =>
    b.addEventListener("click", () => { $("#input").value = b.textContent; $("#input").focus(); })
  );
  $("#messages").appendChild(div);
}

/* ------------------------------------------------ rendering */
function scrollBottom() {
  $("#messages").scrollTop = $("#messages").scrollHeight;
}

function appendUser(text) {
  $("#emptyState")?.remove();
  const row = document.createElement("div");
  row.className = "msg-row user";
  row.innerHTML = `<div class="msg-inner"><div class="bubble"></div></div>`;
  row.querySelector(".bubble").textContent = text;
  $("#messages").appendChild(row);
  scrollBottom();
}

function appendAssistant(text, meta) {
  $("#emptyState")?.remove();
  const row = document.createElement("div");
  row.className = "msg-row assistant";
  row.innerHTML = `<div class="msg-inner"><div class="avatar">✦</div><div class="bubble"></div></div>`;
  const bubble = row.querySelector(".bubble");
  const content = document.createElement("div");
  content.className = "msg-content";
  content.innerHTML = renderMarkdown(text || "");
  addCopyButtons(content);
  bubble.appendChild(content);

  const tools = meta?.tools;
  if (Array.isArray(tools) && tools.length) {
    bubble.appendChild(renderToolChips(tools));
  }
  const usage = formatUsage(meta);
  if (usage) {
    const m = document.createElement("div");
    m.className = "msg-meta";
    m.textContent = usage;
    bubble.appendChild(m);
  }
  $("#messages").appendChild(row);
  scrollBottom();
  return row;
}

function renderToolChips(tools) {
  const wrap = document.createElement("div");
  wrap.className = "tools-row";
  for (const t of tools) {
    const chip = document.createElement("button");
    chip.className = "tool-chip" + (t.ok === false ? " err" : "");
    chip.innerHTML = `<span>${TOOL_ICONS[t.name] || "🔧"}</span><span class="tname">${esc(t.name)}</span><span>${esc(t.summary || "")}</span>`;
    const detail = document.createElement("div");
    detail.className = "tool-detail";
    detail.textContent = t.result || "";
    chip.onclick = () => detail.classList.toggle("open");
    wrap.appendChild(chip);
    if (t.result) wrap.appendChild(detail);
  }
  return wrap;
}

function addCopyButtons(container) {
  container.querySelectorAll("pre").forEach((pre) => {
    if (pre.querySelector(".copy-btn")) return;
    const btn = document.createElement("button");
    btn.className = "copy-btn";
    btn.textContent = "Copy";
    btn.onclick = async () => {
      try {
        await navigator.clipboard.writeText(pre.innerText);
        btn.textContent = "Copied";
        setTimeout(() => (btn.textContent = "Copy"), 1200);
      } catch {}
    };
    pre.appendChild(btn);
  });
}

/* ------------------------------------------------ chat */
async function send() {
  const input = $("#input");
  const text = input.value.trim();
  if (!text || state.streaming) return;
  input.value = "";
  input.style.height = "auto";

  if (!state.activeId) await newConversation();
  appendUser(text);

  const row = document.createElement("div");
  row.className = "msg-row assistant";
  row.innerHTML = `<div class="msg-inner"><div class="avatar">✦</div><div class="bubble"><div class="typing"><span></span><span></span><span></span></div></div></div>`;
  $("#messages").appendChild(row);
  scrollBottom();

  const bubble = row.querySelector(".bubble");
  const content = document.createElement("div");
  content.className = "msg-content";
  state.textEl = content;
  state.chipsEl = null;
  state.metaEl = null;
  state.toolTrace = [];
  state.buffer = "";
  state.assistantMeta = {};
  state.started = false;
  state.bubble = bubble;
  // Typing dots stay visible until the first streamed event arrives.

  setStreaming(true);
  try {
    const ok = await streamChat(text);
    if (!ok) throw new Error("stream_failed");
  } catch (e) {
    if (e.name !== "AbortError") {
      // Fallback: plain (non-streaming) request
      try {
        setStreaming(false);
        const res = await fetch(`/api/chat/${state.activeId}?plain=1`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: text }),
        });
        const data = await res.json();
        if (data.error) {
          renderError(row, data.error);
        } else {
          row.remove();
          appendAssistant(data.text, data.meta);
        }
      } catch (e2) {
        renderError(row, { kind: "network", message: "Connection lost." });
      }
    }
  } finally {
    setStreaming(false);
  }
}

function setStreaming(on) {
  state.streaming = on;
  $("#sendBtn").hidden = on;
  $("#stopBtn").hidden = !on;
  $("#sendBtn").disabled = on;
}

async function streamChat(text) {
  state.abort = new AbortController();
  const res = await fetch(`/api/chat/${state.activeId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text }),
    signal: state.abort.signal,
  });

  if (!res.ok) {
    let detail = "";
    try { detail = (await res.json()).detail || ""; } catch {}
    throw new Error(detail || `HTTP ${res.status}`);
  }
  const ctype = res.headers.get("content-type") || "";
  if (!ctype.includes("text/event-stream")) {
    throw new Error("not_sse");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";

  // Replace the typing dots with the real content on the first event.
  const startContent = () => {
    if (state.started) return;
    state.started = true;
    state.bubble.innerHTML = "";
    state.bubble.appendChild(state.textEl);
  };

  const ensureChips = () => {
    if (!state.chipsEl) {
      state.chipsEl = document.createElement("div");
      state.chipsEl.className = "tools-row";
      state.textEl.parentElement.appendChild(state.chipsEl);
    }
    return state.chipsEl;
  };
  const rebuildChips = (trace) => {
    const wrap = ensureChips();
    wrap.innerHTML = "";
    for (const t of trace) {
      const chip = document.createElement("button");
      chip.className = "tool-chip" + (t.ok === false ? " err" : "");
      chip.innerHTML = `<span>${TOOL_ICONS[t.name] || "🔧"}</span><span class="tname">${esc(t.name)}</span><span>${esc(t.summary || "")}</span>`;
      const detail = document.createElement("div");
      detail.className = "tool-detail";
      detail.textContent = t.result || "";
      chip.onclick = () => detail.classList.toggle("open");
      wrap.appendChild(chip);
      if (t.result) wrap.appendChild(detail);
    }
  };
  const finishStreaming = () => {
    state.textEl.innerHTML = renderMarkdown(state.buffer);
    addCopyButtons(state.textEl);
    if (state.metaEl) state.metaEl.textContent = formatUsage(state.assistantMeta);
    scrollBottom();
  };

  const handleEvent = (payload) => {
    if (payload.type === "delta") {
      startContent();
      state.buffer += payload.text;
      state.textEl.innerHTML = renderMarkdown(state.buffer) + '<span class="caret"></span>';
      scrollBottom();
    } else if (payload.type === "tool_start") {
      startContent();
      state.toolTrace.push({ name: payload.name, summary: "working…" });
      rebuildChips(state.toolTrace);
    } else if (payload.type === "tool_end") {
      const t = state.toolTrace.find((x) => x.name === payload.name && x.summary === "working…");
      if (t) {
        t.ok = payload.ok;
        t.summary = payload.summary;
        t.result = payload.detail;
      } else {
        state.toolTrace.push({ name: payload.name, ok: payload.ok, summary: payload.summary, result: payload.detail });
      }
      rebuildChips(state.toolTrace);
    } else if (payload.type === "usage") {
      startContent();
      if (!state.metaEl) {
        state.metaEl = document.createElement("div");
        state.metaEl.className = "msg-meta";
        state.textEl.parentElement.appendChild(state.metaEl);
      }
      state.assistantMeta.usage = payload;
      state.metaEl.textContent = formatUsage(state.assistantMeta);
    } else if (payload.type === "done") {
      startContent();
      if (payload.usage) state.assistantMeta.usage = payload.usage;
      if (payload.cost != null) state.assistantMeta.cost = payload.cost;
      if (payload.model) state.assistantMeta.model = payload.model;
      if (payload.tools && payload.tools.length) {
        state.toolTrace = payload.tools;
        rebuildChips(state.toolTrace);
      }
      finishStreaming();
    } else if (payload.type === "error") {
      renderError(state.bubble.closest(".msg-row"), payload);
    } else if (payload.type === "notice") {
      startContent();
      const n = document.createElement("div");
      n.className = "msg-meta";
      n.textContent = "ℹ " + payload.text;
      state.textEl.parentElement.appendChild(n);
    }
  };

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    let idx;
    while ((idx = buf.indexOf("\n\n")) !== -1) {
      const raw = buf.slice(0, idx);
      buf = buf.slice(idx + 2);
      for (const line of raw.split("\n")) {
        if (line.startsWith("data: ")) {
          try { handleEvent(JSON.parse(line.slice(6))); } catch {}
        }
      }
    }
  }
  return true;
}

function renderError(row, error) {
  const bubble = row.querySelector(".bubble");
  bubble.innerHTML = "";
  const div = document.createElement("div");
  div.className = "msg-error";
  div.textContent = error.message || "Something went wrong.";
  if (error.kind === "auth") {
    const btn = document.createElement("button");
    btn.textContent = "Open Settings";
    btn.onclick = () => openSettings();
    div.appendChild(btn);
  }
  bubble.appendChild(div);
}

function stop() {
  if (state.abort) state.abort.abort();
  setStreaming(false);
  if (state.started && state.textEl) {
    state.textEl.innerHTML = renderMarkdown(state.buffer || "_(stopped)_");
  } else if (state.bubble) {
    state.bubble.innerHTML = `<span class="msg-meta">_(stopped)_</span>`;
  }
}

/* ------------------------------------------------ settings modal */
async function openSettings() {
  const cfg = state.config || (await api("/api/config"));
  state.config = cfg;
  const sel = $("#setProvider");
  sel.innerHTML = "";
  for (const p of cfg.providers) {
    const opt = document.createElement("option");
    opt.value = p.id;
    opt.textContent = p.label;
    sel.appendChild(opt);
  }
  sel.value = cfg.current.provider;
  syncSettingsFields(cfg.current.provider);
  $("#setModel").value = cfg.current.model || "";
  $("#setBaseUrl").value = cfg.current.base_url || "";
  $("#setWorkspace").value = cfg.current.workspace || "";
  $("#setMaxIter").value = cfg.current.max_iterations || 6;
  $("#setKey").value = "";
  $("#setKey").placeholder = cfg.current.has_key ? "•••••••• (saved — leave blank to keep)" : "sk-…";
  $("#settingsModal").hidden = false;
  $("#saveStatus").textContent = "";
}

function syncSettingsFields(providerId) {
  const p = state.config.providers.find((x) => x.id === providerId);
  $("#fieldKey").style.display = p.needs_key ? "" : "none";
  $("#fieldBaseUrl").style.display = providerId === "anthropic" ? "none" : "";
  $("#keyHint").textContent = p.key_hint || "";
  $("#setBaseUrl").placeholder = p.base_url_placeholder || "";
  const dl = $("#modelList");
  dl.innerHTML = "";
  for (const m of p.models) {
    const o = document.createElement("option");
    o.value = m;
    dl.appendChild(o);
  }
  if (!$("#setModel").value) $("#setModel").value = p.default_model;
}

async function saveSettings() {
  const body = {
    provider: $("#setProvider").value,
    model: $("#setModel").value.trim() || null,
    base_url: $("#setBaseUrl").value.trim() || null,
    workspace: $("#setWorkspace").value.trim() || null,
    max_iterations: parseInt($("#setMaxIter").value, 10) || 6,
  };
  const key = $("#setKey").value.trim();
  if (key) body.api_key = key;
  try {
    await api("/api/settings", { method: "POST", body: JSON.stringify(body) });
    $("#saveStatus").textContent = "Saved ✓";
    $("#saveStatus").className = "save-status ok";
    await loadConfig();
    setTimeout(() => { $("#settingsModal").hidden = true; $("#saveStatus").textContent = ""; }, 500);
  } catch (e) {
    $("#saveStatus").textContent = "Error: " + e.message;
    $("#saveStatus").className = "save-status";
  }
}

/* ------------------------------------------------ events */
function bindEvents() {
  $("#sendBtn").onclick = send;
  $("#stopBtn").onclick = stop;
  $("#newChatBtn").onclick = newConversation;
  $("#themeBtn").onclick = cycleTheme;
  $("#settingsBtn").onclick = openSettings;
  $("#modelBadge").onclick = openSettings;
  $("#settingsClose").onclick = () => ($("#settingsModal").hidden = true);
  $("#settingsModal").addEventListener("click", (e) => {
    if (e.target === $("#settingsModal")) $("#settingsModal").hidden = true;
  });
  $("#setProvider").onchange = (e) => {
    const p = state.config.providers.find((x) => x.id === e.target.value);
    $("#setModel").value = p.default_model;
    syncSettingsFields(e.target.value);
  };
  $("#saveSettings").onclick = saveSettings;

  $("#sidebarOpen").onclick = () => $("#sidebar").classList.remove("closed");
  $("#sidebarClose").onclick = () => $("#sidebar").classList.add("closed");

  const input = $("#input");
  input.addEventListener("input", () => {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 200) + "px";
  });
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  });
}

/* ------------------------------------------------ boot */
(async function boot() {
  bindEvents();
  try {
    await loadConfig();
    await loadConvs();
  } catch (e) {
    $("#statusText").textContent = "Backend unreachable";
    console.error(e);
  }
})();
