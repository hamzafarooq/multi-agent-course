/*
 * FDE · Assignment 1 · Live Translate Widget  (PROVIDED — do not rewrite)
 * -----------------------------------------------------------------------
 * A self-contained, dependency-free translation widget for any web page.
 * It translates the whole page into Mexican Spanish on demand and can
 * restore the original English.
 *
 * It runs in three environments unchanged:
 *   1. Pasted into the DevTools console      (see ../loader/console-snippet.js)
 *   2. Loaded as a Chrome extension          (see ../extension/)
 *   3. Injected via <script> tag             (served by the Node gateway at /widget.js)
 *
 * It talks ONLY to your Node gateway (default http://localhost:8787), using
 * POST /translate/batch. Your job is to build the backend so this lights up.
 * You do not need to edit this file — reading it tells you what the backend
 * must return.
 *
 * Override config before load with:  window.FDE_CONFIG = { API_URL: "..." }
 */
(function () {
  "use strict";

  if (window.__FDE_TRANSLATE_LOADED__) {
    console.warn("[FDE] Widget already loaded on this page.");
    return;
  }
  window.__FDE_TRANSLATE_LOADED__ = true;

  const CONFIG = Object.assign(
    {
      API_URL: "http://localhost:8787", // your Node gateway
      TARGET: "es-MX", // Mexican Spanish
      BATCH_SIZE: 40, // nodes per /translate/batch call
    },
    window.FDE_CONFIG || {}
  );

  // Resolve the backend URL LATE — at call time, not once at load. When the
  // widget is injected as a content script, window.FDE_CONFIG can be populated
  // asynchronously (e.g. after the extension reads chrome.storage), which races
  // this module's synchronous load. Snapshotting API_URL above would lose that
  // race and get stuck on the default; reading it per use means the current
  // value always wins, no matter how the widget was loaded.
  function apiUrl() {
    return (window.FDE_CONFIG && window.FDE_CONFIG.API_URL) || CONFIG.API_URL;
  }

  // ---- state --------------------------------------------------------------
  let panelOpen = false;
  let busy = false;
  const originalText = new Map(); // textNode -> original string (for Restore)

  // ---- icons (Tabler glyphs — no emoji, no hand-drawn paths) --------------
  const ICON_LANG =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 5h7"/><path d="M9 3v2c0 4.418 -2.239 8 -5 8"/><path d="M5 9c0 2.144 2.952 3.908 6.7 4"/><path d="M12 20l4 -9l4 9"/><path d="M19.1 18h-6.2"/></svg>';
  const ICON_X =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 6l-12 12"/><path d="M6 6l12 12"/></svg>';

  // ---- styles -------------------------------------------------------------
  // Design tokens: one accent (emerald), one radius scale (pill FAB/badges,
  // 16px panel, 10px controls), off-black surfaces, tinted shadows.
  const css = `
  .fde-root, .fde-root *{box-sizing:border-box}
  .fde-fab{position:fixed;right:22px;bottom:22px;width:54px;height:54px;border-radius:999px;
    display:flex;align-items:center;justify-content:center;cursor:pointer;z-index:2147483647;
    color:#fff;background:#0b0b0c;border:1px solid rgba(255,255,255,.12);
    box-shadow:0 10px 30px rgba(11,11,12,.28), inset 0 1px 0 rgba(255,255,255,.14);
    transition:transform .16s cubic-bezier(.16,1,.3,1), box-shadow .16s ease}
  .fde-fab svg{width:24px;height:24px}
  .fde-fab:hover{transform:translateY(-1px) scale(1.05);box-shadow:0 16px 40px rgba(11,11,12,.34), inset 0 1px 0 rgba(255,255,255,.16)}
  .fde-fab:active{transform:scale(.96)}
  .fde-fab:focus-visible{outline:2px solid #10b981;outline-offset:3px}

  .fde-panel{position:fixed;right:22px;bottom:88px;width:320px;max-width:calc(100vw - 44px);
    z-index:2147483647;overflow:hidden;border-radius:16px;
    font:14px/1.45 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif;
    color:#18181b;background:#fff;border:1px solid rgba(9,9,11,.08);
    box-shadow:0 24px 60px rgba(11,11,12,.20), 0 2px 8px rgba(11,11,12,.08);
    opacity:0;transform:translateY(8px) scale(.98);pointer-events:none;
    transition:opacity .16s ease, transform .16s cubic-bezier(.16,1,.3,1)}
  .fde-panel.open{opacity:1;transform:none;pointer-events:auto}

  .fde-head{display:flex;align-items:center;gap:10px;padding:14px 16px;
    background:#0b0b0c;color:#fff}
  .fde-head .fde-hicon{display:flex;width:26px;height:26px;align-items:center;justify-content:center;
    border-radius:8px;background:rgba(255,255,255,.10)}
  .fde-head .fde-hicon svg{width:16px;height:16px}
  .fde-head .fde-title{font-size:13.5px;font-weight:600;letter-spacing:-.01em}
  .fde-head .fde-sub{font-size:11.5px;color:rgba(255,255,255,.55);margin-top:1px}
  .fde-head .fde-x{margin-left:auto;display:flex;width:28px;height:28px;align-items:center;justify-content:center;
    border:none;border-radius:8px;background:transparent;color:rgba(255,255,255,.7);cursor:pointer;transition:background .12s}
  .fde-head .fde-x svg{width:16px;height:16px}
  .fde-head .fde-x:hover{background:rgba(255,255,255,.12);color:#fff}

  .fde-body{padding:16px;display:flex;flex-direction:column;gap:12px}
  .fde-lead{margin:0;color:#52525b;font-size:13px}
  .fde-badges{display:flex;gap:6px;flex-wrap:wrap}
  .fde-badges:empty{display:none}
  .fde-badge{display:inline-flex;align-items:center;font-size:11px;font-weight:600;
    padding:2px 9px;border-radius:999px;background:#f4f4f5;color:#52525b}
  .fde-badge.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-weight:500}
  .fde-badge.hit{background:#dcfce7;color:#15803d}

  .fde-row{display:flex;gap:8px}
  .fde-btn{flex:1;display:inline-flex;align-items:center;justify-content:center;
    border:1px solid rgba(9,9,11,.14);background:#fff;color:#18181b;border-radius:10px;
    padding:10px;font:inherit;font-weight:600;cursor:pointer;
    transition:transform .1s ease, background .12s, border-color .12s, opacity .12s}
  .fde-btn:hover{background:#f4f4f5}
  .fde-btn:active{transform:translateY(1px) scale(.985)}
  .fde-btn:focus-visible{outline:2px solid #10b981;outline-offset:2px}
  .fde-btn[disabled]{opacity:.55;cursor:default;transform:none}
  .fde-btn.primary{background:#0b0b0c;color:#fff;border-color:#0b0b0c}
  .fde-btn.primary:hover{background:#26262b}
  .fde-btn.ghost{border-color:transparent;color:#71717a;font-weight:500}
  .fde-btn.ghost:hover{background:#f4f4f5;color:#18181b}

  .fde-status{font-size:12px;color:#71717a;min-height:16px}
  .fde-status.err{color:#dc2626}

  @media (prefers-color-scheme: dark){
    .fde-panel{color:#f4f4f5;background:#18181b;border-color:rgba(255,255,255,.08);
      box-shadow:0 24px 60px rgba(0,0,0,.5)}
    .fde-lead{color:#a1a1aa}
    .fde-badge{background:#27272a;color:#a1a1aa}
    .fde-badge.hit{background:rgba(22,163,74,.22);color:#4ade80}
    .fde-btn{background:#27272a;color:#f4f4f5;border-color:rgba(255,255,255,.12)}
    .fde-btn:hover{background:#323238}
    .fde-btn.primary{background:#fafafa;color:#0b0b0c;border-color:#fafafa}
    .fde-btn.primary:hover{background:#e4e4e7}
    .fde-btn.ghost{background:transparent;color:#a1a1aa;border-color:transparent}
    .fde-status{color:#a1a1aa}
  }
  @media (prefers-reduced-motion: reduce){
    .fde-fab,.fde-panel,.fde-btn{transition:none}
    .fde-panel{transform:none}
  }
  `;
  const styleEl = document.createElement("style");
  styleEl.textContent = css;
  document.head.appendChild(styleEl);

  // ---- DOM ----------------------------------------------------------------
  const fab = el("button", "fde-fab fde-root");
  fab.type = "button";
  fab.setAttribute("aria-label", "Open Live Translate");
  fab.innerHTML = ICON_LANG;

  const panel = el("div", "fde-panel fde-root");
  panel.setAttribute("role", "dialog");
  panel.setAttribute("aria-label", "Live Translate");
  panel.innerHTML = `
    <div class="fde-head">
      <span class="fde-hicon">${ICON_LANG}</span>
      <div>
        <div class="fde-title">Live Translate</div>
        <div class="fde-sub">English to Mexican Spanish</div>
      </div>
      <button class="fde-x" type="button" aria-label="Close">${ICON_X}</button>
    </div>
    <div class="fde-body">
      <p class="fde-lead">Translate this page into Mexican Spanish, then restore it anytime.</p>
      <div class="fde-badges" id="fde-badges"></div>
      <button class="fde-btn primary" id="fde-page" type="button">Translate page</button>
      <button class="fde-btn ghost" id="fde-restore" type="button">Restore page</button>
      <div class="fde-status" id="fde-status"></div>
    </div>`;

  document.body.appendChild(fab);
  document.body.appendChild(panel);

  const badges = panel.querySelector("#fde-badges");
  const statusEl = panel.querySelector("#fde-status");
  const pageBtn = panel.querySelector("#fde-page");

  // Idle hint shows the resolved backend; refreshed each time the panel opens
  // so a late-arriving FDE_CONFIG is reflected (see apiUrl()).
  setStatus(backendHint());

  // ---- events -------------------------------------------------------------
  fab.addEventListener("click", togglePanel);
  panel.querySelector(".fde-x").addEventListener("click", () => setPanel(false));
  pageBtn.addEventListener("click", translatePage);
  panel.querySelector("#fde-restore").addEventListener("click", restorePage);

  // Extension popup drives the widget through window events (see extension/content.js)
  window.addEventListener("FDE_TRANSLATE_PAGE", translatePage);
  window.addEventListener("FDE_RESTORE_PAGE", restorePage);
  window.addEventListener("FDE_OPEN", () => setPanel(true));

  // ---- actions ------------------------------------------------------------
  function togglePanel() {
    setPanel(!panelOpen);
  }
  function setPanel(open) {
    panelOpen = open;
    panel.classList.toggle("open", open);
    if (open) refreshBackendHint();
  }

  async function translatePage() {
    if (busy) return;
    setPanel(true);
    const nodes = collectTextNodes();
    if (!nodes.length) {
      setStatus("No translatable text found on this page.", true);
      return;
    }
    busy = true;
    pageBtn.disabled = true;
    badges.innerHTML = "";
    let hits = 0,
      totalMs = 0;
    setStatus(`Translating page… (${nodes.length} text chunks)`);
    try {
      for (let i = 0; i < nodes.length; i += CONFIG.BATCH_SIZE) {
        const slice = nodes.slice(i, i + CONFIG.BATCH_SIZE);
        const texts = slice.map((n) => n.nodeValue.trim());
        const r = await postJSON("/translate/batch", { texts, target: CONFIG.TARGET });
        const results = r.results || [];
        if (typeof r.latencyMs === "number") totalMs += r.latencyMs;
        slice.forEach((n, j) => {
          const res = results[j];
          if (!res) return;
          if (res.cached) hits++;
          if (!originalText.has(n)) originalText.set(n, n.nodeValue);
          n.nodeValue = res.translated;
        });
        setStatus(`Translating page… ${Math.min(i + CONFIG.BATCH_SIZE, nodes.length)}/${nodes.length}`);
      }
      renderSummary(nodes.length, hits, totalMs);
      setStatus(`Page translated. Click "Restore page" to undo.`);
    } catch (err) {
      handleError(err);
    } finally {
      busy = false;
      pageBtn.disabled = false;
    }
  }

  function restorePage() {
    originalText.forEach((orig, node) => {
      node.nodeValue = orig;
    });
    originalText.clear();
    badges.innerHTML = "";
    setStatus("Page restored to English.");
  }

  // ---- backend I/O --------------------------------------------------------
  async function postJSON(path, body) {
    const res = await fetch(apiUrl() + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (res.status === 501) throw new NotImplemented(path);
    if (!res.ok) throw new Error("HTTP " + res.status);
    return res.json();
  }

  // ---- helpers ------------------------------------------------------------
  function collectTextNodes() {
    const skip = new Set(["SCRIPT", "STYLE", "NOSCRIPT", "TEXTAREA", "CODE", "PRE"]);
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        if (!node.nodeValue || !node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
        const p = node.parentElement;
        if (!p || skip.has(p.tagName)) return NodeFilter.FILTER_REJECT;
        if (p.closest(".fde-panel,.fde-fab")) return NodeFilter.FILTER_REJECT; // never translate our own UI
        return NodeFilter.FILTER_ACCEPT;
      },
    });
    const nodes = [];
    let n;
    while ((n = walker.nextNode())) nodes.push(n);
    return nodes;
  }

  function renderSummary(chunks, hits, totalMs) {
    badges.innerHTML = "";
    badges.appendChild(badge(chunks + " chunks"));
    badges.appendChild(badge(hits + " cache hit" + (hits === 1 ? "" : "s"), hits ? "hit" : ""));
    if (totalMs) badges.appendChild(badge(Math.round(totalMs) + " ms", "mono"));
  }
  function badge(text, kind) {
    return el("span", "fde-badge" + (kind ? " " + kind : ""), text);
  }
  function setStatus(text, isErr) {
    statusEl.textContent = text;
    statusEl.classList.toggle("err", !!isErr);
  }
  function backendHint() {
    return "Backend: " + apiUrl();
  }
  function refreshBackendHint() {
    // refresh only the idle hint — never clobber progress, results, or errors
    if (statusEl.textContent.startsWith("Backend:")) setStatus(backendHint());
  }
  function handleError(err) {
    if (err instanceof NotImplemented) {
      setStatus(`${err.path} isn't implemented yet — build it in your backend!`, true);
    } else if (err.message && err.message.startsWith("HTTP")) {
      setStatus(`Backend error (${err.message}). Check your gateway/AI-service logs.`, true);
    } else {
      setStatus(`Can't reach backend at ${apiUrl()}. Is your Node gateway running?`, true);
    }
    console.error("[FDE]", err);
  }
  function el(tag, className, text) {
    const e = document.createElement(tag);
    if (className) e.className = className;
    if (text != null) e.textContent = text;
    return e;
  }
  function NotImplemented(path) {
    this.path = path;
    this.name = "NotImplemented";
  }
  NotImplemented.prototype = Object.create(Error.prototype);

  console.log("%c[FDE] Live Translate widget loaded.", "color:#10b981;font-weight:bold");
  console.log("[FDE] Backend:", apiUrl(), "· open the button bottom-right.");
})();
