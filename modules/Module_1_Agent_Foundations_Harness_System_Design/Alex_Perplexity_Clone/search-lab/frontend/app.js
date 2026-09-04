// Relative, not "/api": served at / locally and at /lab/ in the deployment.
const API = "api";

const documentsInput = document.getElementById("documents");
const resetDocsBtn = document.getElementById("reset-docs");
const thresholdInput = document.getElementById("threshold");
const thresholdVal = document.getElementById("threshold-val");
const engineInfo = document.getElementById("engine-info");
const headerMeta = document.getElementById("header-meta");
const form = document.getElementById("search-form");
const queryInput = document.getElementById("query");
const searchBtn = document.getElementById("search-btn");
const samplesEl = document.getElementById("samples");
const sampleWhy = document.getElementById("sample-why");
const verdictEl = document.getElementById("verdict");
const keywordResults = document.getElementById("keyword-results");
const semanticResults = document.getElementById("semantic-results");
const semanticSub = document.getElementById("semantic-sub");
const workingWrap = document.getElementById("working-wrap");
const workingEl = document.getElementById("working");
const showKeyword = document.getElementById("show-keyword");
const showSemantic = document.getElementById("show-semantic");
const colKeyword = document.getElementById("col-keyword");
const colSemantic = document.getElementById("col-semantic");
const togglesHint = document.getElementById("toggles-hint");

let setup = null;
let lastResponse = null;

function currentDocuments() {
  return documentsInput.value
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);
}

function renderSamples() {
  samplesEl.innerHTML = "";
  (setup.samples || []).forEach((s) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "sample";
    btn.textContent = s.query;
    btn.addEventListener("click", () => {
      queryInput.value = s.query;
      sampleWhy.textContent = s.why;
      sampleWhy.hidden = false;
      runSearch();
    });
    samplesEl.appendChild(btn);
  });
}

// One result row, shared by both columns so the two are visually comparable.
function resultRow(rank, text, score, max, opts = {}) {
  const row = document.createElement("div");
  row.className = "result" + (opts.dim ? " dim" : "") + (opts.highlight ? " highlight" : "");

  const rankEl = document.createElement("div");
  rankEl.className = "result-rank";
  rankEl.textContent = rank;

  const mid = document.createElement("div");
  mid.className = "result-mid";
  const docEl = document.createElement("div");
  docEl.className = "result-doc";
  docEl.textContent = text;
  mid.appendChild(docEl);

  if (opts.badge) {
    const badge = document.createElement("span");
    badge.className = "result-badge " + (opts.badgeKind || "");
    badge.textContent = opts.badge;
    mid.appendChild(badge);
  }

  const right = document.createElement("div");
  right.className = "result-right";
  const bar = document.createElement("span");
  bar.className = "result-bar";
  const fill = document.createElement("span");
  fill.className = "result-fill " + (opts.kind || "");
  fill.style.width = Math.max(0, Math.round((score / (max || 1)) * 100)) + "%";
  bar.appendChild(fill);
  const val = document.createElement("span");
  val.className = "result-val";
  val.textContent = score.toFixed(3);
  right.appendChild(bar);
  right.appendChild(val);

  row.appendChild(rankEl);
  row.appendChild(mid);
  row.appendChild(right);
  return row;
}

function renderKeyword(data) {
  keywordResults.innerHTML = "";
  const docs = data.documents;
  const rows = data.keyword.results;
  const max = Math.max(...rows.map((r) => r.score), 0.0001);
  const matched = rows.filter((r) => r.matched);

  if (!matched.length) {
    const none = document.createElement("div");
    none.className = "nothing";
    none.textContent =
      "Nothing matched. Not one word in the question appears in any document, so the index has nowhere to look.";
    keywordResults.appendChild(none);
  }

  // Only hint at the other engine's findings when it is actually on screen,
  // otherwise the badge gives away the reveal.
  const compare = showSemantic.checked;
  const semanticOnly = new Set(
    (compare && data.verdict && data.verdict.semantic_only) || []
  );
  rows.forEach((r, i) => {
    const missed = r.score <= 0 && semanticOnly.has(r.doc);
    keywordResults.appendChild(
      resultRow(i + 1, docs[r.doc], r.score, max, {
        kind: "kw",
        dim: r.score <= 0,
        highlight: missed,
        badge: missed ? "missed — the other engine found this" : null,
        badgeKind: "miss",
      })
    );
  });
}

function renderSemantic(data) {
  semanticResults.innerHTML = "";
  if (!data.semantic) {
    const err = document.createElement("div");
    err.className = "nothing";
    err.textContent = "Embedding model unavailable: " + (data.semantic_error || "unknown");
    semanticResults.appendChild(err);
    return;
  }
  const docs = data.documents;
  const rows = data.semantic.results;
  const max = Math.max(...rows.map((r) => r.score), 0.0001);
  const threshold = (data.verdict && data.verdict.threshold) || 0;
  const compare = showKeyword.checked;
  const semanticOnly = new Set(
    (compare && data.verdict && data.verdict.semantic_only) || []
  );

  rows.forEach((r, i) => {
    const only = semanticOnly.has(r.doc);
    semanticResults.appendChild(
      resultRow(i + 1, docs[r.doc], r.score, max, {
        kind: "sem",
        dim: r.score < threshold,
        highlight: only,
        badge: only ? "found by meaning alone" : null,
        badgeKind: "only",
      })
    );
  });
}

function renderWorking(data) {
  workingEl.innerHTML = "";
  const docs = data.documents;

  const intro = document.createElement("p");
  intro.className = "hint";
  intro.textContent =
    "Each word of the question is looked up in the index. A word that is not there contributes nothing at all — that is the whole failure mode.";
  workingEl.appendChild(intro);

  data.keyword.working.forEach((w) => {
    const block = document.createElement("div");
    block.className = "term" + (w.in_index ? "" : " absent");

    const head = document.createElement("div");
    head.className = "term-head";
    const name = document.createElement("code");
    name.textContent = w.term;
    head.appendChild(name);
    const state = document.createElement("span");
    state.className = "term-state";
    state.textContent = w.in_index
      ? `in ${w.document_frequency} document${w.document_frequency === 1 ? "" : "s"}`
      : "not in the index — contributes nothing";
    head.appendChild(state);
    block.appendChild(head);

    w.hits.forEach((h) => {
      const line = document.createElement("div");
      line.className = "term-hit";
      line.textContent = `+${h.contribution.toFixed(3)}  ${docs[h.doc]}`;
      block.appendChild(line);
    });

    workingEl.appendChild(block);
  });
}

function renderVerdict(data) {
  if (!data.verdict) {
    verdictEl.hidden = true;
    return;
  }
  const v = data.verdict;
  verdictEl.hidden = false;
  verdictEl.className = "verdict";

  let text;
  if (v.semantic_only.length && !data.keyword.matched_count) {
    text =
      `Keyword search found nothing. Meaning-based search found ${v.semantic_only.length} document` +
      `${v.semantic_only.length === 1 ? "" : "s"}. The words differ; the meaning does not.`;
    verdictEl.classList.add("win");
  } else if (v.semantic_only.length) {
    text =
      `${v.semantic_only.length} document${v.semantic_only.length === 1 ? "" : "s"} ` +
      `only meaning-based search could find, and ${v.both.length} both agree on.`;
    verdictEl.classList.add("win");
  } else if (v.keyword_only.length) {
    text = `Keyword search matched ${v.keyword_only.length} document${v.keyword_only.length === 1 ? "" : "s"} the semantic threshold missed. Literal matching is not always worse.`;
    verdictEl.classList.add("even");
  } else {
    text = "Both approaches agree on this question. Exact words were enough.";
    verdictEl.classList.add("even");
  }
  verdictEl.textContent = text;
}


// Presenters usually want to show one engine, let the room commit to an
// answer, and only then reveal the other. The verdict compares the two, so it
// stays hidden until both are on screen.
function applyEngineVisibility() {
  const kw = showKeyword.checked;
  const sem = showSemantic.checked;

  // Never let both be switched off - there would be nothing to look at.
  if (!kw && !sem) {
    showSemantic.checked = true;
    return applyEngineVisibility();
  }

  colKeyword.hidden = !kw;
  colSemantic.hidden = !sem;

  const both = kw && sem;
  verdictEl.classList.toggle("hidden-by-toggle", !both);
  if (!both) {
    verdictEl.hidden = true;
  } else if (lastResponse) {
    renderVerdict(lastResponse);
  }

  if (lastResponse) {
    renderKeyword(lastResponse);
    renderSemantic(lastResponse);
  }

  togglesHint.textContent = both
    ? ""
    : kw
    ? "semantic hidden — reveal it once the room has judged these results"
    : "keyword hidden";
}

showKeyword.addEventListener("change", applyEngineVisibility);
showSemantic.addEventListener("change", applyEngineVisibility);

async function runSearch() {
  const query = queryInput.value.trim();
  if (!query) return;
  searchBtn.disabled = true;
  searchBtn.textContent = "Searching...";

  try {
    const res = await fetch(`${API}/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query,
        documents: currentDocuments(),
        threshold: parseFloat(thresholdInput.value),
      }),
    });
    const data = await res.json();
    lastResponse = data;

    renderKeyword(data);
    renderSemantic(data);
    renderWorking(data);
    workingWrap.hidden = false;
    applyEngineVisibility();
    if (data.semantic) {
      semanticSub.textContent = `${data.semantic.model.split("/").pop()} · ${data.semantic.dimensions} dims`;
    }
  } catch (err) {
    verdictEl.hidden = false;
    verdictEl.className = "verdict error";
    verdictEl.textContent = "Search failed: " + err.message;
  } finally {
    searchBtn.disabled = false;
    searchBtn.textContent = "Search both";
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  sampleWhy.hidden = true;
  runSearch();
});

thresholdInput.addEventListener("input", () => {
  thresholdVal.textContent = parseFloat(thresholdInput.value).toFixed(2);
  if (lastResponse) runSearch();
});

resetDocsBtn.addEventListener("click", () => {
  documentsInput.value = (setup.documents || []).join("\n");
});

async function init() {
  const res = await fetch(`${API}/setup`);
  setup = await res.json();

  documentsInput.value = (setup.documents || []).join("\n");
  thresholdVal.textContent = parseFloat(thresholdInput.value).toFixed(2);
  renderSamples();

  headerMeta.textContent = setup.model_ready
    ? "model ready"
    : "loading embedding model...";

  engineInfo.innerHTML = "";
  [
    ["Keyword", setup.tokenizer + ", then tf × log(N / (df + 1))"],
    ["Semantic", setup.model],
  ].forEach(([k, v]) => {
    const row = document.createElement("div");
    row.className = "engine-row";
    const label = document.createElement("div");
    label.className = "engine-label";
    label.textContent = k;
    const val = document.createElement("div");
    val.className = "engine-val";
    val.textContent = v;
    row.appendChild(label);
    row.appendChild(val);
    engineInfo.appendChild(row);
  });

  // The first embedding call loads the model, which is slow; say so rather
  // than letting the first search look broken.
  if (!setup.model_ready) {
    const poll = setInterval(async () => {
      const s = await (await fetch(`${API}/setup`)).json();
      if (s.model_ready || s.model_error) {
        clearInterval(poll);
        headerMeta.textContent = s.model_error ? "embedding model failed" : "model ready";
      }
    }, 2000);
  }

  queryInput.value = (setup.samples && setup.samples[0] && setup.samples[0].query) || "";
  applyEngineVisibility();
}

// --- Access gate -----------------------------------------------------------
// The deployment sits behind a password because live API keys are behind it.
// Locally APP_PASSWORD is unset, the gate reports itself as not required, and
// none of this runs. The cookie is shared with the assistant, so one login
// covers both.

const gateEl = document.getElementById("gate");
const gateForm = document.getElementById("gate-form");
const gatePassword = document.getElementById("gate-password");
const gateError = document.getElementById("gate-error");
const gateSubmit = document.getElementById("gate-submit");

function showGate(message) {
  gateEl.hidden = false;
  if (message) {
    gateError.textContent = message;
    gateError.hidden = false;
  }
  gatePassword.focus();
}

gateForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  gateError.hidden = true;
  gateSubmit.disabled = true;
  gateSubmit.textContent = "Checking...";
  try {
    const res = await fetch(`${API}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: gatePassword.value }),
    });
    const data = await res.json();
    if (data.ok) {
      gateEl.hidden = true;
      init();
    } else {
      gateError.textContent = data.error || "Incorrect password.";
      gateError.hidden = false;
      gatePassword.select();
    }
  } catch (err) {
    gateError.textContent = "Could not reach the server.";
    gateError.hidden = false;
  } finally {
    gateSubmit.disabled = false;
    gateSubmit.textContent = "Enter";
  }
});

async function bootstrap() {
  try {
    const gate = await (await fetch(`${API}/gate`)).json();
    if (!gate.required) return init();
    // A valid cookie from an earlier visit means no need to ask again.
    const probe = await fetch(`${API}/setup`);
    if (probe.ok) return init();
    showGate();
  } catch (err) {
    showGate("Could not reach the server.");
  }
}

bootstrap();
