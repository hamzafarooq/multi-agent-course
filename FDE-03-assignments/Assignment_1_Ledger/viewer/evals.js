// The evaluation page ("/evals"). Provided: do not edit. It renders /evals/report.json, which
// eval/build_report.py wrote from a real run. Nothing here computes or invents a number.
"use strict";

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const md = (t) => (window.marked ? window.marked.parse(String(t ?? "").replace(/</g, "&lt;")) : `<pre>${esc(t)}</pre>`);
const pct = (x) => (typeof x === "number" ? `${Math.round(x * 100)}%` : "n/a");
const num = (v) => (typeof v === "number" ? v.toLocaleString("en-GB", { maximumFractionDigits: 2 }) : esc(v ?? "n/a"));
const badge = (s) => {
  const cls = { pass: "ok", partial: "part", fail: "bad", "for the grader": "" }[s] ?? (s === true ? "ok" : s === false ? "bad" : "");
  const label = s === true ? "pass" : s === false ? "FAIL" : s;
  return `<span class="badge ${cls}">${esc(label)}</span>`;
};
const table = (head, rows) => `<div class="table-wrap"><table><thead><tr>${head.map((h) => `<th>${esc(h)}</th>`).join("")}</tr></thead><tbody>${
  rows.map((r) => `<tr>${r.map((c) => `<td>${c ?? ""}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
const section = (id, title, body, what = "") => `<section class="panel" id="${id}"><h2>${esc(title)}</h2>${what ? `<p class="what">${esc(what)}</p>` : ""}${body}</section>`;

function videoEmbed(url) {
  if (!url) return `<div class="notbuilt"><strong>No video yet.</strong> Pass <code>--video</code> to <code>eval/build_report.py</code>.</div>`;
  let src = null;
  const yt = /(?:youtu\.be\/|youtube\.com\/(?:watch\?v=|shorts\/|embed\/))([\w-]{6,})/.exec(url);
  const loom = /loom\.com\/(?:share|embed)\/([\w-]+)/.exec(url);
  if (yt) src = `https://www.youtube.com/embed/${yt[1]}`;
  else if (loom) src = `https://www.loom.com/embed/${loom[1]}`;
  return src ? `<div class="video"><iframe src="${esc(src)}" title="Demo video" allowfullscreen loading="lazy"></iframe></div>`
    : `<p><a href="${esc(url)}">Watch the demo video</a></p>`;
}

function render(r) {
  const s = r.score || {};
  const auto = r.rubric?.automated || [], manual = r.rubric?.manual || [];
  const sys = r.system || {};
  const out = [];

  document.getElementById("title").textContent = `Evaluation · ${r.student || "unnamed"}`;
  document.getElementById("sub").innerHTML = `Generated ${esc(r.generatedAt || "")}${r.url ? ` for <a href="${esc(r.url)}">${esc(r.url)}</a>` : ""}. Every number came from a run; the grader re-runs the checks against this deployment's <a href="/data/manifest.json">/data</a>.`;

  out.push(section("summary", "Summary", `
    <div class="grid2">
      <div class="card"><div class="muted">Automated rubric</div><div class="score-big">${num(s.automated)} <span class="muted" style="font-size:18px">/ ${num(s.automatedMax)}</span></div>
        <p class="muted">Plus ${num(s.manualMax)} points scored by a person: design, trajectories, your judgment at the gate, the video.</p></div>
      <div class="card"><div class="muted">System verdict</div><p><b>${esc(sys.verdict?.qa_verdict || "no QA verdict")}</b></p>
        <p class="muted">${num(sys.verdict?.pipeline_checks_passed)} of ${num(sys.verdict?.pipeline_checks)} pipeline checks pass · signed off: ${sys.verdict?.signed_off ? "yes" : "no"}</p></div>
    </div>
    <p>The full evaluation report: <a href="/evals/PRODUCT_EVAL.md"><code>/evals/PRODUCT_EVAL.md</code></a> · machine-readable: <a href="/evals/report.json"><code>/evals/report.json</code></a></p>
    <h3>Demo</h3>${videoEmbed(r.video)}`));

  out.push(section("rubric", "Rubric", table(["Row", "Points", "Awarded", "Status", "Evidence"],
    auto.map((x) => [`<b>${esc(x.label)}</b><br><code>${esc(x.id)}</code>${x.selfReported ? `<br><span class="badge part">self-reported: ${esc(x.selfReported)}</span>` : ""}`, num(x.points), num(x.awarded), badge(x.status),
      `<ul>${(x.evidence || []).filter(Boolean).map((e) => `<li>${esc(e)}</li>`).join("")}</ul><details><summary>how it is scored</summary>${esc(x.scoring)}</details>`])
      .concat(manual.map((x) => [`<b>${esc(x.label)}</b><br><code>${esc(x.id)}</code>`, num(x.points), "–", badge("for the grader"), esc(x.check)]))),
    "Automated rows are arithmetic over this run. Manual rows are scored by a person reading this page and watching the video."));

  out.push(section("bars", "The declared bars", table(["Bar (benchmark/sla.json)", "This run", "Target", "Met"],
    (r.bars || []).map((b) => [`<code>${esc(b.name)}</code>`, typeof b.value === "number" && b.value <= 1 && !/runs|caught|open/.test(b.name) ? pct(b.value) : num(b.value),
      `${esc(b.op)} ${typeof b.target === "number" && b.target <= 1 && !/runs|caught|open|decisions/.test(b.name) ? pct(b.target) : num(b.target)}`, badge(b.pass)])),
    "Declared before the first run. A bar is never loosened to pass."));

  const sk = sys.skill;
  out.push(section("skill", "Skill: extract-rules", sk ? table(["Run", "Found", "Not invented", "Fields right", "Quotes verified", "Missed"],
    (sk.runs || []).map((x) => [esc(x.name), pct(x.found), pct(x.precision), pct(x.fields), badge(x.quotes_ok), esc((x.missed || []).join(", "))]))
    + `<p class="muted">Rule sets agree ${pct(sk.consistency)} across runs.</p>` : `<div class="notbuilt">No scored runs. <code>python eval/skill/run_eval.py --runs 3</code></div>`,
    "Fresh-session runs scored against a 30-clause answer key drawn from the PDF itself."));

  out.push(section("gates", "Pipeline checks", table(["Stage", "Check", "Result", "Detail"],
    (sys.gates || []).map((g) => [esc(g.stage), esc(g.check), badge(g.pass), esc(g.detail)]))));

  const pe = sys.planted_errors || {}, gt = sys.golden_thread || {};
  out.push(section("planted", "Planted errors and the golden thread", `
    <p>${pe.baseline_ready ? "The untouched pack passes every check." : "<b>The untouched pack does not pass every check, so no catch counts.</b>"}
      <b>${num(pe.caught)} of ${num(pe.planted)}</b> planted errors caught.</p>
    ${table(["Planted", "Expected", "Caught", "What the check said"], (pe.trials || []).slice(1).map((t) => [esc(t.plant), esc(t.expect), badge(t.caught), esc(t.got)]))}
    <p><b>${num(gt.complete)} of ${num(gt.total)}</b> sampled payments trace back to a verified quote and an approved risk. ${esc(gt.note || "")}</p>
    ${gt.links ? table(["Link", "Payments where it breaks"], gt.links.map((l) => [esc(l), num(gt.broken?.[l])])) : ""}`));

  const tw = sys.teamwork || {}, va = sys.value_added || {};
  out.push(section("team", "Teamwork", (tw.checks || []).length ? table(["Check", "Kind", "Result", "Detail"], tw.checks.map((c) => [esc(c.check), esc(c.kind), badge(c.pass), esc(c.detail)]))
    + (va.first ? table(["Measure", `v${va.first_version}`, `v${va.last_version}`], ["controls", "tests", "sampled transactions", "rules cited"].map((k) => [esc(k), num(va.first[k]), num(va.last[k])])) : "")
    + `<p class="muted">${num(va.challenges)} challenges; by status: ${esc(Object.entries(va.by_status || {}).map(([k, v]) => `${k} ${v}`).join(", "))}.</p>`
    : `<div class="notbuilt">${esc(tw.note || "No team transcripts.")}</div>`, "Scored by script from the run transcripts: who messaged whom, who wrote what, who read what."));

  out.push(section("cost", "Cost", (sys.cost || []).length ? table(["Agent", "Started", "Minutes", "Peak context (tokens)", "Tool calls", "Errored calls"],
    sys.cost.map((c) => [esc(c.agent), esc((c.start || "").slice(0, 16)), num(c.minutes != null ? Math.round(c.minutes) : null), num(c.peak), num(c.calls), num(c.errors)]))
    : `<div class="notbuilt">No agent transcripts found.</div>`, "Read from the transcripts. Budgets: expectations.json."));

  const d = r.design || {};
  out.push(section("design", "Design", d.present === false ? `<div class="notbuilt">${esc(d.note)}</div>`
    : ["Components", "Responsibilities", "Communication", "State", "Trade-offs"].map((h) => `<h3>${h}</h3>${d[h] ? `<div class="md">${md(d[h])}</div>` : '<div class="notbuilt">Not answered.</div>'}`).join(""),
    "In the student's own words. Scored by a person."));

  const iv = d.interview || [];
  out.push(section("interview", "Design interview", iv.length ? iv.map((q) => `<h3>${esc(q.id)}: ${esc(q.question)}</h3><div class="md">${md(q.answer)}</div>`).join("")
    : `<div class="notbuilt">Not done yet: <code>/fde-ledger-eval</code> asks five questions about DESIGN.md and records the answers verbatim.</div>`,
    "Questions asked by the eval skill; answers recorded verbatim. Read alongside DESIGN.md by the person grading it."));

  const lt = r.live_test || {};
  out.push(section("live", "Live test: rules the answer key does not cover", (lt.rows || []).length
    ? `<p><b>${num(lt.correct)} of ${num(lt.checked)}</b> spot-checked rules correct.</p>` + table(["Rule", "Clause", "Verdict", "Note"], lt.rows.map((x) => [esc(x.rule_id), esc(x.clause), esc(x.verdict), esc(x.note)]))
    : `<div class="notbuilt">Not done yet: <code>live-test.md</code>.</div>`,
    "Checked by the student against the PDF: rules the answer key does not score."));

  const tr = r.trajectories || {};
  const traj = (kind, t) => !t ? `<div class="notbuilt">No ${kind} trajectory chosen. ${esc(tr.note || "")}</div>` : `
    <h3>${kind === "successful" ? "A successful run" : "A failing run"}: <code>${esc(t.requestId)}</code> ${t.found ? "" : badge("run log not found")}</h3>
    <p class="muted">${esc(t.agent || "")} · ${esc((t.startedAt || "").slice(0, 16))} · ${num(t.steps?.length)} steps</p>
    <div class="md">${md(t.notes)}</div>
    <details><summary>Every step</summary>${table(["#", "Tool", "OK", "Input (shortened)"], (t.steps || []).map((x) => [x.n, esc(x.tool), x.ok ? "✓" : `✗ ${esc(x.error || "")}`, `<code>${esc(x.what)}</code>`]))}</details>`;
  out.push(section("trajectories", "Two trajectories", traj("successful", tr.successful) + traj("failing", tr.failing), "Read end to end by the student, with what each taught them. This is the human gate on the harness itself."));

  const g = r.gate || {};
  out.push(section("gate", "The auditor's decisions and sign-off", table(["Risk", "Now", "Decision", "Comment"],
    (g.decisions || []).map((x) => [`<code>${esc(x.id)}</code> ${esc(x.risk)}`, esc(x.now), `<b>${esc(x.decision)}</b>`, esc(x.comment)]))
    + `<p>QA verdict in review.md: <b>${esc(g.review_verdict || "none")}</b> · signed off by: <b>${esc(g.signoff?.by || "not signed")}</b>${g.signoff?.date ? ` on ${esc(g.signoff.date)}` : ""} · decision: ${esc(g.signoff?.decision || "")}</p>
      ${g.signoff?.comment ? `<p class="muted">${esc(g.signoff.comment)}</p>` : ""}`));

  const j = r.judges || {};
  const judged = Object.values({ ...(j.subagents || {}), ...(j.teammates || {}) });
  out.push(section("judges", "AI judges (advisory)", judged.length ? table(["Agent", "Dimension", "Score", "Reason"],
    judged.flatMap((x) => (x.scores || []).map((s) => [esc(x.agent), esc(s.dimension), num(s.score), esc(s.reason)])))
    : `<p class="muted">Not run. Optional: <code>python eval/subagents/run_eval.py</code> and <code>python eval/team/run_eval.py</code>.</p>`,
    "A model's review of each agent against the rubric. It informs the human grader and scores no points."));

  const integ = r.integrity || {};
  out.push(section("integrity", "Integrity", `<p>Provided files: ${integ.ok === true ? badge("pass") + " unmodified" : integ.ok === false ? badge("fail") + " " + esc((integ.changed || []).concat(integ.missing || []).join(", ")) : esc(integ.detail || "not checked")}</p>
    ${table(["Red line", "This run", "Detail"], (r.red_lines || []).map((f) => [esc(f.line), f.status === "FLAG" ? badge(false) : f.status === "clear" ? badge(true) : esc(f.status), esc(f.detail)]))}`,
    "Red lines. Any one is an automatic fail. The grader decides; this is what this run can show."));

  document.getElementById("report").innerHTML = out.join("");
}

fetch("/evals/report.json", { cache: "no-store" })
  .then((res) => (res.ok ? res.json() : Promise.reject(new Error(`HTTP ${res.status}`))))
  .then(render)
  .catch(() => {
    document.getElementById("report").innerHTML = `<section class="panel"><h2>No evaluation yet</h2><div class="notbuilt">
      <strong>/evals/report.json is missing.</strong> In Claude Code run <code>/fde-ledger-eval</code> (or <code>python eval/build_report.py --student "Your Name" --video URL</code>),
      then redeploy. This page renders that file and nothing else.</div></section>`;
  });
