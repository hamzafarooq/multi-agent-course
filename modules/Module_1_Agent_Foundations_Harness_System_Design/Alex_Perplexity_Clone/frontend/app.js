const API_BASE = "/api";

const chatWindow = document.getElementById("chat-window");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");
const clearBtn = document.getElementById("clear-btn");
const levelBanner = document.getElementById("level-banner");
const debugCheckbox = document.getElementById("debug-checkbox");
const debugPanel = document.getElementById("debug-panel");
const debugContent = document.getElementById("debug-content");
const levelSelect = document.getElementById("level-select");
const levelSelectDesc = document.getElementById("level-select-desc");
const kbPanel = document.getElementById("kb-panel");
const kbToggle = document.getElementById("kb-toggle");
const kbSummary = document.getElementById("kb-summary");
const kbList = document.getElementById("kb-list");
const ragvizBtn = document.getElementById("ragviz-btn");
const ragvizModal = document.getElementById("ragviz-modal");
const ragvizBackdrop = document.getElementById("ragviz-backdrop");
const ragvizCloseBtn = document.getElementById("ragviz-close-btn");
const levelBadge = document.getElementById("level-badge");
const emptyState = document.getElementById("empty-state");
const debugBackdrop = document.getElementById("debug-backdrop");
const debugCloseBtn = document.getElementById("debug-close-btn");
const howItWorksBtn = document.getElementById("how-it-works-btn");
const hiwBackdrop = document.getElementById("hiw-backdrop");
const hiwModal = document.getElementById("hiw-modal");
const hiwCloseBtn = document.getElementById("hiw-close-btn");
const hiwTitle = document.getElementById("hiw-title");
const hiwNote = document.getElementById("hiw-note");
const hiwSteps = document.getElementById("hiw-steps");
let history = []; // full session history, client-side. Server decides how much to use.
let debugTurns = []; // every turn's debug payload, so the panel shows the whole session
let currentLevel = 1;

const ARROW_SVG =
  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="12" x2="20" y2="12"/><polyline points="14 6 20 12 14 18"/></svg>';

const HOW_IT_WORKS = {
  1: {
    title: "Level 1: LLM Only",
    note: "Every message starts a blank slate — nothing from earlier turns is sent along with it.",
    steps: [
      { type: "box", label: "Your message" },
      { type: "arrow" },
      { type: "box", label: "Alex", variant: "accent" },
      { type: "arrow" },
      { type: "box", label: "Reply" },
    ],
  },
  2: {
    title: "Level 2: + Conversation History",
    note: "Every turn so far — yours and Alex's — is bundled up and resent along with each new message.",
    steps: [
      {
        type: "stack",
        label: "Full history",
        items: ["Turn 1: Q + A", "Turn 2: Q + A", "…", "New message"],
      },
      { type: "arrow" },
      { type: "box", label: "Alex", variant: "accent" },
      { type: "arrow" },
      { type: "box", label: "Reply" },
    ],
  },
  3: {
    title: "Level 3: + Web Search Tool",
    note: "Alex decides whether it needs to search the web before it can answer — try a time-sensitive question (stock price, today's news) vs. one it already knows.",
    layout: "branch",
    before: [{ label: "Your message" }],
    decision: {
      label: "Alex",
      sub: "Does this need current / real-time info?",
      variant: "accent",
    },
    branches: [
      {
        tag: "No",
        tagVariant: "no",
        steps: [{ label: "Answers directly", sub: "from its own knowledge" }],
      },
      {
        tag: "Yes",
        tagVariant: "yes",
        steps: [
          { label: "web_search tool", sub: "runs a real search", variant: "tool" },
          { label: "Alex", sub: "reads results, answers", variant: "accent" },
        ],
      },
    ],
    after: [{ label: "Reply" }],
  },
  4: {
    title: "Level 4: + RAG (document first, web as fallback)",
    note: "Stage 1 happens once, offline, before anyone asks anything. Stage 2 happens on every question. The web_search tool from Level 3 is still available - the model reaches for it only when the document cannot answer.",
    layout: "stages",
    stage1: {
      label: "Stage 1 — Document indexing (once, offline)",
      steps: [
        { label: "Project Management PDF", variant: "rag" },
        { label: "Extract text", sub: "page by page" },
        { label: "Split into chunks", sub: "~900 chars, 150 overlap" },
        {
          label: "Embed each chunk",
          sub: "an embedding model turns every chunk into a list of numbers that encodes its meaning",
          variant: "rag",
        },
        {
          label: "Stored vector index",
          sub: "written to index/ and committed — a numpy matrix in memory at runtime, no external vector database",
          variant: "rag",
        },
      ],
    },
    stage2: {
      label: "Stage 2 — Every question",
      mergeWith: { label: "Your question" },
      mergeLabel: "matched via similarity",
      steps: [
        { label: "Vector search", sub: "cosine similarity between your question and every chunk", variant: "rag" },
        { label: "Top matching excerpts", sub: "with page # + similarity score", variant: "rag" },
        { label: "Alex", sub: "question + excerpts as context", variant: "accent" },
        {
          label: "Enough in the document?",
          sub: "if yes, answer and cite [1][2]. if no, call web_search and cite the URL",
          variant: "tool",
        },
        { label: "Reply", sub: "bracket citations = document, links = web" },
      ],
    },
  },
};

const ICONS = {
  user: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
  assistant: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="8" width="18" height="12" rx="2"/><circle cx="9" cy="14" r="1.5" fill="currentColor" stroke="none"/><circle cx="15" cy="14" r="1.5" fill="currentColor" stroke="none"/><path d="M12 8V4"/><circle cx="12" cy="3" r="1" fill="currentColor" stroke="none"/></svg>',
  search: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
  rag: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>',
  doc: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
};

const LEVEL_INFO = {
  1: {
    label: "Level 1: LLM Only",
    explanation:
      "Level 1 enabled: Each message is sent to the LLM completely on its own, with no memory of earlier turns.",
  },
  2: {
    label: "Level 2: LLM + Conversation History",
    explanation:
      "Level 2 enabled: The chatbot now includes the full conversation history, so it can answer follow-up questions.",
  },
  3: {
    label: "Level 3: LLM + Web Search Tool",
    explanation:
      "Level 3 enabled: The chatbot can now decide when to search the web for external or up-to-date information.",
  },
  4: {
    label: "Level 4: LLM + RAG + Web Search",
    explanation:
      "Level 4 enabled: Everything from Level 3, plus retrieval. Alex answers from the Project Management document first and falls back to web search only when the document does not cover the question.",
  },
};


// --- Level 4 knowledge base -----------------------------------------------
// Shows which documents retrieval is actually running over. Fetched once and
// cached; the index builds in the background so an early call can come back
// not-ready, in which case we retry when the panel is next shown.

let kbData = null;
let kbFetching = false;

function renderKnowledgeBase() {
  kbList.innerHTML = "";

  if (!kbData || !kbData.ready) {
    const wait = document.createElement("div");
    wait.className = "kb-empty";
    wait.textContent = "Building the index…";
    kbList.appendChild(wait);
    return;
  }

  kbSummary.textContent = `Knowledge base · ${kbData.documents.length} documents`;

  kbData.documents.forEach((doc) => {
    const item = document.createElement("div");
    item.className = "kb-item";

    const name = document.createElement("div");
    name.className = "kb-item-name";
    name.textContent = doc.title;
    name.title = doc.title;

    const meta = document.createElement("div");
    meta.className = "kb-item-meta";
    meta.textContent = `${doc.chunks.toLocaleString()} chunks`;

    item.appendChild(name);
    item.appendChild(meta);
    kbList.appendChild(item);
  });

  const total = document.createElement("div");
  total.className = "kb-total";
  total.textContent = `${kbData.total_chunks.toLocaleString()} chunks · ${kbData.model || "embeddings"}`;
  kbList.appendChild(total);
}

async function loadKnowledgeBase() {
  if (kbFetching || (kbData && kbData.ready)) {
    renderKnowledgeBase();
    return;
  }
  kbFetching = true;
  try {
    const res = await fetch(`${API_BASE}/documents`);
    kbData = await res.json();
  } catch (err) {
    kbData = null;
  } finally {
    kbFetching = false;
  }
  renderKnowledgeBase();
  // The index builds on a background thread at boot; check back if it wasn't ready.
  if (kbData && !kbData.ready) setTimeout(loadKnowledgeBase, 3000);
}

function updateKnowledgeBaseVisibility() {
  const show = currentLevel === 4;
  kbPanel.hidden = !show;
  ragvizBtn.hidden = !show;
  if (!show) closeRagviz();
  if (show) loadKnowledgeBase();
}

kbToggle.addEventListener("click", () => {
  const collapsed = kbPanel.classList.toggle("collapsed");
  kbList.hidden = collapsed;
});

// --- "How RAG works" walkthrough -----------------------------------------
// Built for people who have never seen RAG. Every number and every piece of
// text below is pulled live from the real index - nothing is illustrative.

const RAGVIZ_SAMPLE_QUERIES = [
  "What are the payment terms?",
  "What is the highest risk on the program?",
  "Which site is the pilot?",
  "What is a work breakdown structure?",
];

let ragvizDoc = null;
let ragvizChunks = null;
let ragvizQueryTerms = [];

function ragvizStep(n, title, subtitle) {
  const wrap = document.createElement("div");
  wrap.className = "rv-step";

  const head = document.createElement("div");
  head.className = "rv-step-head";

  const num = document.createElement("span");
  num.className = "rv-step-num";
  num.textContent = n;

  const titles = document.createElement("div");
  const t = document.createElement("div");
  t.className = "rv-step-title";
  t.textContent = title;
  titles.appendChild(t);
  if (subtitle) {
    const st = document.createElement("div");
    st.className = "rv-step-sub";
    st.textContent = subtitle;
    titles.appendChild(st);
  }

  head.appendChild(num);
  head.appendChild(titles);
  wrap.appendChild(head);

  const body = document.createElement("div");
  body.className = "rv-step-body";
  wrap.appendChild(body);
  wrap.body = body;
  return wrap;
}

function renderRagvizChunks(container, data) {
  const note = document.createElement("p");
  note.className = "rv-note";
  const split = data.chunks.some((c) => c.overlap_with_previous > 0);
  note.textContent = split
    ? `Long pages are cut into windows of about ${data.chunk_size} characters. Each window repeats the last ${data.chunk_overlap} characters of the one before it — the shaded text below — so a sentence that straddles a boundary is never lost.`
    : `This document's sections are each shorter than the ${data.chunk_size}-character limit, so every section became exactly one chunk and no splitting was needed. Compare with the PDF, where long pages get cut into overlapping windows.`;
  container.appendChild(note);

  data.chunks.forEach((c, i) => {
    const card = document.createElement("div");
    card.className = "rv-chunk";

    const meta = document.createElement("div");
    meta.className = "rv-chunk-meta";
    const label = document.createElement("span");
    label.className = "rv-chunk-label";
    label.textContent = `Chunk ${i + 1}`;
    const stats = document.createElement("span");
    stats.className = "rv-chunk-stats";
    stats.textContent =
      `section ${c.page} · ${c.characters} chars` +
      (c.overlap_with_previous
        ? ` · first ${c.overlap_with_previous} repeated from chunk ${i}`
        : "");
    meta.appendChild(label);
    meta.appendChild(stats);
    card.appendChild(meta);

    const text = document.createElement("div");
    text.className = "rv-chunk-text";
    if (c.overlap_with_previous > 0) {
      const dup = document.createElement("span");
      dup.className = "rv-overlap";
      dup.textContent = c.text.slice(0, c.overlap_with_previous);
      text.appendChild(dup);
      text.appendChild(document.createTextNode(c.text.slice(c.overlap_with_previous)));
    } else {
      text.textContent = c.text;
    }
    card.appendChild(text);
    container.appendChild(card);
  });

  if (data.total_chunks > data.showing) {
    const more = document.createElement("div");
    more.className = "rv-more";
    more.textContent = `…and ${data.total_chunks - data.showing} more chunks from this document.`;
    container.appendChild(more);
  }
}

// A picture of what an embedding actually is: a fixed-length list of numbers,
// most of them small, none of them readable. Drawn from the real vector, not
// an illustration of one.
function buildVectorDiagram(chunk, dimensions) {
  const values = (chunk && chunk.vector_preview) || [];
  if (!values.length) return "";

  const CELL = 17;
  const GAP = 3;
  const MID = 58;
  const H = 128;
  const LEFT = 4;
  const W = LEFT + values.length * (CELL + GAP) + 8;
  const max = Math.max(...values.map((v) => Math.abs(v)), 0.001);

  const svg = [];
  svg.push(
    `<svg viewBox="0 0 ${W} ${H}" width="100%" height="${H}" role="img" ` +
      `aria-label="The first ${values.length} of ${dimensions} numbers that represent this chunk">`
  );

  svg.push(`<text x="${LEFT}" y="12" class="vd-caption">the first ${values.length} of ${dimensions} numbers for this chunk</text>`);
  svg.push(`<line x1="${LEFT}" y1="${MID}" x2="${W - 8}" y2="${MID}" class="vd-axis"/>`);

  values.forEach((v, i) => {
    const x = LEFT + i * (CELL + GAP);
    const height = Math.max(1.5, (Math.abs(v) / max) * 34);
    const y = v >= 0 ? MID - height : MID;
    svg.push(
      `<rect x="${x}" y="${y}" width="${CELL}" height="${height}" rx="2" ` +
        `class="vd-bar ${v >= 0 ? "pos" : "neg"}"><title>dimension ${i + 1}: ${v}</title></rect>`
    );
  });

  svg.push(
    `<text x="${LEFT}" y="${MID + 52}" class="vd-caption">` +
      `no single number means anything on its own — meaning lives in the whole list, and closeness between two lists is the match` +
      `</text>`
  );
  svg.push(`<text x="${LEFT}" y="${MID + 68}" class="vd-caption dim">…and ${dimensions - values.length} more</text>`);
  svg.push("</svg>");
  return svg.join("");
}

function renderRagvizVectors(container, data) {
  const first = data.chunks[0] || {};
  const dims = data.dimensions || 0;

  const note = document.createElement("p");
  note.className = "rv-note";
  note.textContent =
    `Each chunk is sent to an embedding model, which returns ${dims} numbers. ` +
    "Those numbers position the chunk by meaning: two passages that say the same thing in different words end up close together, which is the whole reason retrieval can find something that shares no words with your question.";
  container.appendChild(note);

  const fig = document.createElement("div");
  fig.className = "vd-figure";
  fig.innerHTML = buildVectorDiagram(first, dims);
  container.appendChild(fig);

  const caveat = document.createElement("p");
  caveat.className = "rv-caveat";
  caveat.textContent =
    `Model: ${data.model || "unknown"}. These numbers are computed once, offline, and stored — that is why the app starts instantly and never re-reads the documents. Only your question gets embedded at the moment you ask it.`;
  container.appendChild(caveat);
}

function renderRagvizScores(container, data) {
  container.innerHTML = "";

  const summary = document.createElement("p");
  summary.className = "rv-note";
  summary.textContent =
    `Your question became the terms [${data.query_terms.join(", ")}]. ` +
    `All ${data.total_chunks.toLocaleString()} chunks in the library were scored against it. ` +
    `The top ${data.top_k} that also clear a similarity of ${data.threshold} get used — everything else is thrown away.`;
  container.appendChild(summary);

  const max = Math.max(...data.scored.map((r) => r.score), 0.0001);
  data.scored.forEach((r) => {
    const row = document.createElement("div");
    row.className = "rv-score" + (r.selected ? " selected" : "");

    const rank = document.createElement("div");
    rank.className = "rv-score-rank";
    rank.textContent = "#" + r.rank;

    const mid = document.createElement("div");
    mid.className = "rv-score-mid";
    const doc = document.createElement("div");
    doc.className = "rv-score-doc";
    doc.textContent = r.document;
    const snip = document.createElement("div");
    snip.className = "rv-score-snip";
    snip.textContent = r.text;
    mid.appendChild(doc);
    mid.appendChild(snip);

    const right = document.createElement("div");
    right.className = "rv-score-right";
    const bar = document.createElement("span");
    bar.className = "rv-score-bar";
    const fill = document.createElement("span");
    fill.className = "rv-score-fill";
    fill.style.width = Math.round((r.score / max) * 100) + "%";
    bar.appendChild(fill);
    const val = document.createElement("span");
    val.className = "rv-score-val";
    val.textContent = r.score.toFixed(3);
    const tag = document.createElement("span");
    tag.className = "rv-score-tag " + (r.selected ? "yes" : "no");
    tag.textContent = r.selected ? "used" : r.above_threshold ? "cut by top-k" : "below threshold";
    right.appendChild(bar);
    right.appendChild(val);
    right.appendChild(tag);

    row.appendChild(rank);
    row.appendChild(mid);
    row.appendChild(right);
    container.appendChild(row);
  });

  const outro = document.createElement("p");
  outro.className = "rv-outro";
  outro.textContent =
    `Those ${data.selected_count} winning chunks get pasted, as plain text, into the system prompt before your question is sent. ` +
    "That is the whole trick: search, then paste. The model never 'reads the document' — it only ever sees the text that was pasted in.";
  container.appendChild(outro);
}

async function loadRagvizDocument(title) {
  ragvizDoc = title;
  const chunkBody = document.getElementById("rv-chunks-body");
  const vecBody = document.getElementById("rv-vectors-body");
  chunkBody.innerHTML = '<p class="rv-note">Loading…</p>';
  vecBody.innerHTML = "";
  try {
    const res = await fetch(
      `${API_BASE}/rag/chunks?document=${encodeURIComponent(title)}&limit=6`
    );
    ragvizChunks = await res.json();
  } catch (err) {
    chunkBody.innerHTML = '<p class="rv-note">Could not load chunks.</p>';
    return;
  }
  chunkBody.innerHTML = "";
  vecBody.innerHTML = "";
  renderRagvizChunks(chunkBody, ragvizChunks);
  renderRagvizVectors(vecBody, ragvizChunks);
}

async function runRagvizQuery(query) {
  const body = document.getElementById("rv-scores-body");
  body.innerHTML = '<p class="rv-note">Scoring…</p>';
  try {
    const res = await fetch(`${API_BASE}/rag/score`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    const data = await res.json();
    ragvizQueryTerms = data.query_terms || [];
    renderRagvizScores(body, data);
    // Redraw the diagram so it shows this question's overlap, not the last one's.
    const vb = document.getElementById("rv-vectors-body");
    if (vb && ragvizChunks) {
      vb.innerHTML = "";
      renderRagvizVectors(vb, ragvizChunks);
    }
  } catch (err) {
    body.innerHTML = '<p class="rv-note">Could not score that question.</p>';
  }
}

function buildRagvizShell() {
  const steps = document.getElementById("ragviz-steps");
  steps.innerHTML = "";

  // Step 1 - the document picker
  const s1 = ragvizStep(1, "Start with a document", "Pick anything in the library.");
  const picker = document.createElement("div");
  picker.className = "rv-picker";
  const select = document.createElement("select");
  select.className = "level-select";
  select.id = "rv-doc-select";
  ((kbData && kbData.documents) || []).forEach((d) => {
    const opt = document.createElement("option");
    opt.value = d.title;
    opt.textContent = `${d.title} (${d.chunks} chunks)`;
    select.appendChild(opt);
  });
  select.addEventListener("change", (e) => loadRagvizDocument(e.target.value));
  picker.appendChild(select);
  s1.body.appendChild(picker);
  steps.appendChild(s1);

  // Step 2 - chunking
  const s2 = ragvizStep(2, "Cut it into chunks", "A model cannot be handed a whole book, so the text is sliced up.");
  s2.body.id = "rv-chunks-body";
  steps.appendChild(s2);

  // Step 3 - vectors
  const s3 = ragvizStep(3, "Turn each chunk into numbers", "So one question can be compared against every chunk by arithmetic, in milliseconds.");
  s3.body.id = "rv-vectors-body";
  steps.appendChild(s3);

  // Step 4 - retrieval
  const s4 = ragvizStep(4, "A question picks the winners", "Ask something and watch every chunk get scored and ranked.");
  const qrow = document.createElement("div");
  qrow.className = "rv-query-row";
  const input = document.createElement("input");
  input.type = "text";
  input.id = "rv-query";
  input.className = "rv-query-input";
  input.value = RAGVIZ_SAMPLE_QUERIES[0];
  const go = document.createElement("button");
  go.type = "button";
  go.className = "rv-query-btn";
  go.textContent = "Score it";
  go.addEventListener("click", () => runRagvizQuery(input.value.trim()));
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      runRagvizQuery(input.value.trim());
    }
  });
  qrow.appendChild(input);
  qrow.appendChild(go);
  s4.body.appendChild(qrow);

  const chips = document.createElement("div");
  chips.className = "rv-chips";
  RAGVIZ_SAMPLE_QUERIES.forEach((q) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "rv-chip";
    chip.textContent = q;
    chip.addEventListener("click", () => {
      input.value = q;
      runRagvizQuery(q);
    });
    chips.appendChild(chip);
  });
  s4.body.appendChild(chips);

  const scores = document.createElement("div");
  scores.id = "rv-scores-body";
  s4.body.appendChild(scores);
  steps.appendChild(s4);
}

async function openRagviz() {
  ragvizModal.hidden = false;
  ragvizBackdrop.hidden = false;
  if (!kbData || !kbData.ready) await loadKnowledgeBase();
  buildRagvizShell();
  const first = (kbData && kbData.documents && kbData.documents[1])
    || (kbData && kbData.documents && kbData.documents[0]);
  if (first) {
    const sel = document.getElementById("rv-doc-select");
    if (sel) sel.value = first.title;
    await loadRagvizDocument(first.title);
  }
  runRagvizQuery(RAGVIZ_SAMPLE_QUERIES[0]);
}

function closeRagviz() {
  ragvizModal.hidden = true;
  ragvizBackdrop.hidden = true;
}

ragvizBtn.addEventListener("click", openRagviz);
ragvizCloseBtn.addEventListener("click", closeRagviz);
ragvizBackdrop.addEventListener("click", closeRagviz);

// --- Access gate -----------------------------------------------------------
// The deployed demo sits behind a password because live API keys are behind
// it. Locally APP_PASSWORD is unset, the gate reports itself as not required,
// and none of this runs.

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
    const res = await fetch(`${API_BASE}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: gatePassword.value }),
    });
    const data = await res.json();
    if (data.ok) {
      gateEl.hidden = true;
      startApp();
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
    const gate = await (await fetch(`${API_BASE}/gate`)).json();
    if (!gate.required) return startApp();
    // A valid cookie from an earlier visit means no need to ask again.
    const probe = await fetch(`${API_BASE}/health`);
    if (probe.ok) return startApp();
    showGate();
  } catch (err) {
    showGate("Could not reach the server.");
  }
}

function updateBanner() {
  const info = LEVEL_INFO[currentLevel];
  levelBanner.innerHTML = `<strong>${info.label}</strong><br/>${info.explanation}`;
  levelBadge.textContent = info.label;
  levelSelectDesc.textContent = info.explanation;
}

function hideEmptyState() {
  if (emptyState) emptyState.remove();
}

function addTypingIndicator() {
  const row = document.createElement("div");
  row.className = "typing-indicator";
  row.id = "typing-indicator";
  const avatar = document.createElement("div");
  avatar.className = "avatar assistant";
  avatar.innerHTML = ICONS.assistant;
  const dots = document.createElement("div");
  dots.className = "typing-dots";
  dots.innerHTML = "<span></span><span></span><span></span>";
  row.appendChild(avatar);
  row.appendChild(dots);
  chatWindow.appendChild(row);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function removeTypingIndicator() {
  const el = document.getElementById("typing-indicator");
  if (el) el.remove();
}

// --- Minimal markdown renderer -------------------------------------------
// Deliberately small and dependency-free: the demo must run offline with no
// CDN. Covers what Claude actually emits in chat - headings, bold/italic,
// code, lists, blockquotes, links. Citation markers like [1] are left alone
// and turned into clickable badges afterwards by linkifyCitations().

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function applyEmphasis(text) {
  return text
    .replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
    .replace(/\*\*\*([^*]+)\*\*\*/g, "<strong><em>$1</em></strong>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[^*\w])\*(?!\s)([^*\n]*[^\s*])\*(?![*\w])/g, "$1<em>$2</em>")
    .replace(/(^|[\s(])_(?!\s)([^_\n]*[^\s_])_(?=[\s.,!?):]|$)/g, "$1<em>$2</em>")
    .replace(/~~([^~]+)~~/g, "<del>$1</del>");
}

function renderInline(text) {
  // Split on inline-code spans first so the emphasis rules can never reach
  // inside a code span and mangle its contents.
  return escapeHtml(text)
    .split(/(`[^`]+`)/g)
    .map((part) =>
      part.length > 1 && part.startsWith("`") && part.endsWith("`")
        ? "<code>" + part.slice(1, -1) + "</code>"
        : applyEmphasis(part)
    )
    .join("");
}

function markdownToHtml(src) {
  const lines = src.replace(/\r\n/g, "\n").split("\n");
  const html = [];
  let i = 0;

  const flushList = (tag, items) =>
    html.push(
      "<" + tag + ">" +
        items.map((it) => "<li>" + renderInline(it) + "</li>").join("") +
        "</" + tag + ">"
    );

  while (i < lines.length) {
    const line = lines[i];

    // fenced code block
    const fence = line.match(/^\s*```(\w*)\s*$/);
    if (fence) {
      const body = [];
      i++;
      while (i < lines.length && !/^\s*```\s*$/.test(lines[i])) body.push(lines[i++]);
      i++; // closing fence (or EOF, mid-stream)
      html.push('<pre class="md-code"><code>' + escapeHtml(body.join("\n")) + "</code></pre>");
      continue;
    }

    if (/^\s*$/.test(line)) {
      i++;
      continue;
    }

    if (/^\s*(?:---+|\*\*\*+|___+)\s*$/.test(line)) {
      html.push("<hr/>");
      i++;
      continue;
    }

    const heading = line.match(/^(#{1,6})\s+(.*)$/);
    if (heading) {
      // h1 -> h3: keeps chat-bubble type scale sane
      const level = Math.min(heading[1].length + 2, 6);
      html.push("<h" + level + ">" + renderInline(heading[2]) + "</h" + level + ">");
      i++;
      continue;
    }

    if (/^\s*>\s?/.test(line)) {
      const body = [];
      while (i < lines.length && /^\s*>\s?/.test(lines[i])) {
        body.push(lines[i++].replace(/^\s*>\s?/, ""));
      }
      html.push("<blockquote>" + renderInline(body.join(" ")) + "</blockquote>");
      continue;
    }

    if (/^\s*[-*+]\s+/.test(line)) {
      const items = [];
      while (i < lines.length && /^\s*[-*+]\s+/.test(lines[i])) {
        items.push(lines[i++].replace(/^\s*[-*+]\s+/, ""));
      }
      flushList("ul", items);
      continue;
    }

    if (/^\s*\d+[.)]\s+/.test(line)) {
      const items = [];
      while (i < lines.length && /^\s*\d+[.)]\s+/.test(lines[i])) {
        items.push(lines[i++].replace(/^\s*\d+[.)]\s+/, ""));
      }
      flushList("ol", items);
      continue;
    }

    // paragraph: consume until a blank line or the start of another block
    const para = [];
    while (
      i < lines.length &&
      !/^\s*$/.test(lines[i]) &&
      !/^\s*(?:```|>|#{1,6}\s|[-*+]\s|\d+[.)]\s|---+\s*$)/.test(lines[i])
    ) {
      para.push(lines[i++]);
    }
    html.push("<p>" + renderInline(para.join("\n")).replace(/\n/g, "<br/>") + "</p>");
  }

  return html.join("");
}

// Walks rendered markdown and swaps [1] / [2] text into clickable badges.
// Skips code and links, so a literal [0] inside a snippet is left alone.
function linkifyCitations(root, sources, groupId) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      if (node.parentElement.closest("code, pre, a, .citation-badge")) {
        return NodeFilter.FILTER_REJECT;
      }
      return /\[\d+\]/.test(node.nodeValue)
        ? NodeFilter.FILTER_ACCEPT
        : NodeFilter.FILTER_REJECT;
    },
  });

  const targets = [];
  while (walker.nextNode()) targets.push(walker.currentNode);

  targets.forEach((node) => {
    const frag = document.createDocumentFragment();
    const re = /\[(\d+)\]/g;
    let last = 0;
    let m;
    while ((m = re.exec(node.nodeValue)) !== null) {
      if (m.index > last) {
        frag.appendChild(document.createTextNode(node.nodeValue.slice(last, m.index)));
      }
      frag.appendChild(makeCitationBadge(m[1], sources, groupId));
      last = re.lastIndex;
    }
    if (last < node.nodeValue.length) {
      frag.appendChild(document.createTextNode(node.nodeValue.slice(last)));
    }
    node.parentNode.replaceChild(frag, node);
  });
}

function makeCitationBadge(num, sources, groupId) {
  const source = sources.find((s) => String(s.source_number) === num);
  const badge = document.createElement(source ? "button" : "span");
  badge.className = "citation-badge";
  badge.textContent = num;
  badge.title = source
    ? "Source " + num + " · page " + source.page + " · similarity " + source.score
    : "Source " + num;
  if (source) {
    badge.type = "button";
    badge.addEventListener("click", () => {
      const el = document.getElementById("source-card-" + num + "-" + groupId);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
        el.classList.add("source-card-flash");
        setTimeout(() => el.classList.remove("source-card-flash"), 900);
      }
    });
  }
  return badge;
}

function citedSourceNumbers(text) {
  const nums = new Set();
  const re = /\[(\d+)\]/g;
  let m;
  while ((m = re.exec(text)) !== null) nums.add(m[1]);
  return nums;
}

// Retrieval returns the top-k chunks whether or not they are any good; the
// model decides which (if any) it could actually use. Show only those.
function citedSources(text, sources) {
  if (!sources || !sources.length) return [];
  const cited = citedSourceNumbers(text);
  return sources.filter((s) => cited.has(String(s.source_number)));
}

function renderBubbleContent(bubble, content, sources, groupId) {
  bubble.innerHTML = markdownToHtml(content);
  if (sources && sources.length) linkifyCitations(bubble, sources, groupId);
}

let sourceGroupCounter = 0;

function buildSourcesPanel(sources, groupId, retrievedCount) {
  const panel = document.createElement("div");
  panel.className = "sources-panel";

  const header = document.createElement("div");
  header.className = "sources-panel-header";
  const label =
    retrievedCount && retrievedCount > sources.length
      ? `Cited ${sources.length} of ${retrievedCount} retrieved excerpts`
      : `Cited ${sources.length} excerpt${sources.length === 1 ? "" : "s"}`;
  header.innerHTML = `${ICONS.doc}<span></span>`;
  header.querySelector("span").textContent = label;
  panel.appendChild(header);

  const list = document.createElement("div");
  list.className = "sources-list";
  sources.forEach((s) => {
    const card = document.createElement("div");
    card.className = "source-card";
    card.id = `source-card-${s.source_number}-${groupId}`;
    const meta = document.createElement("div");
    meta.className = "source-card-meta";
    meta.innerHTML = `<span class="source-number">${s.source_number}</span><span class="source-doc"></span><span class="source-loc"></span>`;
    meta.querySelector(".source-doc").textContent = s.document || "document";
    meta.querySelector(".source-loc").textContent = `· ${s.page} · sim ${s.score}`;
    const text = document.createElement("div");
    text.className = "source-card-text";
    text.textContent = s.text.slice(0, 220) + (s.text.length > 220 ? "…" : "");
    card.appendChild(meta);
    card.appendChild(text);
    list.appendChild(card);
  });
  panel.appendChild(list);
  return panel;
}

function addMessage(role, content, sources) {
  hideEmptyState();
  const row = document.createElement("div");
  row.className = `msg-row ${role}`;

  const avatar = document.createElement("div");
  avatar.className = `avatar ${role}`;
  avatar.innerHTML = ICONS[role];

  const bubble = document.createElement("div");
  bubble.className = `msg ${role}`;

  const col = document.createElement("div");
  col.className = "msg-col";
  col.appendChild(bubble);

  if (role === "assistant") {
    const groupId = ++sourceGroupCounter;
    const shown = citedSources(content, sources);
    if (shown.length) col.appendChild(buildSourcesPanel(shown, groupId, sources.length));
    renderBubbleContent(bubble, content, shown, groupId);
  } else {
    bubble.textContent = content;
  }

  row.appendChild(avatar);
  row.appendChild(col);
  chatWindow.appendChild(row);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

// A live assistant bubble that grows as SSE deltas arrive. Sources can land
// before any text does (Level 4 retrieves first), so setSources() is separate.
function beginAssistantMessage() {
  hideEmptyState();
  const row = document.createElement("div");
  row.className = "msg-row assistant";

  const avatar = document.createElement("div");
  avatar.className = "avatar assistant";
  avatar.innerHTML = ICONS.assistant;

  const bubble = document.createElement("div");
  bubble.className = "msg assistant streaming";

  const col = document.createElement("div");
  col.className = "msg-col";
  col.appendChild(bubble);
  row.appendChild(avatar);
  row.appendChild(col);
  chatWindow.appendChild(row);

  const groupId = ++sourceGroupCounter;
  let text = "";
  let sources = [];
  let retrieved = 0;
  let frame = null;

  const paint = () => {
    frame = null;
    const pinned =
      chatWindow.scrollHeight - chatWindow.scrollTop - chatWindow.clientHeight < 80;
    renderBubbleContent(bubble, text, sources, groupId);
    if (pinned) chatWindow.scrollTop = chatWindow.scrollHeight;
  };
  const schedule = () => {
    if (frame === null) frame = requestAnimationFrame(paint);
  };

  return {
    appendText(chunk) {
      text += chunk;
      schedule();
    },
    setSources(next) {
      sources = next || [];
      retrieved = sources.length;
      schedule();
    },
    finish() {
      if (frame !== null) cancelAnimationFrame(frame);
      // Only now is it known which excerpts the answer leaned on.
      sources = citedSources(text, sources);
      if (sources.length) col.appendChild(buildSourcesPanel(sources, groupId, retrieved));
      paint();
      bubble.classList.remove("streaming");
      if (!text) row.remove();
      return text;
    },
  };
}

function addToolIndicator(text, icon) {
  hideEmptyState();
  const div = document.createElement("div");
  div.className = "tool-indicator";
  div.innerHTML = `${icon || ICONS.search}<span></span>`;
  div.querySelector("span").textContent = text;
  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return div;
}

function updateToolIndicator(el, text, variant) {
  if (!el) return;
  el.querySelector("span").textContent = text;
  if (variant) el.classList.add(variant);
}

function addSystemNote(text) {
  hideEmptyState();
  const div = document.createElement("div");
  div.className = "msg system-note";
  div.textContent = text;
  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

const WIRE_ORIGIN_LABELS = {
  new: "appended this turn",
  history: "re-sent from earlier turns",
  turn: "produced during this turn",
  system: "sent on every call",
  context: "assembled fresh for this question",
  absent: "not used at this level",
};

const WIRE_ROLE_LABELS = {
  system: "SYSTEM",
  user: "USER",
  assistant: "ASSISTANT",
  thinking: "INTERNAL REASONING",
  tool_use: "TOOL REQUEST",
  tool_result: "TOOL RESULT",
};

function renderDebug() {
  debugContent.innerHTML = "";

  if (!debugTurns.length) {
    debugContent.innerHTML = '<p class="debug-empty">Send a message to see what happens internally.</p>';
    return;
  }

  // Everything except the payload section describes the most recent turn.
  const debug = debugTurns[debugTurns.length - 1].debug;

  const block = (title, bodyEl) => {
    const wrap = document.createElement("div");
    wrap.className = "debug-block";
    const t = document.createElement("div");
    t.className = "debug-block-title";
    t.textContent = title;
    const b = document.createElement("div");
    b.className = "debug-block-body";
    b.appendChild(bodyEl);
    wrap.appendChild(t);
    wrap.appendChild(b);
    debugContent.appendChild(wrap);
  };

  const pre = (obj) => {
    const p = document.createElement("pre");
    p.textContent = typeof obj === "string" ? obj : JSON.stringify(obj, null, 2);
    return p;
  };

  block("Level", pre(`Level ${debug.level}: ${debug.description || ""}`));

  // The headline section: the literal text handed to the model, for EVERY
  // turn in the session. Seeing turn 2's payload next to turn 1's is the
  // lesson - at Level 1 the earlier turn is visibly absent even though the
  // chat above shows it.
  if (debugTurns.length) {
    const wrap = document.createElement("div");

    if (debugTurns.length > 1) {
      const intro = document.createElement("div");
      intro.className = "wire-note";
      intro.textContent =
        `${debugTurns.length} turns this session. Each block below is one separate ` +
        `call to the model — compare them to see what carried over and what did not.`;
      wrap.appendChild(intro);
    }

    debugTurns.forEach((turn, i) => {
      const li = turn.debug.llm_input;
      if (!li) return;
      const isLast = i === debugTurns.length - 1;

      const section = document.createElement("div");
      section.className = "wire-turn";

      const head = document.createElement("button");
      head.type = "button";
      head.className = "wire-turn-head" + (isLast ? "" : " collapsed");

      const label = document.createElement("span");
      label.className = "wire-turn-label";
      label.textContent = `Turn ${i + 1} · Level ${turn.debug.level}`;

      const q = document.createElement("span");
      q.className = "wire-turn-q";
      q.textContent = turn.question;

      const size = document.createElement("span");
      size.className = "wire-turn-size";
      size.textContent = `${li.characters.toLocaleString()} chars`;

      head.appendChild(label);
      head.appendChild(q);
      head.appendChild(size);

      const body = document.createElement("div");
      body.className = "wire-turn-body";
      body.hidden = !isLast;

      const stats = document.createElement("div");
      stats.className = "wire-stats";
      stats.textContent =
        `${li.message_count} message${li.message_count === 1 ? "" : "s"}` +
        `${li.has_system_prompt ? " + system prompt" : ""} · ` +
        `${li.characters.toLocaleString()} characters · ~${li.approx_tokens.toLocaleString()} tokens`;
      body.appendChild(stats);

      if (turn.debug.what_got_added) {
        const note = document.createElement("div");
        note.className = "wire-note";
        note.textContent = turn.debug.what_got_added;
        body.appendChild(note);
      }

      // Render the payload as the conversation it actually is, so people can
      // see the turns that were (or were not) carried into this call.
      const chat = document.createElement("div");
      chat.className = "wire-chat";
      (li.rows || []).forEach((row) => {
        const item = document.createElement("div");
        item.className = "wire-msg " + row.role + " origin-" + (row.origin || "new");

        const roleEl = document.createElement("div");
        roleEl.className = "wire-msg-role";
        const roleName = document.createElement("span");
        roleName.textContent = WIRE_ROLE_LABELS[row.role] || row.role.toUpperCase();
        if (row.tool) roleName.textContent += ": " + row.tool;
        if (row.label) roleName.textContent += " · " + row.label;
        roleEl.appendChild(roleName);
        if (row.kind) {
          const kind = document.createElement("span");
          kind.className = "wire-kind " + (row.origin === "context" ? "context" : "prompt");
          kind.textContent = row.kind;
          roleEl.appendChild(kind);
        }
        if (WIRE_ORIGIN_LABELS[row.origin]) {
          const badge = document.createElement("span");
          badge.className = "wire-origin " + row.origin;
          badge.textContent = WIRE_ORIGIN_LABELS[row.origin];
          roleEl.appendChild(badge);
        }

        const contentEl = document.createElement("div");
        contentEl.className = "wire-msg-content";
        contentEl.textContent = row.content;

        item.appendChild(roleEl);
        if (row.note) {
          const noteEl = document.createElement("div");
          noteEl.className = "wire-msg-note";
          noteEl.textContent = row.note;
          item.appendChild(noteEl);
        }
        item.appendChild(contentEl);
        chat.appendChild(item);
      });
      body.appendChild(chat);

      const payload = document.createElement("pre");
      payload.className = "wire-payload";
      payload.textContent = li.text;
      payload.hidden = true;
      body.appendChild(payload);

      const rawToggle = document.createElement("button");
      rawToggle.type = "button";
      rawToggle.className = "wire-raw-toggle";
      rawToggle.textContent = "Show as raw text";
      rawToggle.addEventListener("click", () => {
        const showRaw = payload.hidden;
        payload.hidden = !showRaw;
        chat.hidden = showRaw;
        rawToggle.textContent = showRaw ? "Show as conversation" : "Show as raw text";
      });
      body.appendChild(rawToggle);

      head.addEventListener("click", () => {
        body.hidden = !body.hidden;
        head.classList.toggle("collapsed", body.hidden);
      });

      section.appendChild(head);
      section.appendChild(body);
      wrap.appendChild(section);
    });

    block("Exactly what was fed to the model", wrap);
  }

  if (debug.conversation_history_included) {
    block("Conversation history included", pre(debug.conversation_history_included));
  }

  if (debug.tool_calls && debug.tool_calls.length > 0) {
    debug.tool_calls.forEach((tc, i) => {
      block(
        `Tool call ${i + 1}: ${tc.tool}${tc.mocked ? " (mocked)" : ""}`,
        pre({ query: tc.query, results: tc.results })
      );
    });
  } else if (debug.level === 3) {
    block(
      "Tool calls",
      pre(debug.tool_calls_note || "No tool was called — the model answered directly.")
    );
  }

  if (debug.min_similarity_threshold !== undefined) {
    block(
      "Retrieval settings",
      pre({
        query_used_for_retrieval: debug.query_embedded,
        rewritten_from_history: debug.query_rewritten_from_history,
        min_similarity_threshold: debug.min_similarity_threshold,
        chunks_passing_threshold: (debug.retrieved_chunks || []).length,
      })
    );
  }

  if (debug.retrieved_chunks) {
    const container = document.createElement("div");
    if (debug.retrieved_chunks.length === 0) {
      container.textContent = "No relevant chunks found above the similarity threshold.";
    } else {
      debug.retrieved_chunks.forEach((c) => {
        const card = document.createElement("div");
        card.className = "chunk-card";
        const meta = document.createElement("div");
        meta.className = "chunk-meta";
        meta.innerHTML = `${ICONS.doc}<span></span>`;
        meta.querySelector("span").textContent = `Source ${c.source_number} · ${c.document || "document"} · ${c.page} · similarity ${c.score}`;
        const text = document.createElement("div");
        text.textContent = c.text.slice(0, 400) + (c.text.length > 400 ? "..." : "");
        card.appendChild(meta);
        card.appendChild(text);
        container.appendChild(card);
      });
    }
    block("Retrieved RAG chunks", container);
  }

  if (debug.system_prompt_with_context) {
    block("System prompt with retrieved context", pre(debug.system_prompt_with_context));
  }

  if (debug.api_request) {
    block("The actual API request", pre(debug.api_request));
  }
}

async function sendMessage(message) {
  sendBtn.disabled = true;

  let statusEl = null;
  if (currentLevel === 4) {
    statusEl = addToolIndicator("Embedding query and searching document...", ICONS.rag);
  }
  addTypingIndicator();

  const bubble = beginAssistantMessage();
  let sources = [];
  let errored = null;
  let searchEl = null;

  const handle = (evt) => {
    switch (evt.type) {
      case "text":
        removeTypingIndicator();
        bubble.appendText(evt.text);
        break;
      case "sources":
        sources = evt.sources || [];
        bubble.setSources(sources);
        updateToolIndicator(
          statusEl,
          sources.length
            ? `Retrieved ${sources.length} excerpt${sources.length === 1 ? "" : "s"} above the similarity threshold`
            : "No excerpt cleared the similarity threshold \u2014 the model will say it cannot answer from the document",
          sources.length ? "ok" : "warn"
        );
        break;
      case "tool_call":
        if (evt.status === "running") {
          searchEl = addToolIndicator(`Searching the web: "${evt.query}"`, ICONS.search);
        } else {
          updateToolIndicator(
            searchEl,
            evt.mocked
              ? `Web search returned MOCKED results (no TAVILY_API_KEY set) \u2014 "${evt.query}"`
              : `Web search returned ${evt.result_count} live result${evt.result_count === 1 ? "" : "s"} \u2014 "${evt.query}"`,
            evt.mocked ? "warn" : "ok"
          );
        }
        break;
      case "debug":
        debugTurns.push({ question: message, debug: evt.debug });
        if (debugCheckbox.checked) renderDebug();
        break;
      case "error":
        errored = evt.message;
        break;
      default:
        break;
    }
  };

  try {
    const res = await fetch(`${API_BASE}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ level: currentLevel, message, history }),
    });
    if (!res.ok) throw new Error((await res.text()) || `HTTP ${res.status}`);

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let finished = false;

    while (!finished) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const frames = buffer.split("\n\n");
      buffer = frames.pop();
      for (const frame of frames) {
        const line = frame.split("\n").find((l) => l.startsWith("data: "));
        if (!line) continue;
        const evt = JSON.parse(line.slice(6));
        if (evt.type === "done") {
          finished = true;
          break;
        }
        handle(evt);
      }
    }

    removeTypingIndicator();
    const reply = bubble.finish();

    if (errored) {
      addSystemNote(`Error: ${errored}`);
    } else if (currentLevel >= 2) {
      history.push({ role: "user", content: message });
      history.push({ role: "assistant", content: reply });
    }
  } catch (err) {
    removeTypingIndicator();
    bubble.finish();
    addSystemNote(`Error: ${err.message}`);
  } finally {
    sendBtn.disabled = false;
    chatInput.focus();
  }
}

chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;
  addMessage("user", message);
  chatInput.value = "";
  sendMessage(message);
});

function resetChat() {
  history = [];
  debugTurns = [];
  chatWindow.innerHTML = "";
  chatWindow.appendChild(emptyState);
  debugContent.innerHTML = '<p class="debug-empty">Send a message to see what happens internally.</p>';
}

function makeArrow(label, direction) {
  const wrap = document.createElement("div");
  wrap.className = "hiw-arrow-wrap" + (direction === "down" ? " down" : "");
  wrap.innerHTML = ARROW_SVG;
  if (label) {
    const lbl = document.createElement("span");
    lbl.className = "hiw-arrow-label";
    lbl.textContent = label;
    wrap.appendChild(lbl);
  }
  return wrap;
}

function makeBox(step) {
  const box = document.createElement("div");
  box.className = `hiw-box${step.variant ? " " + step.variant : ""}`;

  if (step.type === "stack") {
    const label = document.createElement("div");
    label.className = "hiw-box-label";
    label.textContent = step.label;
    box.appendChild(label);
    const stack = document.createElement("div");
    stack.className = "hiw-stack";
    step.items.forEach((item) => {
      const it = document.createElement("div");
      it.className = "hiw-stack-item";
      it.textContent = item;
      stack.appendChild(it);
    });
    box.appendChild(stack);
  } else {
    const label = document.createElement("div");
    label.className = "hiw-box-label";
    label.textContent = step.label;
    box.appendChild(label);
    if (step.sub) {
      const sub = document.createElement("div");
      sub.className = "hiw-box-sub";
      sub.textContent = step.sub;
      box.appendChild(sub);
    }
  }

  return box;
}

function renderLinearFlow(data) {
  hiwSteps.className = "hiw-steps";
  data.steps.forEach((step) => {
    hiwSteps.appendChild(step.type === "arrow" ? makeArrow(step.label) : makeBox(step));
  });
}

function renderBranchFlow(data) {
  hiwSteps.className = "hiw-steps hiw-steps-branch";

  data.before.forEach((step) => {
    hiwSteps.appendChild(makeBox(step));
    hiwSteps.appendChild(makeArrow(null, "down"));
  });

  hiwSteps.appendChild(makeBox(data.decision));
  hiwSteps.appendChild(makeArrow(null, "down"));

  const branchesRow = document.createElement("div");
  branchesRow.className = "hiw-branches";
  data.branches.forEach((branch) => {
    const col = document.createElement("div");
    col.className = "hiw-branch";

    const tag = document.createElement("div");
    tag.className = `hiw-branch-label ${branch.tagVariant}`;
    tag.textContent = branch.tag;
    col.appendChild(tag);

    branch.steps.forEach((step, i) => {
      if (i > 0) col.appendChild(makeArrow(null, "down"));
      col.appendChild(makeBox(step));
    });

    branchesRow.appendChild(col);
  });
  hiwSteps.appendChild(branchesRow);

  hiwSteps.appendChild(makeArrow("both paths converge", "down"));
  data.after.forEach((step) => hiwSteps.appendChild(makeBox(step)));
}

function renderMergeFlow(data) {
  hiwSteps.className = "hiw-steps hiw-steps-branch";

  const inputsRow = document.createElement("div");
  inputsRow.className = "hiw-branches";
  data.inputs.forEach((step) => {
    inputsRow.appendChild(makeBox(step));
  });
  hiwSteps.appendChild(inputsRow);

  hiwSteps.appendChild(makeArrow(data.mergeLabel, "down"));

  data.after.forEach((step, i) => {
    if (i > 0) hiwSteps.appendChild(makeArrow(null, "down"));
    hiwSteps.appendChild(makeBox(step));
  });
}

function makeStageLabel(text) {
  const el = document.createElement("div");
  el.className = "hiw-stage-label";
  el.textContent = text;
  return el;
}

function renderStagesFlow(data) {
  hiwSteps.className = "hiw-steps hiw-steps-branch";

  hiwSteps.appendChild(makeStageLabel(data.stage1.label));
  data.stage1.steps.forEach((step, i) => {
    if (i > 0) hiwSteps.appendChild(makeArrow(null, "down"));
    hiwSteps.appendChild(makeBox(step));
  });

  hiwSteps.appendChild(makeStageLabel(data.stage2.label));

  const lastStage1 = data.stage1.steps[data.stage1.steps.length - 1];
  const inputsRow = document.createElement("div");
  inputsRow.className = "hiw-branches";
  inputsRow.appendChild(makeBox({ ...lastStage1, variant: (lastStage1.variant || "") + " carried" }));
  inputsRow.appendChild(makeBox(data.stage2.mergeWith));
  hiwSteps.appendChild(inputsRow);

  hiwSteps.appendChild(makeArrow(data.stage2.mergeLabel, "down"));

  data.stage2.steps.forEach((step, i) => {
    if (i > 0) hiwSteps.appendChild(makeArrow(null, "down"));
    hiwSteps.appendChild(makeBox(step));
  });
}

function renderHowItWorks() {
  const data = HOW_IT_WORKS[currentLevel];
  hiwTitle.textContent = data.title;
  hiwNote.textContent = data.note;
  hiwSteps.innerHTML = "";

  if (data.layout === "branch") {
    renderBranchFlow(data);
  } else if (data.layout === "merge") {
    renderMergeFlow(data);
  } else if (data.layout === "stages") {
    renderStagesFlow(data);
  } else {
    renderLinearFlow(data);
  }
}

function openHowItWorks() {
  renderHowItWorks();
  hiwModal.hidden = false;
  hiwBackdrop.hidden = false;
}

function closeHowItWorks() {
  hiwModal.hidden = true;
  hiwBackdrop.hidden = true;
}

howItWorksBtn.addEventListener("click", openHowItWorks);
hiwCloseBtn.addEventListener("click", closeHowItWorks);
hiwBackdrop.addEventListener("click", closeHowItWorks);

levelSelect.addEventListener("change", (e) => {
  currentLevel = parseInt(e.target.value, 10);
  updateBanner();
  updateKnowledgeBaseVisibility();
  resetChat();
  if (!hiwModal.hidden) renderHowItWorks();
});

clearBtn.addEventListener("click", () => {
  resetChat();
  addSystemNote("Chat cleared.");
});

function setDebugPanelOpen(open) {
  debugCheckbox.checked = open;
  debugPanel.hidden = !open;
  debugBackdrop.classList.toggle("active", open);
  // Opening the panel after replies have already streamed in should still
  // show them, not an empty placeholder.
  if (open) renderDebug();
}

debugCheckbox.addEventListener("change", () => {
  setDebugPanelOpen(debugCheckbox.checked);
});

debugCloseBtn.addEventListener("click", () => setDebugPanelOpen(false));
debugBackdrop.addEventListener("click", () => setDebugPanelOpen(false));

function startApp() {
  updateBanner();
  updateKnowledgeBaseVisibility();
}

bootstrap();
