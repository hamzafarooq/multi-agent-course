#!/usr/bin/env python3
"""The whole-system evaluation: one report for the run in the project.

Usage: python eval/run_all.py

It does not rerun the skill or the AI judges. It reads their latest results:
  eval/skill/runs/*/rules.json        (scored here against the answer key)
  eval/subagents/judgements/*.json    (from eval/subagents/run_eval.py; advisory)
  eval/team/judgements/*.json         (from eval/team/run_eval.py; advisory)
and runs everything else itself, read-only: the contract schemas, every pipeline
gate, the golden thread, teamwork and the planted errors (from the run
transcripts and a copy of the pack), and the cost of each stage.

Writes reports/system.md (by component; --layout=objective for the other layout)
and reports/system.json, which eval/build_report.py reads. Nothing in outputs/ or data/ is changed.
Safe on an unfinished project: every missing output is reported as "not built yet" with its TODO.
"""
import os as _os, subprocess as _sp, sys as _sys
if __name__ == "__main__" and _os.name == "nt" and not _sys.flags.utf8_mode:  # Windows: rerun in UTF-8 mode
    _sys.exit(_sp.call([_sys.executable, "-X", "utf8", *_sys.argv]))  # (£, →, curly quotes in the data)
import csv, glob, importlib.util, itertools, json, os, re, shutil, subprocess, sys, tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "eval"
OUT = ROOT / "outputs"
PY = sys.executable
NAMES = {1: "Critical Failure", 2: "Requires Tuning", 3: "Production Ready"}
SUBAGENTS = ["spend-analyst", "findings-analyst", "risk-assessor"]
TEAMMATES = ["planner", "challenger", "qa-reviewer"]
OBJECTIVES = [
    "Extract every testable rule, with clause references and verbatim quotes",
    "Analyse the full spend population against the rules, by code",
    "Summarise past audit coverage and the council's risk scale",
    "Rate risks on a fixed scale, every rating citing evidence",
    "Produce an audit program and planning memo for the approved risks",
    "Cross-check the whole pack before the auditor signs off",
]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


skill = load("score_skill", EVALS / "skill/score_skill.py")
sub = load("subagent_eval", EVALS / "subagents/run_eval.py")
quotes = load("verify_quotes", ROOT / ".claude/skills/extract-rules/verify_quotes.py")
samples_check = load("check_samples", ROOT / "scripts/checks/check_samples.py")


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    return p.returncode, (p.stdout + p.stderr).strip()


def pct(x):
    return "n/a" if x is None else f"{x:.0%}"


# ---------------------------------------------------------------- the skill
def skill_results():
    paths = sorted(glob.glob(str(EVALS / "skill/runs/*/rules.json")))
    if not paths:
        return None
    key, blank = skill.load_key(EVALS / "skill/answer-key.csv")
    if blank:
        return None
    runs = []
    for p in paths:
        doc = json.loads(Path(p).read_text())
        s = skill.score_run(doc, key)
        s["quotes_ok"], _ = skill.quotes_ok(p, ROOT / "data/contract-rules.pdf")
        s["name"] = Path(p).parent.name
        s["sig"] = skill.signature(doc)
        runs.append(s)
    cons = None
    if len(runs) > 1:
        pairs = list(itertools.combinations(runs, 2))
        cons = sum(len(a["sig"] & b["sig"]) / len(a["sig"] | b["sig"]) for a, b in pairs) / len(pairs)
    bar = skill.BAR
    worst = lambda k: min((r[k] for r in runs if r[k] is not None), default=None)
    found, prec, fields = worst("found"), worst("precision"), worst("fields")
    q = all(r["quotes_ok"] for r in runs)
    if not q or (prec is not None and prec < bar["precision"]):
        score = 1
    elif (found or 0) >= bar["found"] and (fields or 0) >= bar["fields"]:
        score = 3
    else:
        score = 2
    return {"runs": runs, "consistency": cons, "found": found, "precision": prec, "fields": fields, "quotes": q, "score": score, "bar": bar}


# ---------------------------------------------------------------- judged components
def judgement(folder, agent):
    p = EVALS / folder / "judgements" / f"{agent}.json"
    if not p.exists():
        return None
    r = json.loads(p.read_text())
    r["overall"] = sub.overall(r)
    r["below"] = [f"{s['dimension']} {s['score']}" for s in r.get("scores", []) if isinstance(s.get("score"), int) and s["score"] < 3]
    return r


# ---------------------------------------------------------------- pipeline gates
NEEDS = {  # what each stage reads, and the TODO that produces it: a missing file is reported, never a crash
    "Rules": (["rules.json"], "#1 extract-rules"),
    "Analytics": (["analytics.json", "analytics-full/selfcheck.json"], "#2 spend-analyst"),
    "History": (["history.json"], "#3 findings-analyst"),
    "Register": (["risk-ratings.json", "risk-register.md", "auditor-comments.md"], "#4-#5 risk-assessor"),
    "Approval gate": (["risk-register.md", "auditor-comments.md"], "#6 the auditor's decisions"),
    "Pack": (["audit-plan.json"], "#8-#9 the planner"),
}


def missing(stage):
    files, todo = NEEDS[stage]
    gone = [f for f in files if not (OUT / f).exists()]
    return f"not built yet: outputs/{', outputs/'.join(gone)} missing (TODO {todo})" if gone else None


def contract_gate(add):
    """Every JSON output validates against its schema in contract/. Missing files are skipped here (the stage reports them)."""
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        add("Contract", "Outputs match contract/*.schema.json", False, "jsonschema not installed: pip install -r requirements.txt")
        return
    for name in ("rules", "analytics", "history", "risk-ratings", "audit-plan"):
        p = OUT / f"{name}.json"
        if not p.exists():
            continue
        schema = json.loads((ROOT / f"contract/{name}.schema.json").read_text(encoding="utf-8"))
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            add("Contract", f"{name}.json matches its schema", False, f"not valid JSON: {e}")
            continue
        errs = sorted(Draft202012Validator(schema).iter_errors(doc), key=lambda e: list(e.path))
        detail = "valid" if not errs else f"{len(errs)} error(s); first: {'/'.join(map(str, errs[0].path)) or '(root)'}: {errs[0].message[:120]}"
        add("Contract", f"{name}.json matches its schema", not errs, detail)


def gates():
    g = []

    def add(stage, check, ok, detail, **extra):
        g.append({"stage": stage, "check": check, "pass": bool(ok), "detail": detail, **extra})

    contract_gate(add)

    if missing("Rules"):
        add("Rules", "Every quote is in the PDF on its page", False, missing("Rules"))
    else:
        code, text = run([PY, ".claude/skills/extract-rules/verify_quotes.py", "outputs/rules.json", "data/contract-rules.pdf"])
        add("Rules", "Every quote is in the PDF on its page", code == 0, (text.splitlines() or [""])[-1])

    sc = OUT / "analytics-full/selfcheck.json"
    try:
        items = json.loads(sc.read_text()) if sc.exists() else []
        items = items if isinstance(items, list) else []
    except json.JSONDecodeError:
        items = []
    ok = [i for i in items if isinstance(i, dict) and i.get("pass")]
    tests_run = {}
    if (OUT / "analytics.json").exists():
        try:
            tests_run = {k for k, v in json.loads((OUT / "analytics.json").read_text()).get("tests", {}).items() if not (isinstance(v, dict) and v.get("skipped"))}
        except json.JSONDecodeError:
            pass
    covered = {i.get("test") for i in ok}
    uncovered = sorted(t for t in tests_run if t not in covered)
    add("Analytics", "One item per test re-derived from the cleaned data",
        bool(items) and len(ok) == len(items) and not uncovered,
        missing("Analytics") or f"{len(ok)} of {len(items)} self-check items match" + (f"; tests with no self-check item: {', '.join(uncovered)}" if uncovered else ""))

    if missing("History"):
        add("History", "Every quote is on its page of its paper", False, missing("History"))
    else:
        code, text = run([PY, "scripts/verify_history.py", "outputs/history.json", "data/committee"])
        add("History", "Every quote is on its page of its paper", code == 0, " ".join(text.splitlines()[-3:]).strip())

    if missing("Register") or not all((OUT / f).exists() for f in ("rules.json", "analytics.json", "history.json")):
        add("Register", "Every rating traces to evidence; the register matches a fresh build", False,
            missing("Register") or "not built yet: the register needs rules.json, analytics.json and history.json first")
        add("Approval gate", "Every risk has the auditor's decision, applied in a revision", False, missing("Approval gate") or "register not built")
        add("Pack", "Only approved risks planned; samples drawn and verified; every rule accounted for", False, missing("Pack") or "register not built")
        return qa_gates(g, add)

    with tempfile.TemporaryDirectory() as tmp:
        shutil.copy(OUT / "auditor-comments.md", Path(tmp) / "comments.md")
        code, text = run([PY, ".claude/skills/risk-assessment/build_register.py", "outputs/risk-ratings.json",
                          "--out", f"{tmp}/register.md", "--comments", f"{tmp}/comments.md"])
        line = next((l for l in text.splitlines() if l.startswith("risks kept")), "")
        same = (Path(tmp) / "register.md").exists() and (Path(tmp) / "register.md").read_text() == (OUT / "risk-register.md").read_text()
        if code != 0:
            line = (line + "; " if line else "") + "; ".join(l for l in text.splitlines() if l.startswith("FAIL"))[:300]
        add("Register", "Every rating traces to evidence; the register matches a fresh build", code == 0 and same,
            line + ("" if same else "; register differs from a fresh build"), builder_ok=code == 0, same_as_fresh_build=same)

    code, text = run([PY, ".claude/skills/audit-program/build_pack.py", "--gate"])
    add("Approval gate", "Every risk has the auditor's decision, applied in a revision", code == 0, (text.splitlines() or [""])[0])

    if missing("Pack"):
        add("Pack", "Only approved risks planned; samples drawn and verified; every rule accounted for", False, missing("Pack"))
    else:
        with tempfile.TemporaryDirectory() as tmp:
            code, text = run([PY, ".claude/skills/audit-program/build_pack.py", "--out-dir", tmp])
            line = next((l for l in text.splitlines() if l.startswith("scope:")), "")
            if code != 0:
                line = (line + "; " if line else "") + "; ".join(l for l in text.splitlines() if l.startswith("FAIL"))[:300]
            add("Pack", "Only approved risks planned; samples drawn and verified; every rule accounted for", code == 0, line)
            # the rendered pack must be exactly what the builder renders: nobody edits it by hand (red line).
            # Skipped by the grader: on pseudonymised supplier names a recipe that filters supplier_norm by pattern redraws differently.
            if code == 0 and not os.environ.get("LEDGER_GRADER"):
                docs = ["planning-memo.md", "risk-control-matrix.md", "audit-program.md"]
                differ = [d for d in docs if not (OUT / d).exists() or (Path(tmp) / d).read_text(encoding="utf-8") != (OUT / d).read_text(encoding="utf-8")]
                add("Pack (rendered)", "The pack documents equal a fresh build from audit-plan.json (never edited by hand)", not differ,
                    "identical to a fresh build" if not differ else f"differs from a fresh build: {', '.join(differ)}")
    language_gate(add)
    return qa_gates(g, add)


ACCUSATION = re.compile(r"\b(fraud\w*|corrupt\w*|misconduct|theft|thie[fv]\w*|stole|steal\w*|collu\w*|kickback\w*|brib\w*|embezzl\w*|"
                        r"deliberately|dishonest\w*|illegal\w*|unlawful\w*|criminal\w*)\b", re.I)


def language_gate(add):
    """Indicators, not accusations (red line). Scans the text the MODELS wrote (not the builders' disclaimers) for accusatory
    words. A hit is not proof of an accusation ("anti-fraud plan" can be a fair citation); it is a line a person must read."""
    texts = []
    for name, fields in (("risk-ratings.json", None), ("audit-plan.json", None)):
        p = OUT / name
        if p.exists():
            try:
                doc = json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            stack = [(name, doc)]
            while stack:
                where, o = stack.pop()
                if isinstance(o, dict):
                    stack += [(f"{where}.{k}", v) for k, v in o.items() if k not in ("cite", "cites", "sample", "sample_source")]
                elif isinstance(o, list):
                    stack += [(f"{where}[{i}]", v) for i, v in enumerate(o)]
                elif isinstance(o, str):
                    texts.append((where, o))
    for name in ("challenges.md", "review.md"):
        p = OUT / name
        if p.exists():
            texts += [(f"{name}:{i}", l) for i, l in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)]
    if not texts:
        return
    hits = [f"{w}: “{m.group(0)}”" for w, t in texts for m in [ACCUSATION.search(t)] if m]
    add("Language", "Indicators, not accusations: no accusatory wording in what the models wrote", not hits,
        "no accusatory wording found" if not hits else f"{len(hits)} line(s) for a person to read: " + "; ".join(hits[:5]))


def hardcoded_thresholds():
    """Evidence only (no gate, no points): threshold figures from rules.json typed as literals in the spend-analyst's scripts.
    SPEC §7.2 says thresholds come only from rules.json. The grader cannot see scripts/, so this never scores."""
    rules = OUT / "rules.json"
    scripts = [p for p in (ROOT / "scripts").glob("*.py") if p.name not in ("status.py", "pdftext.py", "verify_history.py")]
    if not rules.exists() or not scripts:
        return None
    try:
        vals = {v for r in json.loads(rules.read_text(encoding="utf-8")).get("rules", [])
                for v in (r.get("threshold_low"), r.get("threshold_high")) if isinstance(v, int) and v >= 1000}
    except json.JSONDecodeError:
        return None
    found = []
    for p in scripts:
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            code = line.split("#", 1)[0]
            for v in vals:
                if re.search(rf"(?<![\w.]){v}(?:\.0+)?(?![\w.])|(?<![\w.]){v // 1000}_?000(?![\w.])", code.replace(",", "")):
                    found.append(f"scripts/{p.name}:{i}: {v}")
    return sorted(set(found))


def qa_gates(g, add):
    """The four QA checks (run_checks.py) and the auditor's sign-off in review.md."""
    if not (OUT / "audit-plan.json").exists():
        for c in ("quotes", "numbers", "trace", "samples"):
            add("QA", f"QA check: {c}", False, "not built yet: no pack to check (TODOs #7-#12)")
        return g, "VERDICT: BLOCKED (no pack)", False
    code, text = run([PY, "scripts/checks/run_checks.py"])
    for l in text.splitlines():
        m = re.match(r"\| (quotes|numbers|trace|samples) \| (PASS|FAIL) \| (.*) \|", l)
        if m:
            detail = m.group(3).split(": ", 1)[-1]
            if detail == "(no summary)":  # the check crashed; say why (often a TODO still raising NotImplementedError)
                detail = next((x.strip() for x in text.splitlines() if "Error" in x), detail)[:200]
            add("QA", f"QA check: {m.group(1)}", m.group(2) == "PASS", detail)
    verdict = next((l for l in text.splitlines() if l.startswith("VERDICT")), "")

    for c in ("quotes", "numbers", "trace", "samples"):  # a check that crashed (e.g. TODO #12 not done) prints no table row
        if not any(x["check"] == f"QA check: {c}" for x in g):
            err = next((l.strip() for l in text.splitlines() if "NotImplementedError" in l or "Error" in l), "the check printed no result")
            add("QA", f"QA check: {c}", False, err[:200])
    review = (OUT / "review.md").read_text() if (OUT / "review.md").exists() else ""
    m = re.search(r"^Signed off by:[ \t]*(\S.*)?$", review, re.M)
    signed = bool(m and m.group(1))
    return g, verdict, signed


# ---------------------------------------------------------------- golden thread
def golden_thread():
    """Trace every sampled payment back: payment -> workbook row -> test -> control -> rule -> quote in the PDF -> approved risk."""
    links = ["payment in the cleaned data", "payment at its workbook row", "test in the plan", "control defined for the test",
             "control cites a rule", "rule's quote found in the PDF", "risk approved by the auditor"]
    need = ["analytics-full/spend-clean.csv", "audit-plan.json", "rules.json", "auditor-comments.md", "risk-register.md"]
    gone = [f for f in need if not (OUT / f).exists()]
    if gone or not list((OUT / "samples").glob("T-*.csv")):
        return {"total": 0, "complete": 0, "share": None, "links": links, "broken": {l: 0 for l in links}, "score": None,
                "tests": 0, "rules_used": 0, "note": "not built yet: " + (", ".join(gone) if gone else "no samples drawn") + " (the pack, TODOs #8-#9)"}
    spend = {r["row_id"]: r for r in csv.DictReader(open(OUT / "analytics-full/spend-clean.csv", newline="", encoding="utf-8"))}
    plan = json.loads((OUT / "audit-plan.json").read_text())
    rules = {r["rule_id"]: r for r in json.loads((OUT / "rules.json").read_text())["rules"]}
    pages = [quotes.normalise(p) for p in quotes.pdf_pages(ROOT / "data/contract-rules.pdf")]
    quote_ok = {}

    def rule_verified(rid):
        if rid not in quote_ok:
            r = rules.get(rid)
            ok = False
            if r:
                q, pg = quotes.normalise(r["verbatim_quote"]), r.get("page")
                ok = isinstance(pg, int) and 1 <= pg <= len(pages) and q in pages[pg - 1]
            quote_ok[rid] = ok
        return quote_ok[rid]

    comments = (OUT / "auditor-comments.md").read_text(encoding="utf-8")
    approved = set()
    for line in comments.splitlines():
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) >= 5 and re.fullmatch(r"R-\d+", c[0]) and c[4].lower() in ("approve", "amend"):
            approved.add(c[0])
    register = (OUT / "risk-register.md").read_text(encoding="utf-8")
    in_register = set(re.findall(r"^\| (R-\d+) \|", register.split("## Summary", 1)[-1].split("\n## ", 1)[0], re.M))

    tests = {}
    for risk in plan.get("risks", []):
        controls = {c["id"]: c for c in risk.get("controls") or []}
        for t in risk.get("tests") or []:
            tests[t["id"]] = (risk["id"], controls.get(t.get("control")))

    links = ["payment in the cleaned data", "payment at its workbook row", "test in the plan", "control defined for the test",
             "control cites a rule", "rule's quote found in the PDF", "risk approved by the auditor"]
    broken = {l: 0 for l in links}
    total = complete = 0
    cache = {}
    money = samples_check.money
    for f in sorted((OUT / "samples").glob("T-*.csv")):
        for s in csv.DictReader(open(f, newline="", encoding="utf-8")):
            total += 1
            ok = []
            row = spend.get(s["row_id"])
            ok.append(bool(row) and row["Supplier name"].strip() == s["supplier"].strip() and money(row["Net amount"]) == money(s["amount"]))
            src, _, n = s["row_id"].rpartition(":")
            wb = samples_check.load_workbook_rows(src, cache) or {}
            w = wb.get(int(n)) if n.isdigit() else None
            ok.append(bool(w) and w.get("Supplier name", "").strip() == s["supplier"].strip() and money(w.get("Net amount")) == money(s["amount"]))
            risk_id, control = tests.get(s["test"], (None, None))
            ok.append(s["test"] in tests)
            ok.append(control is not None)
            cited = [c.split(":", 1)[1] for c in (control or {}).get("cites", []) if c.startswith("rule:")]
            ok.append(any(c in rules for c in cited))
            ok.append(any(rule_verified(c) for c in cited))
            ok.append(risk_id in approved and risk_id in in_register)
            for l, v in zip(links, ok):
                if not v:
                    broken[l] += 1
            complete += all(ok)
    share = complete / total if total else None
    score = None if share is None else 3 if share == 1 else 2 if share >= 0.95 else 1
    return {"total": total, "complete": complete, "share": share, "links": links, "broken": broken, "score": score,
            "tests": len({t for t in tests}), "rules_used": len(quote_ok)}


# ---------------------------------------------------------------- cost
def cost():
    rows = []
    for agent in SUBAGENTS + TEAMMATES:
        for path, meta in sub.find_runs(agent):
            t0 = t1 = None
            peak = out = calls = errors = 0
            for line in open(path, encoding="utf-8", errors="replace"):
                try:
                    o = json.loads(line)
                except Exception:
                    continue
                ts = o.get("timestamp")
                if ts:
                    t0 = t0 or ts
                    t1 = ts
                m = o.get("message") or {}
                c = m.get("content")
                if o.get("type") == "assistant":
                    u = m.get("usage") or {}
                    peak = max(peak, u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0))
                    out += u.get("output_tokens", 0)
                    calls += sum(1 for b in c or [] if isinstance(b, dict) and b.get("type") == "tool_use")
                elif o.get("type") == "user" and isinstance(c, list):
                    errors += sum(1 for b in c if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("is_error"))
            try:
                secs = (datetime.fromisoformat(t1.replace("Z", "+00:00")) - datetime.fromisoformat(t0.replace("Z", "+00:00"))).total_seconds()
            except Exception:
                secs = None
            rows.append({"agent": meta.get("agentType", agent), "start": t0 or "", "minutes": None if secs is None else secs / 60,
                         "peak": peak, "calls": calls, "errors": errors})
    return sorted(rows, key=lambda r: r["start"])


# ---------------------------------------------------------------- scoring the objectives
def worst(*scores):
    """The lowest of the scores that exist; None when there are none."""
    s = [x for x in scores if isinstance(x, int)]
    return min(s) if s else None


def main():
    sk = skill_results()
    subs = {a: judgement("subagents", a) for a in SUBAGENTS}
    # teamwork, value added and planted errors are scripts: always computed fresh (the judges are optional)
    team_mod = load("team_eval", EVALS / "team/run_eval.py")
    team = {"teamwork": team_mod.teamwork(), "value_added": team_mod.value_added(), "planted_errors": team_mod.planted_errors()}
    mates = {a: judgement("team", a) for a in TEAMMATES}
    g, verdict, signed = gates()
    gt = golden_thread()
    cs = cost()
    gate = lambda stage: all(x["pass"] for x in g if x["stage"] == stage)
    g3 = lambda ok: 3 if ok else 1
    ov = lambda r: r["overall"] if r else None
    tw = team["teamwork"]["score"] if team else None
    pe = team["planted_errors"] if team else None
    pe_score = None if not pe else 3 if pe["caught"] == pe["planted"] and pe["baseline_ready"] else 1

    def why(parts):
        return "; ".join(p for p in parts if p) or "nothing: every check passed"

    below = lambda name, r: f"{name}: {', '.join(r['below'])}" if r and r["below"] else ""
    objs = [
        (worst(sk["score"] if sk else None, g3(gate("Rules"))),
         why([f"found {pct(sk['found'])} in the weakest run, below the {pct(sk['bar']['found'])} bar" if sk and (sk["found"] or 0) < sk["bar"]["found"] else "",
              "" if gate("Rules") else "a quote is not in the PDF", "" if sk else "the skill has not been scored"])),
        (worst(ov(subs["spend-analyst"]), g3(gate("Analytics"))), why([below("spend-analyst", subs["spend-analyst"]), "" if gate("Analytics") else "the self-check fails"])),
        (worst(ov(subs["findings-analyst"]), g3(gate("History"))), why([below("findings-analyst", subs["findings-analyst"]), "" if gate("History") else "a quote is not in its paper"])),
        (worst(ov(subs["risk-assessor"]), g3(gate("Register")), g3(gate("Approval gate"))),
         why([below("risk-assessor", subs["risk-assessor"]), "" if gate("Register") else "the register fails its build", "" if gate("Approval gate") else "the approval gate is not closed"])),
        (worst(ov(mates["planner"]), g3(gate("Pack"))), why([below("planner", mates["planner"]), "" if gate("Pack") else "the pack fails its build"])),
        (worst(ov(mates["challenger"]), ov(mates["qa-reviewer"]), tw, g3(gate("QA")), pe_score, gt["score"]),
         why([below("challenger", mates["challenger"]), below("qa-reviewer", mates["qa-reviewer"]),
              f"teamwork {tw}: " + ", ".join(c["check"].lower() for c in team["teamwork"]["checks"] if not c["pass"]) if team and tw and tw < 3 else "",
              "" if gate("QA") else "a QA check fails",
              f"{pe['planted'] - pe['caught']} planted error(s) missed" if pe and pe["caught"] < pe["planted"] else "",
              f"golden thread {pct(gt['share'])}" if gt["score"] and gt["score"] < 3 else ""])),
    ]
    # an objective whose judged component has not been scored yet is not scored either
    needs = [[sk], [subs["spend-analyst"]], [subs["findings-analyst"]], [subs["risk-assessor"]], [mates["planner"]],
             [mates["challenger"], mates["qa-reviewer"], team]]
    objs = [(s, w) if all(n) else (None, "a component has not been scored yet; run its evaluation first") for (s, w), n in zip(objs, needs)]
    overall = None if any(o[0] is None for o in objs) else worst(*[o[0] for o in objs])
    scored = lambda s: "not scored" if s is None else f"{s} {NAMES[s]}"
    n_pass = sum(1 for x in g if x["pass"])

    # ---- blocks shared by both layouts
    head = ["# Whole-system evaluation", "",
            f"Scored {datetime.now().strftime('%Y-%m-%d')} on the run in the project. 1 = Critical Failure, 2 = Requires Tuning, 3 = Production Ready. "
            "A score is the lowest of what it is made from.", "",
            f"**Verdict: {scored(overall)}.** {n_pass} of {len(g)} pipeline checks pass, "
            f"{gt['complete']:,} of {gt['total']:,} sampled payments trace back to a verified rule, "
            + (f"{pe['caught']} of {pe['planted']} planted errors were caught, " if pe else "")
            + f"and the pack is {'signed off' if signed else 'not yet signed off by the auditor'}.", ""]

    obj_table = ["| # | Objective | Score | What holds it back |", "|---|---|---|---|"]
    obj_table += [f"| {i} | {o} | **{scored(s)}** | {w} |" for i, (o, (s, w)) in enumerate(zip(OBJECTIVES, objs), 1)]

    comp = ["| Component | Kind | Score | Below 3 on |", "|---|---|---|---|"]
    comp.append(f"| extract-rules | skill | **{scored(sk['score'] if sk else None)}** | " + (f"found {pct(sk['found'])} (bar {pct(sk['bar']['found'])})" if sk and sk["score"] < 3 else "") + " |")
    for a in SUBAGENTS:
        comp.append(f"| {a} | sub-agent | **{scored(ov(subs[a]))}** | {', '.join(subs[a]['below']) if subs[a] else 'run eval/subagents/run_eval.py'} |")
    for a in TEAMMATES:
        comp.append(f"| {a} | teammate | **{scored(ov(mates[a]))}** | {', '.join(mates[a]['below']) if mates[a] else 'run eval/team/run_eval.py'} |")
    comp.append(f"| teamwork | the team | **{scored(tw)}** | " + (", ".join(c["check"].lower() for c in team["teamwork"]["checks"] if not c["pass"]) if team else "run eval/team/run_eval.py") + " |")

    skill_block = []
    if sk:
        skill_block = ["| Run | Found | Not invented | Fields right | Quotes verified |", "|---|---|---|---|---|"]
        skill_block += [f"| {r['name']} | {pct(r['found'])} | {pct(r['precision'])} | {pct(r['fields'])} | {'yes' if r['quotes_ok'] else 'NO'} |" for r in sk["runs"]]
        skill_block += ["", f"Rule sets agree {pct(sk['consistency'])} across runs on average." if sk["consistency"] is not None else ""]

    def gate_table(stages=None):
        rows = [x for x in g if stages is None or x["stage"] in stages]
        return ["| Stage | Check | Result | Detail |", "|---|---|---|---|"] + [
            f"| {x['stage']} | {x['check']} | {'pass' if x['pass'] else '**FAIL**'} | {str(x['detail']).replace('|', '/')} |" for x in rows]

    thread = [f"**{gt['complete']:,} of {gt['total']:,} sampled payments ({pct(gt['share'])}) have a complete chain**, across {gt['tests']} tests and {gt['rules_used']} rules.", "",
              "| Link | Payments where it breaks |", "|---|---|"] + [f"| {l} | {gt['broken'][l]} |" for l in gt["links"]]

    def score_table(results, heading):
        return sub.render([r for r in results if r], heading)[: 2 + len([r for r in results if r])]

    planted = []
    if pe:
        planted = [f"**{pe['caught']} of {pe['planted']} planted errors caught.**", "", "| Planted | Caught |", "|---|---|"]
        planted += [f"| {t['plant']} | {'yes' if t['caught'] else '**NO**'} |" for t in pe["trials"][1:]]
    teamwork_block, value_block = [], []
    if team:
        teamwork_block = ["| Check | Kind | Result | Detail |", "|---|---|---|---|"] + [
            f"| {c['check']} | {c['kind']} | {'pass' if c['pass'] else '**FAIL**'} | {str(c['detail']).replace('|', '/')} |" for c in team["teamwork"]["checks"]]
        va = team["value_added"]
        if va.get("first"):
            value_block = [f"| Measure | Version {va['first_version']} | Version {va['last_version']} |", "|---|---|---|"]
            value_block += [f"| {k.capitalize()} | {va['first'][k]} | {va['last'][k]} |" for k in ("controls", "tests", "sampled transactions", "rules cited")]
            value_block += ["", f"{va['challenges']} challenges: " + ", ".join(f"{v} {k}" for k, v in va["by_status"].items()) + "."]

    cost_block = ["| Agent | Minutes | Peak context (tokens) | Tool calls | Calls that errored |", "|---|---|---|---|---|"]
    cost_block += [f"| {r['agent']} | {r['minutes']:.0f} | {r['peak']:,} | {r['calls']} | {r['errors']} |" for r in cs if r["minutes"] is not None]
    total_min = sum(r["minutes"] for r in cs if r["minutes"] is not None)
    cost_block += ["", f"Total agent time: {total_min:.0f} minutes across {len(cs)} runs. The skill's runs and the lead session are not included."]

    pointers = ["", "## Where the detail is", "",
                "- Skill: `eval/skill/report.md`", "- Sub-agents: `eval/subagents/report.md`", "- Agent team: `eval/team/report.md`"]

    # ---- layout A: by objective
    a = head + ["## Scorecard: the system against its six objectives", ""] + obj_table
    ev = [
        ("extract-rules skill", skill_block + [""] + gate_table(["Rules"])),
        ("spend-analyst", score_table([subs["spend-analyst"]], "Sub-agent") + [""] + gate_table(["Analytics"])),
        ("findings-analyst", score_table([subs["findings-analyst"]], "Sub-agent") + [""] + gate_table(["History"])),
        ("risk-assessor", score_table([subs["risk-assessor"]], "Sub-agent") + [""] + gate_table(["Register", "Approval gate"])),
        ("planner", score_table([mates["planner"]], "Teammate") + [""] + gate_table(["Pack"])),
        ("challenger, qa-reviewer and the checks", score_table([mates["challenger"], mates["qa-reviewer"]], "Teammate") + ["", "**Teamwork**", ""] + teamwork_block
         + ["", "**QA checks**", ""] + gate_table(["QA"]) + ["", "**Planted errors**", ""] + planted + ["", "**Golden thread**", ""] + thread
         + ["", "**What the challenge rounds changed**", ""] + value_block),
    ]
    for i, ((s, w), (who, block)) in enumerate(zip(objs, ev), 1):
        a += ["", f"## Objective {i}: {OBJECTIVES[i - 1]}", "", f"Score: **{scored(s)}**. Done by: {who}.", ""] + block
    a += ["", "## Cost", ""] + cost_block + pointers

    # ---- layout B: by component
    b = head + ["## Components", ""] + comp
    b += ["", "## Skill: extract-rules", ""] + skill_block
    b += ["", "## Sub-agents", ""] + score_table([subs[x] for x in SUBAGENTS], "Sub-agent")
    b += ["", "## Agent team", ""] + score_table([mates[x] for x in TEAMMATES], "Teammate")
    b += ["", "### Teamwork", ""] + teamwork_block + ["", "### What the challenge rounds changed", ""] + value_block
    b += ["", "## Pipeline checks", ""] + gate_table() + ["", verdict]
    b += ["", "### Golden thread", ""] + thread + ["", "### Planted errors", ""] + planted
    b += ["", "## Objectives", ""] + obj_table
    b += ["", "## Cost", ""] + cost_block + pointers

    layout = "objective" if "--layout=objective" in sys.argv else "component"
    out = ROOT / "reports"
    out.mkdir(parents=True, exist_ok=True)
    (out / "system.md").write_text("\n".join(a if layout == "objective" else b) + "\n", encoding="utf-8")
    slim_skill = None
    if sk:
        slim_skill = {k: sk[k] for k in ("consistency", "found", "precision", "fields", "quotes", "score", "bar")}
        slim_skill["runs"] = [{k: r[k] for k in ("name", "found", "precision", "fields", "quotes_ok", "tp", "fn", "fp")}
                              | {"missed": [f"{x['id']} ({x['clause']})" for x in r["rows"] if x["want"] and not x["got"]],
                                 "invented": [f"{x['id']} ({x['clause']})" for x in r["rows"] if not x["want"] and x["got"]]}
                              for r in sk["runs"]]
    system = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "verdict": {"overall": overall, "name": NAMES.get(overall), "qa_verdict": verdict, "signed_off": signed,
                    "pipeline_checks_passed": n_pass, "pipeline_checks": len(g)},
        "skill": slim_skill,
        "gates": g,
        "golden_thread": gt,
        "planted_errors": pe,
        "teamwork": team["teamwork"] if team else None,
        "value_added": team["value_added"] if team else None,
        "judges": {"subagents": {a: subs[a] for a in SUBAGENTS if subs[a]}, "teammates": {a: mates[a] for a in TEAMMATES if mates[a]},
                   "note": "AI judges are advisory: they inform the human grader and score no rubric points."},
        "objectives": [{"objective": o, "score": s, "held_back_by": w} for o, (s, w) in zip(OBJECTIVES, objs)],
        "cost": cs,
        "hardcoded_thresholds": hardcoded_thresholds(),
    }
    (out / "system.json").write_text(json.dumps(system, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    print("written: reports/system.md and reports/system.json")
    print("\n".join(head[4:5]))
    for x in g:
        print(f"  [{'pass' if x['pass'] else 'FAIL'}] {x['stage']}: {x['check']}: {x['detail']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
