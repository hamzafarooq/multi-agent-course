// The pack viewer ("/"). Provided: do not edit. It renders whatever your run published under /data;
// a stage your harness has not produced yet renders as "Not built yet", which is your progress bar.
"use strict";

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const md = (t) => (window.marked ? window.marked.parse(String(t).replace(/</g, "&lt;")) : `<pre>${esc(t)}</pre>`);
const fmt = (v) => (typeof v === "number" ? (Number.isInteger(v) ? v.toLocaleString("en-GB") : v.toLocaleString("en-GB", { maximumFractionDigits: 2 })) : esc(v));

async function get(path) {
  try {
    const r = await fetch(`/data/${path}`, { cache: "no-store" });
    if (!r.ok) return null;
    return path.endsWith(".json") ? await r.json() : await r.text();
  } catch { return null; }
}

const STAGES = [
  { id: "rules", title: "1 · Rules", todo: "#1 the extract-rules skill", what: "Every testable rule in the council's Contract Rules, each with a verbatim quote verified against its page in the PDF." },
  { id: "analytics", title: "2 · Analytics", todo: "#2 the spend-analyst", what: "The full spend population tested against those rules. Every figure was computed by a script, never by the model." },
  { id: "history", title: "3 · Audit history", todo: "#3 the findings-analyst", what: "Past audit opinions, open actions and the council's own risk scale, each sourced to a page of a committee paper." },
  { id: "register", title: "4 · Risk register", todo: "#4 risk-assessment skill and #5 risk-assessor", what: "Risks rated likelihood × impact on the council's scale. Every rating cites a rule, a metric or a past finding." },
  { id: "gate", title: "5 · The auditor's gate", todo: "#6 your decisions", what: "A human approves, amends or rejects every risk before anything is planned." },
  { id: "pack", title: "6 · The pack", todo: "#7-#9 the agent team and the planner", what: "Risk → control → test step → targeted sample, plus the planning memo and the request list." },
  { id: "challenges", title: "7 · Challenges", todo: "#10 the challenger", what: "Where the plan was weaker than the evidence, what was asked, how the planner answered." },
  { id: "review", title: "8 · QA and sign-off", todo: "#11 the qa-reviewer, #12 check_trace.py, #13 your sign-off", what: "Four automated checks, the verdict, and the auditor's signature." },
  { id: "harness", title: "The harness", todo: "TODOs #1-#11", what: "The skills, sub-agents and teammates that produced this pack, with the tools each is allowed." },
];

function notBuilt(stage, file) {
  return `<div class="notbuilt"><strong>Not built yet.</strong> <code>${esc(file)}</code> is not published. It comes from TODO ${esc(stage.todo)}.</div>`;
}

function table(head, rows) {
  return `<div class="table-wrap"><table><thead><tr>${head.map((h) => `<th>${esc(h)}</th>`).join("")}</tr></thead><tbody>${rows
    .map((r) => `<tr>${r.map((c) => `<td${typeof c === "number" ? ' class="num"' : ""}>${typeof c === "number" ? fmt(c) : c ?? ""}</td>`).join("")}</tr>`)
    .join("")}</tbody></table></div>`;
}

const chip = (label, value) => `<div class="chip"><b>${typeof value === "number" ? fmt(value) : esc(value)}</b>${esc(label)}</div>`;

// ------------------------------------------------------------------ stages
async function rules(stage) {
  const r = await get("outputs/rules.json");
  if (!r) return [false, notBuilt(stage, "outputs/rules.json")];
  const byType = {};
  (r.rules || []).forEach((x) => (byType[x.type] = (byType[x.type] || 0) + 1));
  const params = Object.entries(r.parameters || {}).filter(([, p]) => p && p.value === null);
  const thr = (x) => [x.threshold_low ?? (x.threshold_low_ref ? `{${x.threshold_low_ref}}` : ""), x.threshold_high ?? (x.threshold_high_ref ? `{${x.threshold_high_ref}}` : "")]
    .map((v) => (typeof v === "number" ? "£" + fmt(v) : esc(v))).join(" – ");
  return [true, `
    <div class="chips">${chip("testable rules", (r.rules || []).length)}${Object.entries(byType).map(([k, v]) => chip(k, v)).join("")}
      ${chip("clauses excluded, with reasons", (r.excluded || []).length)}${chip("parameters awaiting the auditor", params.length)}</div>
    <details><summary>All ${(r.rules || []).length} rules</summary>
    ${table(["Rule", "Clause", "Page", "Type", "Condition", "Thresholds", "Approver", "Verbatim quote"],
      (r.rules || []).map((x) => [esc(x.rule_id), esc(x.clause), x.page, esc(x.type), esc(x.condition), thr(x), esc(x.approver || ""), `<details><summary>quote</summary>${esc(x.verbatim_quote)}</details>`]))}
    </details>
    ${(r.notes || []).length ? `<details><summary>Notes for the auditor (${r.notes.length})</summary><ul>${r.notes.map((n) => `<li>${esc(n)}</li>`).join("")}</ul></details>` : ""}`];
}

function scalars(obj, prefix = "", depth = 0, out = []) {
  if (!obj || typeof obj !== "object" || depth > 1) return out;
  for (const [k, v] of Object.entries(obj)) {
    if (typeof v === "number" || typeof v === "boolean") out.push([prefix + k, v]);
    else if (v && typeof v === "object" && !Array.isArray(v) && depth < 1) scalars(v, prefix + k + ".", depth + 1, out);
  }
  return out;
}

async function analytics(stage) {
  const a = await get("outputs/analytics.json");
  if (!a) return [false, notBuilt(stage, "outputs/analytics.json")];
  const p = a.population || {};
  const tests = Object.entries(a.tests || {});
  return [true, `
    <div class="chips">${chip("payments in the files", p.rows_raw ?? "?")}${chip("after logged exclusions", p.rows_after_exclusions ?? "?")}
      ${chip("total £", p.total_gbp ?? "?")}${chip("months covered", p.months_covered ?? "?")}${chip("thresholds from rules.json", (a.thresholds || []).length)}</div>
    <p class="muted">${esc(p.date_min || "")} to ${esc(p.date_max || "")}. ${(p.limitations || []).map(esc).join(" · ")}</p>
    ${table(["Threshold", "Inclusive", "Triggers competition", "Rules"], (a.thresholds || []).map((t) => ["£" + fmt(t.value), t.inclusive ? "yes" : "no", t.competition_triggering ? "yes" : "no", esc((t.rule_ids || []).join(", "))]))}
    ${tests.map(([name, t]) => `<details><summary><code>${esc(name)}</code> ${t && t.skipped ? `<span class="badge part">skipped</span>` : ""}</summary>
      ${t && t.skipped ? `<p>${esc(t.reason)}</p>` : table(["Metric (path)", "Value"], scalars(t).filter(([k]) => !k.startsWith("parameters")).slice(0, 40).map(([k, v]) => [`<code>$.tests.${esc(name)}.${esc(k)}</code>`, typeof v === "number" ? v : esc(String(v))]))}
      ${t && t.caveat ? `<p class="muted">${esc(t.caveat)}</p>` : ""}</details>`).join("")}
    ${(a.skipped || []).length ? `<details><summary>Skipped tests and tiers (${a.skipped.length})</summary><ul>${a.skipped.map((s) => `<li><code>${esc(s.test)}</code>${s.tier ? ` (${esc(s.tier)})` : ""}: ${esc(s.reason)}</li>`).join("")}</ul></details>` : ""}`];
}

async function history(stage) {
  const h = await get("outputs/history.json");
  if (!h) return [false, notBuilt(stage, "outputs/history.json")];
  const sm = h.scoring_method || {};
  return [true, `
    <div class="chips">${chip("audits recorded", (h.audits || []).length)}${chip("risk themes", (h.risk_themes || []).length)}
      ${chip("gaps in the papers", (h.gaps || []).length)}${chip("discrepancies recorded", (h.discrepancies || []).length)}
      ${chip("council scoring method", sm.usable ? "usable" : "not usable")}</div>
    <details><summary>Audits</summary>${table(["ID", "Audit", "Opinion", "Procurement relevance", "Source"],
      (h.audits || []).map((x) => [esc(x.id), esc(x.audit_title), esc(x.opinion || ""), esc(x.procurement_relevance || ""), `${esc(x.source || "")} p.${esc(x.pdf_page ?? "")}`]))}</details>
    ${(h.gaps || []).length ? `<details><summary>Gaps</summary><ul>${h.gaps.map((g) => `<li><b>${esc(g.item)}</b>: ${esc(g.status)}. ${esc(g.consequence)}</li>`).join("")}</ul></details>` : ""}
    ${sm.usable && sm.bands ? `<details><summary>The council's bands</summary>${table(["Level", "From", "To"], sm.bands.map((b) => [esc(b.level), b.score_low ?? "", b.score_high ?? ""]))}</details>` : ""}`];
}

async function mdStage(stage, file, from) {
  const t = await get(file);
  if (!t) return [false, notBuilt(stage, file)];
  const body = from && t.includes(from) ? t.slice(t.indexOf(from)) : t;
  return [true, `<div class="md md-scroll">${md(body)}</div>`];
}

async function pack(stage) {
  const files = [["Planning memo", "outputs/planning-memo.md"], ["Risk-control matrix", "outputs/risk-control-matrix.md"], ["Audit program", "outputs/audit-program.md"]];
  const texts = await Promise.all(files.map(([, f]) => get(f)));
  const figs = await get("outputs/pack-figures.json");
  if (!texts.some(Boolean)) return [false, notBuilt(stage, "outputs/planning-memo.md")];
  const f = (figs && figs.figures) || {};
  const tabs = files.map(([n], i) => `<button role="tab" aria-selected="${i === 0}" data-i="${i}">${esc(n)}</button>`).join("");
  const panes = texts.map((t, i) => `<div class="md md-scroll" data-pane="${i}" ${i ? "hidden" : ""}>${t ? md(t) : notBuilt(stage, files[i][1])}</div>`).join("");
  return [true, `
    <div class="chips">${chip("approved risks planned", f.approved_in_scope ?? "?")}${chip("controls", f.controls ?? "?")}${chip("tests", f.tests ?? "?")}
      ${chip("sampled payments", f.sampled_transactions ?? "?")}${chip("rules cited", f.rules_cited != null ? `${f.rules_cited}/${f.rules_total}` : "?")}${chip("requests to the council", f.pbc_items ?? "?")}</div>
    <div class="tabs" role="tablist">${tabs}</div>${panes}`];
}

async function harness(stage) {
  const agents = ["spend-analyst", "findings-analyst", "risk-assessor", "planner", "challenger", "qa-reviewer"];
  const skills = ["extract-rules", "risk-assessment", "audit-program"];
  const fm = (t) => {
    const m = /^---\s*\n([\s\S]*?)\n---/.exec(t || "");
    const o = {};
    (m ? m[1] : "").split("\n").forEach((l) => { const i = l.indexOf(":"); if (i > 0) o[l.slice(0, i).trim()] = l.slice(i + 1).trim(); });
    return o;
  };
  const a = await Promise.all(agents.map((n) => get(`harness/claude/agents/${n}.md`)));
  const s = await Promise.all(skills.map((n) => get(`harness/claude/skills/${n}/SKILL.md`)));
  const settings = await get("harness/claude/settings.json");
  if (!a.some(Boolean) && !s.some(Boolean)) return [false, notBuilt(stage, ".claude/agents/*.md")];
  const todo = (t) => (t && t.includes("TODO (YOU)") ? ` <span class="badge bad">TODO</span>` : "");
  const teams = settings && settings.env && String(settings.env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS) === "1";
  const allWritten = a.every((t) => t && !t.includes("TODO (YOU)")) && s.every((t) => t && !t.includes("TODO (YOU)")) && teams;
  return [allWritten, `
    <p>Agent teams: ${teams ? '<span class="badge ok">enabled</span>' : '<span class="badge bad">not enabled</span>'}</p>
    ${table(["Skill", "What it does"], skills.map((n, i) => [`<a href="/data/harness/claude/skills/${n}/SKILL.md"><code>${n}</code></a>${todo(s[i])}`, esc(fm(s[i]).description || (s[i] ? "" : "not written"))]))}
    ${table(["Agent", "Role", "Tools", "Memory"], agents.map((n, i) => [`<a href="/data/harness/claude/agents/${n}.md"><code>${n}</code></a>${todo(a[i])}`,
      esc((fm(a[i]).description || (a[i] ? "" : "not written")).slice(0, 220)), esc(fm(a[i]).tools || ""), esc(fm(a[i]).memory || "")]))}`];
}

const RENDER = {
  rules, analytics, history, harness, pack,
  register: (st) => mdStage(st, "outputs/risk-register.md"),
  gate: (st) => mdStage(st, "outputs/auditor-comments.md", "## Decisions"),
  challenges: (st) => mdStage(st, "outputs/challenges.md"),
  review: (st) => mdStage(st, "outputs/review.md"),
};

async function main() {
  const report = await fetch("/evals/report.json", { cache: "no-store" }).then((r) => (r.ok ? r.json() : null)).catch(() => null);
  if (report && report.student) document.getElementById("title").textContent = `Audit planning pack · ${report.student}`;
  const results = await Promise.all(STAGES.map((st) => RENDER[st.id](st).catch((e) => [false, `<div class="notbuilt">Could not render: ${esc(e.message)}</div>`])));
  document.getElementById("panels").innerHTML = STAGES.map((st, i) => `
    <section class="panel" id="${st.id}">
      <div class="panel-head"><h2>${esc(st.title)}</h2>${results[i][0] ? '<span class="badge ok">built</span>' : '<span class="badge bad">not built</span>'}</div>
      <p class="what">${esc(st.what)}</p>${results[i][1]}
    </section>`).join("");
  document.getElementById("pipeline").innerHTML = STAGES.map((st, i) =>
    `<li><a href="#${st.id}"><span class="dot ${results[i][0] ? "ok" : "no"}"></span>${esc(st.title)}</a></li>`).join("");
  document.querySelectorAll(".tabs").forEach((tabs) => tabs.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    const panel = tabs.parentElement;
    tabs.querySelectorAll("button").forEach((x) => x.setAttribute("aria-selected", String(x === b)));
    panel.querySelectorAll("[data-pane]").forEach((p) => (p.hidden = p.dataset.pane !== b.dataset.i));
  }));
}

main();
