#!/usr/bin/env python3
"""Assemble reports/report.json, the evaluation your /evals page renders.

Usage: python eval/build_report.py --student "Your Name" --video https://... [--url https://your-app.vercel.app]
       python eval/build_report.py                      (re-uses the name, video and URL saved last time)
       python eval/build_report.py --no-run             (score the existing reports/system.json; do not re-run)

In order, it:
  1. exports your agent runs (eval/export_runs.py -> runs/),
  2. runs the whole-system eval (eval/run_all.py -> reports/system.json),
  3. runs the course quality kit over runs/ (node quality/check.mjs . -> reports/quality.json),
  4. scores every AUTOMATED rubric row by arithmetic (eval/rubric.json `scoring`),
  5. compares your numbers with the bars in benchmark/sla.json,
  6. reads DESIGN.md (five headings) and trajectories.md (two runs + your notes),
  7. writes reports/report.json and prints the scorecard.

It never writes a number a run did not produce, and it never scores the four
MANUAL rows: a person does. The grader re-runs steps 2 and 4 against your
deployed /data with eval/grade_url.py; a mismatch is a fabricated number.
"""
import os as _os, subprocess as _sp, sys as _sys
if __name__ == "__main__" and _os.name == "nt" and not _sys.flags.utf8_mode:  # Windows: rerun in UTF-8 mode
    _sys.exit(_sp.call([_sys.executable, "-X", "utf8", *_sys.argv]))  # (£, →, curly quotes in the data)
import argparse, hashlib, json, math, re, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESIGN_HEADINGS = ["Components", "Responsibilities", "Communication", "State", "Trade-offs"]
CHALLENGER_TOOLS = {"Read", "Write", "Glob", "Grep"}
TEAM_FLAG = "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"
TODO_MARK = "TODO (YOU)"
AGENTS = ["spend-analyst", "findings-analyst", "risk-assessor", "planner", "challenger", "qa-reviewer"]
# files a student must not change; hashed in eval/integrity.json (text normalised to \n so git's line endings do not matter)
PROVIDED = ["data", "contract", "eval", "quality", "benchmark", "viewer", "expectations.json", "vercel.json",
            ".claude/skills/extract-rules/verify_quotes.py", ".claude/skills/risk-assessment/build_register.py",
            ".claude/skills/audit-program/build_pack.py", ".claude/skills/fde-ledger-eval",
            "scripts/verify_history.py", "scripts/status.py", "scripts/checks/run_checks.py", "scripts/checks/check_quotes.py",
            "scripts/checks/check_numbers.py", "scripts/checks/check_samples.py"]
INTEGRITY_SKIP = ("eval/skill/runs/", "eval/subagents/judgements/", "eval/team/judgements/", "eval/team/results.json",
                  "eval/subagents/report.md", "eval/team/report.md", "eval/skill/report.md", "viewer/dist/", "__pycache__", "eval/integrity.json")


def read_json(p, default=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def run(cmd, root=ROOT, env=None):
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=root, env=env)
    return p.returncode, (p.stdout + p.stderr).strip()


# ------------------------------------------------------------------ integrity
def file_hash(p):
    b = p.read_bytes()
    if b"\0" not in b[:1024]:  # text: hash with \n line endings so a Windows checkout matches
        b = b.replace(b"\r\n", b"\n")
    return hashlib.sha256(b).hexdigest()


def provided_files(root=ROOT):
    out = {}
    for entry in PROVIDED:
        p = root / entry
        files = [p] if p.is_file() else sorted(x for x in p.rglob("*") if x.is_file()) if p.is_dir() else []
        for f in files:
            rel = f.relative_to(root).as_posix()
            if any(s in rel for s in INTEGRITY_SKIP):
                continue
            out[rel] = file_hash(f)
    return out


def integrity(root=ROOT):
    manifest = read_json(root / "eval/integrity.json", {}).get("files", {})
    if not manifest:
        return {"ok": None, "detail": "eval/integrity.json missing", "changed": [], "missing": []}
    now = provided_files(root)
    changed = sorted(f for f, h in manifest.items() if f in now and now[f] != h)
    gone = sorted(f for f in manifest if f not in now)
    return {"ok": not changed and not gone, "changed": changed, "missing": gone,
            "detail": "all provided files unmodified" if not changed and not gone else f"{len(changed)} changed, {len(gone)} missing"}


# ------------------------------------------------------------------ harness facts
def frontmatter(text):
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    fm = {}
    for line in (m.group(1) if m else "").splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm


def harness(root=ROOT):
    """What the student's harness declares: per agent its tools and memory, the team flag, leftover TODOs."""
    agents = {}
    for a in AGENTS:
        p = root / f".claude/agents/{a}.md"
        text = p.read_text(encoding="utf-8") if p.exists() else ""
        fm = frontmatter(text)
        tools = fm.get("tools", "")
        agents[a] = {"exists": bool(text), "tools": [t.strip() for t in tools.split(",") if t.strip()] if TODO_MARK not in tools else [],
                     "tools_declared": bool(tools) and TODO_MARK not in tools, "memory": fm.get("memory", ""),
                     "todo_left": TODO_MARK in text}
    settings = read_json(root / ".claude/settings.json", {}) or {}
    team_on = str((settings.get("env") or {}).get(TEAM_FLAG, "")) == "1"
    todo_files = []
    for p in list((root / ".claude").rglob("*.md")) + [root / "CLAUDE.md", root / "scripts/checks/check_trace.py"]:
        rel = p.relative_to(root).as_posix() if p.exists() else None
        if rel and "fde-ledger-eval" not in rel and TODO_MARK in p.read_text(encoding="utf-8", errors="replace"):
            todo_files.append(rel)
    return {"agents": agents, "agent_teams_enabled": team_on, "todo_files": sorted(todo_files)}


def per_agent_budgets(root=ROOT):
    exp = read_json(root / "expectations.json", {}) or {}
    caps = exp.get("perAgent", {})
    runs = [read_json(p) for p in sorted((root / "runs").glob("*.json"))] if (root / "runs").is_dir() else []
    runs = [r for r in runs if r]
    seen, over = set(), []
    for r in runs:
        a, cap = r.get("agent"), caps.get(r.get("agent"), {})
        seen.add(a)
        mins = (r.get("wallClockSec") or 0) / 60
        if cap.get("maxMinutes") and mins > cap["maxMinutes"]:
            over.append(f"{r['requestId']}: {mins:.0f} min > {cap['maxMinutes']}")
        if cap.get("maxToolCalls") and len(r.get("toolCalls") or []) > cap["maxToolCalls"]:
            over.append(f"{r['requestId']}: {len(r['toolCalls'])} tool calls > {cap['maxToolCalls']}")
        if cap.get("maxPeakTokens") and (r.get("tokens") or 0) > cap["maxPeakTokens"]:
            over.append(f"{r['requestId']}: peak {r['tokens']:,} tokens > {cap['maxPeakTokens']:,}")
    no_run = [a for a in AGENTS if a not in seen]
    return {"runs": len(runs), "over": over, "agents_without_a_run": no_run, "ok": bool(runs) and not over and not no_run}


# ------------------------------------------------------------------ scoring (arithmetic only)
def gate(system, stage, check=None):
    for x in system.get("gates", []):
        if x["stage"] == stage and (check is None or x["check"] == check):
            return x
    return {"pass": False, "detail": "not run"}


def decisions(root=ROOT):
    text = (root / "outputs/auditor-comments.md").read_text(encoding="utf-8") if (root / "outputs/auditor-comments.md").exists() else ""
    rows = []
    for line in text.splitlines():
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) >= 6 and re.fullmatch(r"R-\d+", c[0]):
            rows.append({"id": c[0], "risk": c[1], "now": c[2], "scope": c[3], "decision": c[4].lower(), "comment": "|".join(c[5:]).strip()})
    return rows


def thresholds_traced(root=ROOT):
    an, rules = read_json(root / "outputs/analytics.json"), read_json(root / "outputs/rules.json")
    if not an or not rules:
        return False, "analytics.json or rules.json missing"
    rule_ids = {r["rule_id"] for r in rules.get("rules", [])}
    values = {v for r in rules.get("rules", []) for v in (r.get("threshold_low"), r.get("threshold_high")) if isinstance(v, (int, float))}
    bad = []
    for t in an.get("thresholds", []):
        v = t.get("value")
        if not isinstance(v, (int, float)) or not any(abs(v - x) <= 1 for x in values):
            bad.append(f"{v} is not a threshold in rules.json")
        unknown = [r for r in t.get("rule_ids", []) if r not in rule_ids]
        if unknown:
            bad.append(f"{v} cites unknown rule(s) {unknown}")
    if not an.get("thresholds"):
        bad.append("no thresholds listed")
    return not bad, "; ".join(bad) or f"{len(an['thresholds'])} thresholds, each a rules.json threshold with real rule_ids"


def score_rows(root, system, quality, sla):
    """One dict per automated rubric row: awarded points and the evidence behind them."""
    rows = {}
    bar = sla["sla"]

    # rules_extracted
    sk = system.get("skill")
    if not sk or not sk.get("runs"):
        rows["rules_extracted"] = (0, ["no scored runs: python eval/skill/run_eval.py --runs 3"])
    else:
        runs = sk["runs"]
        worst = lambda k: min((r[k] for r in runs if r[k] is not None), default=None)
        found, prec, fields = worst("found"), worst("precision"), worst("fields")
        quotes = all(r["quotes_ok"] for r in runs)
        ev = [f"{len(runs)} run(s); weakest: found {found:.0%}" if found is not None else f"{len(runs)} run(s)",
              f"not invented {prec:.0%}" if prec is not None else "not invented n/a",
              f"fields right {fields:.0%}" if fields is not None else "fields n/a",
              "quotes verified in every run" if quotes else "a run's quotes FAIL verification"]
        if not quotes or (prec is not None and prec < bar["skill_min_not_invented"]):
            pts = 0
        elif (found or 0) >= bar["skill_min_found"] and (fields or 0) >= bar["skill_min_fields_right"]:
            pts = 15
        elif (found or 0) >= 0.80:
            pts = 10
        else:
            pts = 5
        if len(runs) < bar["skill_min_runs"] and pts > 10:
            pts = 10
            ev.append(f"capped at 10: fewer than {bar['skill_min_runs']} runs")
        rows["rules_extracted"] = (pts, ev)

    # analytics_reproducible
    c = gate(system, "Contract", "analytics.json matches its schema")
    a = gate(system, "Analytics")
    t_ok, t_detail = thresholds_traced(root)
    hard = system.get("hardcoded_thresholds")
    rows["analytics_reproducible"] = (3 * c["pass"] + 4 * a["pass"] + 3 * t_ok,
                                      [f"schema: {c['detail']}", f"self-check: {a['detail']}", f"thresholds: {t_detail}",
                                       (f"note, no points: possible threshold figures typed in scripts, check by hand ({'; '.join(hard[:3])}); SPEC §7.2 says they come only from rules.json"
                                        if hard else "")])

    # history_sourced
    c, h = gate(system, "Contract", "history.json matches its schema"), gate(system, "History")
    rows["history_sourced"] = (2 * c["pass"] + 3 * h["pass"], [f"schema: {c['detail']}", f"verifier: {h['detail']}"])

    # register_traceable
    c, r = gate(system, "Contract", "risk-ratings.json matches its schema"), gate(system, "Register")
    rows["register_traceable"] = (2 * c["pass"] + 5 * bool(r.get("builder_ok")) + 3 * bool(r.get("same_as_fresh_build")),
                                  [f"schema: {c['detail']}", f"builder: {r['detail']}"])

    # human_gate_enforced
    g = gate(system, "Approval gate")
    ratings = read_json(root / "outputs/risk-ratings.json", {}) or {}
    rev = (ratings.get("revision") or {}).get("number", 0)
    ds = decisions(root)
    reasoned = [d for d in ds if d["decision"] in ("amend", "reject") and len(d["comment"]) >= 10]
    rows["human_gate_enforced"] = (6 * g["pass"] + 2 * (isinstance(rev, int) and rev >= 1) + 2 * (len(reasoned) >= bar["min_auditor_decisions_amend_or_reject"]),
                                   [f"gate: {g['detail']}", f"register revision: {rev or 'none'}",
                                    f"{len(ds)} decisions; {len(reasoned)} amend/reject with a reason"])

    # pack_checks_pass
    pk = gate(system, "Pack")
    qa = [x for x in system.get("gates", []) if x["stage"] == "QA"]
    n_pass = sum(1 for x in qa if x["pass"])
    rows["pack_checks_pass"] = (2.5 * n_pass if pk["pass"] else 0,
                                [f"pack build: {pk['detail']}"] + [f"{x['check']}: {'PASS' if x['pass'] else 'FAIL'} ({x['detail']})" for x in qa])

    # planted_errors_caught
    pe, gt = system.get("planted_errors") or {}, system.get("golden_thread") or {}
    caught, planted = pe.get("caught", 0), pe.get("planted", 7) or 7
    pts = 0
    if pe.get("baseline_ready"):
        pts = math.floor(8 * caught / planted) + (2 if gt.get("share") == 1 else 0)
    rows["planted_errors_caught"] = (pts, [f"untouched pack passes: {'yes' if pe.get('baseline_ready') else 'NO'}",
                                           f"{caught} of {planted} planted errors caught",
                                           f"golden thread: {gt.get('complete', 0)} of {gt.get('total', 0)} sampled payments" + (f" ({gt['note']})" if gt.get("note") else "")])

    # teamwork
    tw = system.get("teamwork") or {}
    s = tw.get("score")
    rows["teamwork"] = ({3: 5, 2: 3}.get(s, 0),
                        ["self-reported: scored from the transcripts on your machine; the grader checks it against your trajectories and video"]
                        + ([tw.get("note", "")] if s is None else [f"{x['check']}: {'pass' if x['pass'] else 'FAIL'} ({x['detail']})" for x in tw.get("checks", [])]))

    # harness_hygiene
    hz = harness(root)
    ag = hz["agents"]
    least = all(v["tools_declared"] for v in ag.values()) and set(ag["challenger"]["tools"]) <= CHALLENGER_TOOLS and bool(ag["challenger"]["tools"])
    run_rules = {"A1", "A2", "A3", "B1", "B2"}  # the per-run rules; E2 (the skill bars) is scored in rules_extracted, not twice
    q_fail = [r["id"] for r in (quality or {}).get("results", []) if r.get("id") in run_rules and r.get("status") == "fail"]
    q_ok = bool(quality) and quality.get("runs", 0) > 0 and not q_fail
    bud = per_agent_budgets(root)
    items = [
        (least, "every agent declares tools; challenger limited to Read, Write, Glob, Grep" if least else
         "an agent has no tools list, or the challenger has tools beyond Read, Write, Glob, Grep: " + ", ".join(f"{k}={v['tools'] or 'none'}" for k, v in ag.items())),
        (hz["agent_teams_enabled"], f"agent teams {'enabled' if hz['agent_teams_enabled'] else 'NOT enabled'} in .claude/settings.json"),
        (not hz["todo_files"], "no TODO (YOU) left" if not hz["todo_files"] else "TODO (YOU) left in: " + ", ".join(hz["todo_files"])),
        (q_ok, "self-reported: quality/check.mjs run rules (A1-A3, B1, B2): " + (f"{quality.get('runs')} runs" + (f"; failing: {', '.join(q_fail)}" if q_fail else "; none failing")
                                                                 if quality else "not run (needs Node 18+ and runs/)")),
        (bud["ok"], f"self-reported: per-agent envelopes: {bud['runs']} runs" + (f"; over: {'; '.join(bud['over'][:4])}" if bud["over"] else "")
         + (f"; no run for {', '.join(bud['agents_without_a_run'])}" if bud["agents_without_a_run"] else "")),
    ]
    rows["harness_hygiene"] = (sum(1 for ok, _ in items if ok), [("ok: " if ok else "missing: ") + d for ok, d in items])
    return rows


def bars(system, sla):
    sk, b = system.get("skill") or {}, sla["sla"]
    g = system.get("gates", [])
    gt, pe = system.get("golden_thread") or {}, system.get("planted_errors") or {}
    vw = system.get("value_added") or {}
    open_ch = (vw.get("by_status") or {}).get("open", 0) + (vw.get("by_status") or {}).get("", 0)
    rows = [
        ("skill_min_found", sk.get("found"), b["skill_min_found"], ">="),
        ("skill_min_not_invented", sk.get("precision"), b["skill_min_not_invented"], ">="),
        ("skill_min_fields_right", sk.get("fields"), b["skill_min_fields_right"], ">="),
        ("skill_min_runs", len(sk.get("runs") or []), b["skill_min_runs"], ">="),
        ("min_pipeline_checks_passed_ratio", (sum(1 for x in g if x["pass"]) / len(g)) if g else None, b["min_pipeline_checks_passed_ratio"], ">="),
        ("min_golden_thread_ratio", gt.get("share"), b["min_golden_thread_ratio"], ">="),
        ("min_planted_errors_caught", pe.get("caught") if pe.get("baseline_ready") else 0, b["min_planted_errors_caught"], ">="),
        ("max_open_challenges", open_ch if vw.get("challenges") else None, b["max_open_challenges"], "<="),
    ]
    out = []
    for name, val, target, op in rows:
        ok = val is not None and (val >= target if op == ">=" else val <= target)
        out.append({"name": name, "value": val, "target": target, "op": op, "pass": ok})
    return out


# ------------------------------------------------------------------ the student's own words
def design(root=ROOT):
    p = root / "DESIGN.md"
    if not p.exists():
        return {"present": False, "note": "DESIGN.md missing: copy DESIGN.template.md and answer it in your own words"}
    text = p.read_text(encoding="utf-8")
    template = (root / "DESIGN.template.md").read_text(encoding="utf-8") if (root / "DESIGN.template.md").exists() else ""
    out, missing = {"present": True}, []
    for h in DESIGN_HEADINGS:
        m = re.search(rf"^##\s+{re.escape(h)}\s*\n(.*?)(?=^##\s|\Z)", text, re.S | re.M)
        body = (m.group(1).strip() if m else "")
        tm = re.search(rf"^##\s+{re.escape(h)}\s*\n(.*?)(?=^##\s|\Z)", template, re.S | re.M)
        if not body or (tm and body == tm.group(1).strip()):
            missing.append(h)
        out[h] = body
    out["unanswered"] = missing
    return out


def trajectories(root=ROOT):
    p = root / "trajectories.md"
    res = {"successful": None, "failing": None}
    if not p.exists():
        res["note"] = "trajectories.md missing: copy trajectories.template.md, pick two runs from `python eval/export_runs.py`, write what each taught you"
        return res
    text = p.read_text(encoding="utf-8")
    for kind in ("successful", "failing"):
        m = re.search(rf"^##\s+{kind}\s*:\s*(\S+)\s*\n(.*?)(?=^##\s|\Z)", text, re.S | re.M | re.I)
        if not m:
            continue
        rid, notes = m.group(1).strip("`"), m.group(2).strip()
        run_log = read_json(root / "runs" / f"{rid}.json") or read_json(root / "runs" / "failing" / f"{rid}.json")
        res[kind] = {"requestId": rid, "notes": notes, "found": bool(run_log),
                     "agent": (run_log or {}).get("agent"), "startedAt": (run_log or {}).get("startedAt"),
                     "wallClockSec": (run_log or {}).get("wallClockSec"), "tokens": (run_log or {}).get("tokens"),
                     "steps": [{"n": i, "tool": t["name"], "ok": t["ok"], "what": t.get("what", ""), "error": t.get("error")}
                               for i, t in enumerate((run_log or {}).get("toolCalls") or [], 1)]}
    return res


def gate_record(root=ROOT):
    review = (root / "outputs/review.md").read_text(encoding="utf-8") if (root / "outputs/review.md").exists() else ""
    sign = {}
    for k, label in (("by", "Signed off by"), ("date", "Date"), ("decision", r"Decision \(sign off / return to the team\)"), ("comment", "Comment")):
        m = re.search(rf"^{label}:[ \t]*(.*)$", review.split("## Auditor sign-off", 1)[-1], re.M)
        sign[k] = m.group(1).strip() if m else ""
    verdict = "READY FOR SIGN-OFF" if "READY FOR SIGN-OFF" in review else "BLOCKED" if "BLOCKED" in review else None
    return {"decisions": decisions(root), "review_verdict": verdict, "signoff": sign}


def design_interview(root=ROOT):
    """design-interview.md, written by /fde-ledger-eval: five questions, the student's answers recorded verbatim."""
    p = root / "design-interview.md"
    if not p.exists():
        return []
    out = []
    for m in re.finditer(r"^##\s+(Q\d+)[:.]?\s*(.*?)\n(.*?)(?=^##\s|\Z)", p.read_text(encoding="utf-8"), re.S | re.M):
        out.append({"id": m.group(1), "question": m.group(2).strip(), "answer": m.group(3).strip()})
    return out


def live_test(root=ROOT):
    """live-test.md: the student's spot-check of rules from clauses the answer key does NOT cover.
    Table rows: | rule_id | clause | verdict (correct / wrong field / not a rule / quote wrong) | note |"""
    p = root / "live-test.md"
    if not p.exists():
        return {"present": False, "rows": []}
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) >= 3 and re.fullmatch(r"CPR-\d+", c[0]) and c[0] != "CPR-00":
            rows.append({"rule_id": c[0], "clause": c[1], "verdict": c[2].lower(), "note": c[3] if len(c) > 3 else ""})
    return {"present": True, "rows": rows, "checked": len(rows), "correct": sum(1 for r in rows if r["verdict"] == "correct")}


def red_line_flags(system, integ):
    """What this run can say about each red line. The grader decides; this only reports."""
    gates = system.get("gates", [])
    g = lambda st: next((x for x in gates if x["stage"] == st), None)
    reg, pack, lang = g("Register"), g("Pack (rendered)"), g("Language")
    return [
        {"line": "numbers on /evals reproduced from /data", "status": "checked by the grader", "detail": "python eval/grade_url.py <url>"},
        {"line": "provided files unmodified", "status": "self-reported" if integ.get("ok") is not False else "FLAG",
         "detail": integ.get("detail", "") + ". The grader re-runs everything with its own copies, so edits gain nothing"},
        {"line": "builder-rendered files not edited by hand",
         "status": "FLAG" if (reg and reg.get("builder_ok") and not reg.get("same_as_fresh_build")) or (pack and not pack["pass"]) else "clear" if reg or pack else "not built",
         "detail": "; ".join(x for x in [f"register: {'equals' if reg and reg.get('same_as_fresh_build') else 'DIFFERS from'} a fresh build" if reg and reg.get("builder_ok") else "",
                                         f"pack: {pack['detail']}" if pack else ""] if x)},
        {"line": "indicators, not accusations", "status": "clear" if lang and lang["pass"] else "for a person to read" if lang else "not built",
         "detail": lang["detail"] if lang else ""},
        {"line": "no supplier name published", "status": "checked at publish", "detail": "viewer/collect.mjs fails the build on a leak"},
        {"line": "DESIGN.md, gate decisions and trajectory notes are the student's own", "status": "for the grader", "detail": ""},
    ]


def product_eval_md(r):
    """reports/PRODUCT_EVAL.md: the human-readable evaluation (the FDE product-eval shape), rendered from report.json only."""
    s, sys_ = r["score"], r["system"]
    pct = lambda x: "n/a" if not isinstance(x, (int, float)) else f"{x:.0%}" if x <= 1 else f"{x:g}"
    bars_met = sum(1 for b in r["bars"] if b["pass"])
    flags = [f for f in r["red_lines"] if f["status"] == "FLAG"]
    gaps = [x for x in r["rubric"]["automated"] if x["status"] != "pass"]
    L = [f"# Product Evaluation: Ledger", "",
         f"- **Student:** {r['student'] or '(not given)'}",
         f"- **Generated:** {r['generatedAt']}",
         f"- **Deployed URL:** {r['url'] or '(not deployed yet)'}",
         f"- **Video demo:** {r['video'] or '(not recorded yet)'}",
         f"- **Every number below came from a run.** The grader re-derives them from the deployment's /data.", "",
         "## Verdict", "",
         f"> Automated rubric **{s['automated']:g} / {s['automatedMax']}**; {s['manualMax']} manual points are scored by a person. "
         f"{bars_met} of {len(r['bars'])} declared bars met. QA: {(sys_.get('verdict') or {}).get('qa_verdict') or 'no verdict'}. "
         f"Signed off: {'yes' if r['gate']['signoff'].get('by') else 'no'}. "
         + (f"**Red-line flags: {', '.join(f['line'] for f in flags)}.**" if flags else "No red-line flags from this run."), "",
         "## 1. The declared bars (benchmark/sla.json)", "", "| Bar | This run | Target | Met |", "|---|---|---|---|"]
    L += [f"| `{b['name']}` | {pct(b['value'])} | {b['op']} {pct(b['target'])} | {'✅' if b['pass'] else '❌'} |" for b in r["bars"]]
    lt = r["live_test"]
    L += ["", "## 2. Live test: rules the answer key does not cover", ""]
    if lt["present"] and lt["rows"]:
        L += [f"{lt['correct']} of {lt['checked']} spot-checked rules correct (checked by the student against the PDF; "
              "the answer key does not score these clauses).", "", "| Rule | Clause | Verdict | Note |", "|---|---|---|---|"]
        L += [f"| {x['rule_id']} | {x['clause']} | {x['verdict']} | {x['note']} |" for x in lt["rows"]]
    else:
        L += ["Not done yet: `/fde-ledger-eval` Step 1b (live-test.md)."]
    L += ["", "## 3. Rubric scorecard", "", "| Row | Points | Awarded | Status | Evidence |", "|---|---|---|---|---|"]
    for x in r["rubric"]["automated"]:
        ev = "; ".join(e for e in x["evidence"] if e).replace("|", "/")
        L.append(f"| {x['label']} (`{x['id']}`){' *(self-reported: ' + x['selfReported'] + ')*' if x.get('selfReported') else ''} | {x['points']} | {x['awarded']:g} | {x['status']} | {ev[:300]} |")
    L += [f"| {x['label']} (`{x['id']}`) | {x['points']} | – | for the grader | {x['check'][:200]} |" for x in r["rubric"]["manual"]]
    pe, gt = sys_.get("planted_errors") or {}, sys_.get("golden_thread") or {}
    L += ["", "## 4. Pipeline, planted errors, golden thread", "", "| Stage | Check | Result | Detail |", "|---|---|---|---|"]
    L += [f"| {g['stage']} | {g['check']} | {'pass' if g['pass'] else '**FAIL**'} | {str(g['detail']).replace('|', '/')[:200]} |" for g in sys_.get("gates") or []]
    L += ["", f"Planted errors: **{pe.get('caught', 0)} of {pe.get('planted', 7)}** caught (untouched pack passes: {'yes' if pe.get('baseline_ready') else 'no'}). "
          f"Golden thread: **{gt.get('complete', 0)} of {gt.get('total', 0)}** sampled payments trace to a verified quote and an approved risk."]
    L += ["", "## 5. Integrity and red lines", "", "| Red line | Status | Detail |", "|---|---|---|"]
    L += [f"| {f['line']} | {f['status']} | {f['detail']} |" for f in r["red_lines"]]
    d = r["design"]
    L += ["", "## 6. Design and the interview", "",
          "DESIGN.md: " + ("missing" if not d.get("present") else "answered" if not d.get("unanswered") else "unanswered: " + ", ".join(d["unanswered"])) + ". "
          + (f"Design interview: {len(d.get('interview') or [])} answers recorded verbatim (on /evals)." if d.get("interview") else "Design interview: not done yet (/fde-ledger-eval Step 2b).")]
    tr = r["trajectories"]
    L += ["", "## 7. Trajectories", "",
          f"Successful: {tr['successful']['requestId'] if tr.get('successful') else 'not chosen'}. Failing: {tr['failing']['requestId'] if tr.get('failing') else 'not chosen'}. Full steps and notes on /evals."]
    L += ["", "## 8. Top fixes", ""]
    L += [f"{i}. **{x['id']}** ({x['awarded']:g}/{x['points']}): " + "; ".join(e for e in x["evidence"] if e)[:240] for i, x in enumerate(gaps[:3], 1)] or ["Nothing automated left to fix."]
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------ assemble
def assemble(root, system, quality, args_info, run_quality_note=""):
    rubric = read_json(root / "eval/rubric.json")
    sla = read_json(root / "benchmark/sla.json")
    scored = score_rows(root, system, quality, sla)
    auto = []
    for row in rubric["automated"]:
        pts, ev = scored[row["id"]]
        pts = min(row["points"], pts)
        auto.append({"id": row["id"], "label": row["label"], "points": row["points"], "awarded": pts,
                     "status": "pass" if pts == row["points"] else "partial" if pts > 0 else "fail",
                     "selfReported": {"teamwork": "all", "harness_hygiene": "items 4-5"}.get(row["id"]),
                     "rules": row["rules"], "check": row["check"], "scoring": row.get("scoring", ""), "evidence": ev})
    manual = [{"id": r["id"], "label": r["label"], "points": r["points"], "awarded": None, "status": "for the grader",
               "rules": r["rules"], "check": r["check"]} for r in rubric["manual"]]
    integ = integrity(root)
    dsg = design(root)
    dsg["interview"] = design_interview(root)
    return {
        "assignment": "LEDGER",
        "student": args_info.get("student", ""),
        "video": args_info.get("video", ""),
        "url": args_info.get("url", ""),
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "score": {"automated": sum(r["awarded"] for r in auto), "automatedMax": sum(r["points"] for r in auto),
                  "manualMax": sum(r["points"] for r in manual), "manual": None},
        "rubric": {"automated": auto, "manual": manual, "red_lines": rubric["red_lines"]},
        "bars": bars(system, sla),
        "system": {k: system.get(k) for k in ("verdict", "skill", "gates", "golden_thread", "planted_errors", "teamwork", "value_added", "cost", "objectives")},
        "judges": system.get("judges"),
        "quality": quality or {"note": run_quality_note or "not run"},
        "design": dsg,
        "live_test": live_test(root),
        "red_lines": red_line_flags(system, integ),
        "trajectories": trajectories(root),
        "gate": gate_record(root),
        "integrity": integ,
        "harness": harness(root),
    }


def run_quality(root=ROOT):
    node = shutil.which("node")
    if not node:
        return None, "node not found: install Node 18+ to run quality/check.mjs"
    run([node, "quality/check.mjs", "."], root)
    return read_json(root / "reports/quality.json"), ""


def write_eval_json(root, system):
    """reports/eval.json: the metrics quality/check.mjs rule E2 compares with expectations.json `eval`."""
    sk, g = system.get("skill") or {}, system.get("gates", [])
    gt, pe = system.get("golden_thread") or {}, system.get("planted_errors") or {}
    m = {"found": sk.get("found"), "notInvented": sk.get("precision"), "fieldsRight": sk.get("fields"),
         "goldenThread": gt.get("share"), "plantedCaught": (pe.get("caught", 0) / pe["planted"]) if pe.get("planted") and pe.get("baseline_ready") else 0,
         "checksPassed": (sum(1 for x in g if x["pass"]) / len(g)) if g else 0}
    (root / "reports").mkdir(exist_ok=True)
    (root / "reports/eval.json").write_text(json.dumps({k: v for k, v in m.items() if v is not None}, indent=2) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--student")
    ap.add_argument("--video")
    ap.add_argument("--url")
    ap.add_argument("--no-run", action="store_true", help="score the existing reports/system.json")
    ap.add_argument("--write-integrity", action="store_true", help=argparse.SUPPRESS)  # staff: refresh eval/integrity.json
    a = ap.parse_args()
    if a.write_integrity:
        (ROOT / "eval/integrity.json").write_text(json.dumps({"$comment": "sha256 of every provided file (text with \\n line endings). Checked by eval/build_report.py; changing a provided file is a red line.",
                                                               "files": provided_files()}, indent=1) + "\n", encoding="utf-8")
        print("written: eval/integrity.json")
        return 0

    saved = read_json(ROOT / "reports/submission.json", {}) or {}
    info = {k: getattr(a, k) or saved.get(k, "") for k in ("student", "video", "url")}
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports/submission.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")

    if not a.no_run:
        print("1/3 exporting agent runs ...", flush=True)
        run([sys.executable, "eval/export_runs.py"])
        print("2/3 running the whole-system eval (a few minutes) ...", flush=True)
        code, text = run([sys.executable, "eval/run_all.py"])
        if code != 0:
            print(text[-2000:])
            return 1
    system = read_json(ROOT / "reports/system.json")
    if not system:
        sys.exit("STOP: reports/system.json missing; run without --no-run")
    write_eval_json(ROOT, system)
    print("3/3 running the quality kit ...", flush=True)
    quality, note = run_quality(ROOT)
    report = assemble(ROOT, system, quality, info, note)
    (ROOT / "reports/report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    (ROOT / "reports/PRODUCT_EVAL.md").write_text(product_eval_md(report), encoding="utf-8")

    s = report["score"]
    print(f"\nLEDGER evaluation for {info['student'] or '(no name: pass --student)'}")
    print(f"Automated: {s['automated']:g} / {s['automatedMax']}   (manual rows, {s['manualMax']} pts, are scored by a person)\n")
    print("| Row | Points | Awarded | Status |\n|---|---|---|---|")
    for r in report["rubric"]["automated"]:
        print(f"| {r['id']} | {r['points']} | {r['awarded']:g} | {r['status']} |")
    first_gap = next((r for r in report["rubric"]["automated"] if r["status"] != "pass"), None)
    if first_gap:
        print(f"\nFirst thing to fix: {first_gap['id']}: " + "; ".join(e for e in first_gap["evidence"] if e)[:400])
    todo = []
    if not info["video"]: todo.append("video URL (--video)")
    if report["design"].get("unanswered") or not report["design"].get("present"): todo.append("DESIGN.md")
    if not (report["trajectories"]["successful"] and report["trajectories"]["failing"]): todo.append("trajectories.md (two runs)")
    if not report["gate"]["signoff"].get("by"): todo.append("the sign-off block in outputs/review.md (TODO #13)")
    if not report["live_test"]["rows"]: todo.append("live-test.md (spot-check five rules the key does not cover)")
    if not report["design"].get("interview"): todo.append("the design interview (/fde-ledger-eval)")
    if report["integrity"].get("ok") is False: todo.append("RED LINE: provided files changed: " + ", ".join(report["integrity"]["changed"][:5]))
    if todo:
        print("\nStill missing for submission: " + "; ".join(todo))
    print("\nwritten: reports/report.json and reports/PRODUCT_EVAL.md  (viewer/collect.mjs publishes both under /evals/)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
