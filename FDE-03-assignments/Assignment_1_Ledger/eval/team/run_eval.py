#!/usr/bin/env python3
"""Evaluate the agent team: planner, challenger, qa-reviewer.

Usage: python eval/team/run_eval.py [--no-judges]

Four parts, all on the run already in the project:
  1. Teammates   each scored 1 to 3 on the six dimensions by a judge (a fresh
                 Claude Code session with read-only tools), against rubric.md.
  2. Teamwork    scored by script from the run transcripts and challenges.md.
  3. Value added what the challenge rounds changed in the pack, first version
                 to last, read from the planner's own announcements.
  4. Planted errors  known mistakes are planted in a copy of the pack; every
                 one must be caught by the QA checks.

--no-judges reuses the judgements saved by the last run (parts 2 to 4 are quick).
Writes eval/team/report.md and eval/team/results.json. Nothing in outputs/
or data/ is changed.
"""
import os as _os, subprocess as _sp, sys as _sys
if __name__ == "__main__" and _os.name == "nt" and not _sys.flags.utf8_mode:  # Windows: rerun in UTF-8 mode
    _sys.exit(_sp.call([_sys.executable, "-X", "utf8", *_sys.argv]))  # (£, →, curly quotes in the data)
import concurrent.futures, csv, json, re, shutil, subprocess, sys, tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
import importlib.util
_spec = importlib.util.spec_from_file_location("subagent_eval", ROOT / "eval/subagents/run_eval.py")
base = importlib.util.module_from_spec(_spec)  # the sub-agent evaluation: judge, transcripts, render
_spec.loader.exec_module(base)

PY = base.PY
OUT = ROOT / "outputs"
PACK = ["planning-memo.md", "risk-control-matrix.md", "audit-program.md", "audit-plan.json", "pack-figures.json", "challenges.md"]
TEAM = {
    "planner": {
        "brief": [".claude/agents/planner.md", ".claude/skills/audit-program/SKILL.md"],
        "outputs": ["outputs/audit-plan.json", "outputs/planning-memo.md", "outputs/risk-control-matrix.md", "outputs/audit-program.md",
                    "outputs/risk-register.md", "outputs/auditor-comments.md", "outputs/rules.json", "outputs/analytics.json", "outputs/challenges.md"],
        "owns": ["outputs/audit-plan.json"],
    },
    "challenger": {
        "brief": [".claude/agents/challenger.md"],
        "outputs": ["outputs/challenges.md", "outputs/audit-plan.json", "outputs/planning-memo.md", "outputs/risk-control-matrix.md",
                    "outputs/audit-program.md", "outputs/risk-register.md", "outputs/analytics.json", "outputs/history.json", "outputs/rules.json"],
        "owns": ["outputs/challenges.md"],
    },
    "qa-reviewer": {
        "brief": [".claude/agents/qa-reviewer.md"],
        "outputs": ["outputs/review.md", "scripts/checks/run_checks.py", "outputs/challenges.md"],
        "owns": ["outputs/review.md"],
    },
}
TEAM_TOOLS = {"SendMessage", "ToolSearch", "Skill", "TaskCreate", "TaskGet", "TaskList", "TaskUpdate", "TaskStop", "SubagentHandback"}


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    return p.returncode, (p.stdout + p.stderr).strip()


def rel(path):
    """A project-relative path with forward slashes, whatever the OS wrote in the transcript."""
    p, root = str(path).replace("\\", "/"), str(ROOT).replace("\\", "/").rstrip("/") + "/"
    return p[len(root):] if p.lower().startswith(root.lower()) else p


# ---------------------------------------------------------------- transcripts
def events(agent):
    """Every tool call the teammate made, oldest first: time, tool, input."""
    ev = []
    for path, _meta in base.find_runs(agent):
        for line in open(path, encoding="utf-8", errors="replace"):
            try:
                o = json.loads(line)
            except Exception:
                continue
            if o.get("type") != "assistant":
                continue
            for b in (o.get("message") or {}).get("content") or []:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    ev.append({"ts": o.get("timestamp", ""), "tool": b.get("name"), "input": b.get("input") or {}})
    return sorted(ev, key=lambda e: e["ts"])


def messages(ev):
    out = []
    for e in ev:
        if e["tool"] == "SendMessage":
            m = e["input"].get("message")
            out.append({"ts": e["ts"], "to": e["input"].get("to", ""), "text": m if isinstance(m, str) else json.dumps(m)})
    return out


def written_paths(ev):
    """Project files a teammate wrote, by Write/Edit or by a shell command."""
    paths = set()
    for e in ev:
        i = e["input"]
        if e["tool"] in ("Write", "Edit"):
            paths.add(rel(i.get("file_path", "")))
        elif e["tool"] == "Bash":
            c = i.get("command", "")
            found = re.findall(r"(?<![0-9&>])>{1,2}\s*([^\s;&|)]+)", c)
            found += re.findall(r"open\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"][wa]", c)
            found += re.findall(r"Path\(\s*['\"]([^'\"]+)['\"]\s*\)\.write_text", c)
            if re.search(r"open\(\s*\w+\s*,\s*['\"][wa]|\.write_text\(|\.write\(", c):
                found += re.findall(r"\b\w+\s*=\s*['\"]((?:outputs|data|scripts|\.claude)/[^'\"]+)['\"]", c)
            found += re.findall(r"sed\s+-i[^\n;|&]*?\s((?:outputs|data|scripts|\.claude)/[^\s;&|]+)", c)
            for f in found:
                f = rel(f.strip("'\""))
                if f.startswith(("/dev/", "/tmp", "/private/tmp", "&")) or not f or f.isdigit():
                    continue
                paths.add(f)
    return {p for p in paths if p.startswith(("outputs/", "data/", "scripts/", ".claude/"))}


def declared_tools(agent):
    text = (ROOT / f".claude/agents/{agent}.md").read_text()
    m = re.search(r"^tools:\s*(.+)$", text, re.M)
    return {t.strip() for t in m.group(1).split(",")} if m else set()


# ---------------------------------------------------------------- challenges.md
def challenge_rows():
    p = OUT / "challenges.md"
    rows = []
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            c = [x.strip() for x in line.strip().strip("|").split("|")]
            if len(c) >= 8 and re.fullmatch(r"\d+", c[0]):
                rows.append({"n": int(c[0]), "type": c[1], "risk": c[2], "evidence": c[4], "response": c[6], "status": c[7].lower()})
    return rows


# ---------------------------------------------------------------- part 2: teamwork
def teamwork():
    ev = {a: events(a) for a in TEAM}
    msg = {a: messages(ev[a]) for a in TEAM}
    rows = challenge_rows()
    checks = []

    def add(name, kind, ok, detail):
        checks.append({"check": name, "kind": kind, "pass": bool(ok), "detail": detail})

    if not any(ev.values()):
        return {"score": None, "checks": [], "note": "No team transcripts found; teamwork cannot be scored."}

    sent = sorted({int(n) for m in msg["challenger"] for n in re.findall(r"CHALLENGE #(\d+)", m["text"])})
    answered = {int(n) for m in msg["planner"] for n in re.findall(r"RESPONSE #(\d+)", m["text"])}
    missing = [n for n in sent if n not in answered]
    add("Every challenge has a response from the planner", "critical", sent and not missing,
        f"{len(sent)} challenges sent, {len(sent) - len(missing)} answered" + (f"; unanswered: {missing}" if missing else ""))

    still = [r["n"] for r in rows if r["status"] in ("open", "")]
    add("No challenge is open at the end", "critical", rows and not still,
        f"{len(rows)} rows in challenges.md; open: {still or 'none'}")

    bad = {}
    for a, spec in TEAM.items():
        extra = sorted(p for p in written_paths(ev[a]) if p not in spec["owns"] and not p.startswith(f".claude/agent-memory/{a}/"))
        if extra:
            bad[a] = extra
    add("Each teammate wrote only the files it owns", "critical", not bad,
        "planner: audit-plan.json; challenger: challenges.md; qa-reviewer: review.md" if not bad else f"wrote outside its remit: {bad}")

    raw = []
    for e in ev["challenger"]:
        text = e["input"].get("file_path", "") + " " + e["input"].get("command", "") + " " + e["input"].get("pattern", "") + " " + e["input"].get("path", "")
        if re.search(r"(?<![\w.-])data/(spend|committee|contracts|contract-rules)|analytics-full", text):
            raw.append(base.short(text, 90))
    add("The challenger read no raw data", "critical", not raw, "no read of data/ or analytics-full/" if not raw else f"{len(raw)} call(s): {raw[:2]}")

    first_resp = min([m["ts"] for m in msg["planner"] if re.search(r"RESPONSE #\d", m["text"])] or ["9"])
    r1 = sum(1 for m in msg["challenger"] if re.match(r"\s*CHALLENGE #\d", m["text"]) and m["ts"] < first_resp)
    r2 = sum(1 for m in msg["challenger"] if re.match(r"\s*CHALLENGE #\d", m["text"]) and m["ts"] >= first_resp)
    add("At most eight challenges in round one and four in round two", "minor", r1 <= 8 and r2 <= 4, f"round one {r1}, round two {r2}")

    outside = {}
    for a in TEAM:
        used = {e["tool"] for e in ev[a]}
        extra = sorted(used - declared_tools(a) - TEAM_TOOLS)
        if extra:
            outside[a] = extra
    add("Each teammate used only the tools its definition lists", "minor", not outside,
        "all within their definitions" if not outside else "; ".join(f"{a} also used {', '.join(t)}" for a, t in outside.items()))

    resp_msgs = [m for m in msg["planner"] if re.search(r"RESPONSE #\d", m["text"])]
    no_pack = [m["ts"][11:19] for m in resp_msgs
               if "PACK READY" not in m["text"] and not any(n["ts"] > m["ts"] and "PACK READY" in n["text"] for n in msg["planner"])]
    add("Every response round is followed by a new pack version", "minor", resp_msgs and not no_pack,
        f"{len(resp_msgs)} response messages, each with or followed by PACK READY" if not no_pack else f"no pack version after the response at {no_pack}")

    done = {a: any(w in m["text"] for m in msg[a]) for a, w in (("planner", "PLANNER DONE"), ("challenger", "CHALLENGER DONE"), ("qa-reviewer", "QA DONE"))}
    add("All three teammates reported DONE to the lead", "minor", all(done.values()),
        ", ".join(f"{a}: {'yes' if v else 'NO'}" for a, v in done.items()))

    crit = [c for c in checks if c["kind"] == "critical" and not c["pass"]]
    minor = [c for c in checks if c["kind"] == "minor" and not c["pass"]]
    score = 1 if crit else 2 if minor else 3
    counts = {a: len(msg[a]) for a in TEAM}
    return {"score": score, "checks": checks, "messages": counts}


# ---------------------------------------------------------------- part 3: value added
def value_added():
    versions = {}
    for m in messages(events("planner")):
        v = re.search(r"(?:PACK READY|PLANNER DONE) v(\d+)", m["text"])
        f = re.search(r"controls: (\d+); tests: (\d+); sampled transactions: (\d+); rules cited: (\d+)/(\d+)", m["text"])
        if v and f:
            versions[int(v.group(1))] = {"controls": int(f.group(1)), "tests": int(f.group(2)), "sampled transactions": int(f.group(3)),
                                        "rules cited": int(f.group(4)), "rules in total": int(f.group(5))}
    rows = challenge_rows()
    by_status, by_type = {}, {}
    for r in rows:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
        by_type[r["type"]] = by_type.get(r["type"], 0) + 1
    out = {"versions": len(versions), "challenges": len(rows), "by_status": by_status, "by_type": by_type}
    if versions:
        out["first"], out["last"] = versions[min(versions)], versions[max(versions)]
        out["first_version"], out["last_version"] = min(versions), max(versions)
    return out


# ---------------------------------------------------------------- part 4: planted errors
def pack_copy(tmp):
    d = Path(tmp)
    for f in PACK:
        if (OUT / f).exists():
            shutil.copy(OUT / f, d / f)
    if (OUT / "samples").is_dir():
        shutil.copytree(OUT / "samples", d / "samples")
    else:
        (d / "samples").mkdir()
    return d


def edit_csv(path, fn):
    rows = list(csv.DictReader(open(path, newline="", encoding="utf-8")))
    fn(rows)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def planted_errors():
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        clean = pack_copy(tmp)
        code, text = run([PY, "scripts/checks/run_checks.py", str(clean)])
        results.append({"plant": "Nothing planted (the pack as it is)", "expect": "READY FOR SIGN-OFF",
                        "caught": code == 0, "got": (text.splitlines() or [""])[-1]})

    def trial(name, check, plant):
        with tempfile.TemporaryDirectory() as tmp:
            d = pack_copy(tmp)
            try:
                plant(d)
            except Exception as e:  # no pack yet, or a file missing: nothing to plant into, so nothing caught
                results.append({"plant": name, "expect": f"{check} fails", "caught": False,
                                "got": f"could not plant (pack incomplete): {type(e).__name__}"})
                return
            code, text = run([PY, f"scripts/checks/{check}", str(d)])
            fails = [l.strip() for l in text.splitlines() if l.strip().startswith("FAIL")]
            results.append({"plant": name, "expect": f"{check} fails", "caught": code != 0 and bool(fails),
                            "got": base.short(fails[0], 150) if fails else "no failure reported"})

    def wrong_figure(d):
        p = d / "planning-memo.md"
        p.write_text(p.read_text() + "\nThe sampled value is £123,457.89.\n")

    def first_sample(d):
        return sorted((d / "samples").glob("T-*.csv"))[0]

    def fake_payment(d):
        def f(rows):
            rows[0]["row_id"] = rows[0]["source_file"] + ":999999"
            rows[0]["sheet_row"] = "999999"
        edit_csv(first_sample(d), f)

    def altered_amount(d):
        def f(rows):
            rows[0]["amount"] = str(round(float(rows[0]["amount"]) + 1, 2))
        edit_csv(first_sample(d), f)

    def open_challenge(d):
        p = d / "challenges.md"
        lines = p.read_text().splitlines()
        for i, line in enumerate(lines):
            c = line.strip().strip("|").split("|")
            if len(c) >= 8 and c[0].strip() == "1":
                c[7] = " open "
                lines[i] = "|" + "|".join(c) + "|"
                break
        p.write_text("\n".join(lines) + "\n")

    def plan_edit(fn):
        def g(d):
            p = d / "audit-plan.json"
            plan = json.loads(p.read_text())
            fn(plan)
            p.write_text(json.dumps(plan))
        return g

    def drop_rule(plan):
        plan["rules_not_tested"] = plan["rules_not_tested"][1:]

    def unapproved_risk(plan):
        plan["risks"].append({"id": "R-99", "objective": "planted", "controls": [{"id": "C-99.1", "control": "planted", "cites": ["rule:CPR-01"]}],
                              "tests": [{"id": "T-99.1", "control": "C-99.1", "step": "planted", "evidence": "planted", "cites": ["rule:CPR-01"],
                                         "sample": {"kind": "none", "note": "planted"}, "pbc": []}]})

    trial("A figure in the memo that no script produced", "check_numbers.py", wrong_figure)
    trial("A sampled payment that does not exist", "check_samples.py", fake_payment)
    trial("A sampled payment with its amount changed by £1", "check_samples.py", altered_amount)
    trial("A challenge left open", "check_trace.py", open_challenge)
    trial("A rule neither tested nor given a reason", "check_trace.py", plan_edit(drop_rule))
    trial("A risk planned that the auditor did not approve", "check_trace.py", plan_edit(unapproved_risk))

    with tempfile.TemporaryDirectory() as tmp:
        if not (OUT / "rules.json").exists():
            results.append({"plant": "A rule quote with one word changed", "expect": "verify_quotes.py fails", "caught": False,
                            "got": "could not plant: outputs/rules.json missing"})
            planted = results[1:]
            return {"baseline_ready": results[0]["caught"], "planted": len(planted), "caught": sum(1 for r in planted if r["caught"]), "trials": results}
        rules = json.loads((OUT / "rules.json").read_text())
        q = rules["rules"][0]["verbatim_quote"]
        words = q.split(" ")
        words[len(words) // 2] = "PLANTED"
        rules["rules"][0]["verbatim_quote"] = " ".join(words)
        p = Path(tmp) / "rules.json"
        p.write_text(json.dumps(rules))
        code, text = run([PY, ".claude/skills/extract-rules/verify_quotes.py", str(p), "data/contract-rules.pdf"])
        fails = [l.strip() for l in text.splitlines() if l.strip().startswith("FAIL")]
        results.append({"plant": "A rule quote with one word changed", "expect": "verify_quotes.py fails", "caught": code != 0 and bool(fails),
                        "got": base.short(fails[0], 150) if fails else "no failure reported"})
    planted = results[1:]
    return {"baseline_ready": results[0]["caught"], "planted": len(planted), "caught": sum(1 for r in planted if r["caught"]), "trials": results}


# ---------------------------------------------------------------- part 1: evidence for the judges
def teammate_checks(agent):
    out = []
    if agent == "planner":
        code, text = run([PY, ".claude/skills/audit-program/build_pack.py", "--gate"])
        out.append(f"build_pack.py --gate: exit {code}: " + " | ".join(text.splitlines()[:3]))
        with tempfile.TemporaryDirectory() as tmp:
            code, text = run([PY, ".claude/skills/audit-program/build_pack.py", "--out-dir", tmp])
            out.append(f"build_pack.py (rendered to a temporary folder): exit {code}: " + " | ".join(
                l for l in text.splitlines() if l.startswith(("FAIL", "WARN", "scope:"))))
            for f in ("planning-memo.md", "risk-control-matrix.md", "audit-program.md"):
                a, b = Path(tmp) / f, OUT / f
                if a.exists() and b.exists():
                    out.append(f"outputs/{f} is identical to a fresh build from audit-plan.json: " + ("yes" if a.read_text() == b.read_text() else "NO"))
    elif agent == "challenger":
        rows = challenge_rows()
        va = value_added()
        out.append(f"challenges.md: {len(rows)} rows; by type {va['by_type']}; by status {va['by_status']}")
        nocite = [r["n"] for r in rows if not re.search(r"CPR-\d+|\$\.[\w.\[\]]+|\b(?:AUD|RT|D|T|C)-\d+", r["evidence"])]
        out.append(f"rows whose Evidence cell names no rule, metric path, audit or test: {nocite or 'none'}")
        tw = teamwork()
        out += [f"teamwork check: {c['check']}: {'pass' if c['pass'] else 'FAIL'} ({c['detail']})" for c in tw["checks"]
                if "challenger" in c["check"].lower() or "tools" in c["check"] or "round" in c["check"] or "wrote" in c["check"]]
    elif agent == "qa-reviewer":
        code, text = run([PY, "scripts/checks/run_checks.py"])
        table = [l for l in text.splitlines() if l.startswith("| ") or l.startswith("VERDICT")]
        out.append(f"run_checks.py run now on the current pack: exit {code}")
        out += table
        review = (OUT / "review.md").read_text() if (OUT / "review.md").exists() else ""
        for l in table:
            if l.startswith("| ") and not l.startswith("| Check"):
                out.append(f"this line appears word for word in review.md: {'yes' if l in review else 'NO'}: {l[:60]}")
    return out


def main():
    use_saved = "--no-judges" in sys.argv
    print("teamwork, value added and planted errors (by script)")
    tw, va, pe = teamwork(), value_added(), planted_errors()
    if use_saved:
        results = []
        for a in TEAM:
            p = HERE / "judgements" / f"{a}.json"
            results.append(json.loads(p.read_text()) if p.exists() else {"agent": a, "error": "no saved judgement; run without --no-judges"})
    else:
        if shutil.which("claude") is None:
            sys.exit("STOP: the claude command is not on PATH.")
        print("judging planner, challenger, qa-reviewer (each in a fresh session; this takes a few minutes)")
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
            results = list(ex.map(lambda a: base.judge(a, TEAM[a], HERE / "rubric.md", HERE / "judgements", teammate_checks(a)), TEAM))

    names = base.NAMES
    md = ["# Agent team evaluation", "",
          f"Scored {datetime.now().strftime('%Y-%m-%d')} against `eval/team/rubric.md`. "
          "1 = Critical Failure, 2 = Requires Tuning, 3 = Production Ready. Overall is the lowest score.", "",
          "## Teammates", ""] + base.render(results, "Teammate")
    md += ["", "## Teamwork", "",
           f"Score: **{tw['score']} {names.get(tw['score'], '')}**" if tw.get("score") else tw.get("note", ""), ""]
    if tw.get("checks"):
        md += ["| Check | Kind | Result | Detail |", "|---|---|---|---|"]
        md += [f"| {c['check']} | {c['kind']} | {'pass' if c['pass'] else '**FAIL**'} | {str(c['detail']).replace('|', '/')} |" for c in tw["checks"]]
        md += ["", "Messages sent: " + ", ".join(f"{a} {n}" for a, n in tw["messages"].items()) + "."]
    md += ["", "## Value added by the challenge rounds", ""]
    if va.get("first"):
        md += [f"| Measure | Version {va['first_version']} | Version {va['last_version']} |", "|---|---|---|"]
        md += [f"| {k.capitalize()} | {va['first'][k]} | {va['last'][k]} |" for k in ("controls", "tests", "sampled transactions", "rules cited")]
        md.append("")
    md.append(f"{va['challenges']} challenges across {va['versions']} pack versions. By status: "
              + ", ".join(f"{k} {v}" for k, v in va["by_status"].items()) + ". By type: " + ", ".join(f"{k} {v}" for k, v in va["by_type"].items()) + ".")
    md += ["", "## Planted errors", "",
           f"**{pe['caught']} of {pe['planted']} planted errors caught.** The untouched pack passes: {'yes' if pe['baseline_ready'] else 'NO'}.", "",
           "| Planted | Expected | Caught | What the check said |", "|---|---|---|---|"]
    md += [f"| {t['plant']} | {t['expect']} | {'yes' if t['caught'] else '**NO**'} | {str(t['got']).replace('|', '/')} |" for t in pe["trials"]]
    (HERE / "report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (HERE / "results.json").write_text(json.dumps({"teammates": results, "teamwork": tw, "value_added": va, "planted_errors": pe}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("\n".join(md))
    print(f"\nwritten: {rel(HERE / 'report.md')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
