#!/usr/bin/env python3
"""Score the three sub-agents against eval/subagents/rubric.md.

Usage: python eval/subagents/run_eval.py [agent ...]
       (default: spend-analyst findings-analyst risk-assessor)

For each agent this script:
  1. gathers evidence: the project's own checks, run read-only, and a summary
     of the agent's run transcript (tools used, errors, time, context size);
  2. asks a judge, a fresh Claude Code session with read-only tools, to score
     the six dimensions 1 to 3 with a reason and the evidence it looked at;
  3. writes eval/subagents/report.md and the raw judgements.

Nothing in outputs/ or data/ is changed.
"""
import os as _os, subprocess as _sp, sys as _sys
if __name__ == "__main__" and _os.name == "nt" and not _sys.flags.utf8_mode:  # Windows: rerun in UTF-8 mode
    _sys.exit(_sp.call([_sys.executable, "-X", "utf8", *_sys.argv]))  # (£, →, curly quotes in the data)
import concurrent.futures, glob, json, os, re, shutil, subprocess, sys, tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PY = sys.executable
DIMENSIONS = ["Format adherence", "Response correctness", "Tool use precision", "Security guardrails",
              "Performance", "Business logic compliance"]
NAMES = {1: "Critical Failure", 2: "Requires Tuning", 3: "Production Ready"}
AGENTS = {
    "spend-analyst": {
        "brief": [".claude/agents/spend-analyst.md"],
        "outputs": ["outputs/analytics.json", "outputs/analytics-full/selfcheck.json", "outputs/analytics-full/cleaning-log.json",
                    "scripts/clean.py", "scripts/analyse.py", "scripts/selfcheck.py", "scripts/common.py", "outputs/rules.json"],
    },
    "findings-analyst": {
        "brief": [".claude/agents/findings-analyst.md"],
        "outputs": ["outputs/history.json", "scripts/verify_history.py", "data/committee/"],
    },
    "risk-assessor": {
        "brief": [".claude/agents/risk-assessor.md", ".claude/skills/risk-assessment/SKILL.md"],
        "outputs": ["outputs/risk-ratings.json", "outputs/risk-register.md", "outputs/auditor-comments.md",
                    "outputs/analytics.json", "outputs/history.json", "outputs/rules.json"],
    },
}


def run(cmd, **kw):
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, **kw)
    return p.returncode, (p.stdout + p.stderr).strip()


# ---------------------------------------------------------------- evidence: checks
def checks(agent):
    out = []
    if agent == "spend-analyst":
        sc = ROOT / "outputs/analytics-full/selfcheck.json"
        if sc.exists():
            items = json.loads(sc.read_text())
            ok = sum(1 for i in items if i.get("pass") or i.get("ok") or i.get("match"))
            out.append(f"selfcheck.json: {len(items)} items recorded; {ok} marked as passing; tests covered: "
                       + ", ".join(sorted({str(i.get('test')) for i in items})))
        else:
            out.append("selfcheck.json: NOT FOUND")
        a = json.loads((ROOT / "outputs/analytics.json").read_text())
        out.append("analytics.json tests: " + ", ".join(a.get("tests", {}).keys()))
        out.append("analytics.json skipped tiers recorded: " + str(len(a.get("skipped", []))))
        out.append("analytics.json thresholds: " + ", ".join(f"{t.get('value')} from {t.get('rule_ids')}" for t in a.get("thresholds", [])))
    elif agent == "findings-analyst":
        code, text = run([PY, "scripts/verify_history.py", "outputs/history.json", "data/committee"])
        out.append(f"verify_history.py: exit {code}: " + " | ".join(text.splitlines()[-3:]))
    elif agent == "risk-assessor":
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copy(ROOT / "outputs/auditor-comments.md", Path(tmp) / "comments.md")
            code, text = run([PY, ".claude/skills/risk-assessment/build_register.py", "outputs/risk-ratings.json",
                              "--out", f"{tmp}/register.md", "--comments", f"{tmp}/comments.md"])
            out.append(f"build_register.py (rendered to a temporary folder): exit {code}: " + " | ".join(
                l for l in text.splitlines() if l.startswith(("FAIL", "WARN", "risks kept"))))
            reg = Path(tmp) / "register.md"
            if reg.exists():
                same = reg.read_text() == (ROOT / "outputs/risk-register.md").read_text()
                out.append("outputs/risk-register.md is identical to a fresh build from risk-ratings.json: " + ("yes" if same else "NO (it may have been edited by hand, or the ratings changed since)"))
    return out


# ---------------------------------------------------------------- evidence: transcripts
def transcript_dirs():
    """Claude Code keeps each project's transcripts in ~/.claude/projects/<slug>, where the slug is the
    project path with every non-alphanumeric character turned into '-' (G:\\x\\y -> G--x-y, /Users/a/b -> -Users-a-b).
    The drive letter's case depends on how the folder was opened, so match case-insensitively.
    LEDGER_TRANSCRIPTS=<dir> overrides the search (used by the eval's own tests)."""
    if os.environ.get("LEDGER_TRANSCRIPTS"):
        return [Path(os.environ["LEDGER_TRANSCRIPTS"])]
    base = Path.home() / ".claude/projects"
    slug = re.sub(r"[^A-Za-z0-9]", "-", str(ROOT))
    if not base.is_dir():
        return []
    return [d for d in base.iterdir() if d.is_dir() and d.name.lower() == slug.lower()]


def find_runs(agent):
    runs = []
    metas = [m for d in transcript_dirs() for m in glob.glob(str(d / "*/subagents/agent-*.meta.json"))]
    for meta in metas:
        try:
            m = json.loads(Path(meta).read_text())
        except Exception:
            continue
        if str(m.get("agentType", "")).startswith(agent):
            runs.append((Path(meta.replace(".meta.json", ".jsonl")), m))
    return runs


def short(v, n=200):
    return re.sub(r"\s+", " ", str(v))[:n]


def summarise(path, meta):
    calls, results, t0, t1, peak, out_tok = [], {}, None, None, 0, 0
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
        content = m.get("content")
        if o.get("type") == "assistant":
            u = m.get("usage") or {}
            peak = max(peak, u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0))
            out_tok += u.get("output_tokens", 0)
            for b in content or []:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    inp = b.get("input") or {}
                    what = inp.get("command") or inp.get("file_path") or inp.get("pattern") or inp.get("skill") or inp.get("to") or ""
                    calls.append({"id": b.get("id"), "tool": b.get("name"), "what": short(what)})
        elif o.get("type") == "user" and isinstance(content, list):
            for b in content:
                if isinstance(b, dict) and b.get("type") == "tool_result":
                    c = b.get("content")
                    s = c if isinstance(c, str) else json.dumps(c)
                    results[b.get("tool_use_id")] = (bool(b.get("is_error")), len(s))
    secs = None
    try:
        secs = (datetime.fromisoformat(t1.replace("Z", "+00:00")) - datetime.fromisoformat(t0.replace("Z", "+00:00"))).total_seconds()
    except Exception:
        pass
    lines = [f"Run: {meta.get('agentType')} ({meta.get('description', '')}); started {t0}; "
             f"duration {secs:.0f} seconds; peak context {peak:,} tokens; output {out_tok:,} tokens"
             if secs is not None else f"Run: {meta.get('agentType')}"]
    tools = Counter(c["tool"] for c in calls)
    errs = sum(1 for c in calls if results.get(c["id"], (False, 0))[0])
    biggest = max([results.get(c["id"], (False, 0))[1] for c in calls] or [0])
    lines.append(f"Tool calls: {len(calls)} ({', '.join(f'{k} {v}' for k, v in tools.items())}); "
                 f"calls that returned an error: {errs}; largest tool output: {biggest:,} characters")
    for n, c in enumerate(calls, 1):
        err, size = results.get(c["id"], (False, 0))
        lines.append(f"  {n}. {c['tool']}{' [ERROR]' if err else ''} ({size:,} chars back): {c['what']}")
    return t0 or "", lines


def transcripts(agent):
    runs = sorted((summarise(p, m) for p, m in find_runs(agent)), key=lambda x: x[0])
    if not runs:
        return ["No run transcript found for this agent. Tool use and performance cannot be evidenced."]
    out = [f"{len(runs)} run(s) found, oldest first."]
    for _, lines in runs:
        out += [""] + lines
    return out


# ---------------------------------------------------------------- the judge
def rubric_for(agent, rubric=None):
    text = Path(rubric or HERE / "rubric.md").read_text()
    head = text.split("\n## ")
    keep = [head[0]] + [s for s in head[1:] if s.startswith(("The scale", "The dimensions", agent))]
    return "\n## ".join(keep)


def judge(agent, spec=None, rubric=None, outdir=None, check_lines=None):
    """Score one agent. spec, rubric, outdir and check_lines let the team evaluation reuse this."""
    spec = spec or AGENTS[agent]
    outdir = Path(outdir or HERE / "judgements")
    evidence = "\n".join(["CHECKS RUN BY THE EVALUATION (read-only)", *("- " + c for c in (check_lines if check_lines is not None else checks(agent))), "",
                          "RUN TRANSCRIPT SUMMARY (tool inputs are shortened; tool outputs are not shown)", *transcripts(agent)])
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / f"{agent}.evidence.txt").write_text(evidence + "\n", encoding="utf-8")
    prompt = f"""You are evaluating one sub-agent of this project against a rubric. You are a strict, fair reviewer.

Sub-agent: {agent}

Read, in this order:
1. Its brief: {', '.join(spec['brief'])}
2. Its outputs and inputs: {', '.join(spec['outputs'])}
   Read JSON and Markdown files. Do not read whole CSV files; their first lines are enough.
3. The evidence gathered for you, below.

Then score each of the six dimensions 1, 2 or 3 using the rubric below. Rules:
- Judge only from what you read. Give 3 only when you found evidence for it; when evidence is missing, give 2 and say what is missing.
- Give 1 only for what the rubric calls a critical failure, and name the exact file or transcript item that shows it.
- Reasons are one or two plain sentences. Never write a supplier name or a supplier-level amount in a reason.
- Evidence names the file, section or transcript item you relied on.
- You may only read. Do not create or change any file.

Reply with one JSON object and nothing else, in this form:
{{"agent": "{agent}", "scores": [{{"dimension": "<one of: {'; '.join(DIMENSIONS)}>", "score": 1, "reason": "...", "evidence": "..."}}]}}
with exactly one entry per dimension, in the order given.

RUBRIC
{rubric_for(agent, rubric)}

EVIDENCE
{evidence}
"""
    p = subprocess.run([shutil.which("claude") or "claude", "-p", "--no-session-persistence", "--allowedTools", "Read,Grep,Glob", "--output-format", "json"],
                       input=prompt, capture_output=True, text=True, cwd=ROOT)
    raw = p.stdout
    try:
        text = json.loads(raw).get("result", "")
    except Exception:
        text = raw
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return {"agent": agent, "error": "the judge returned no JSON", "raw": text[:2000] or p.stderr[:2000]}
    try:
        res = json.loads(m.group(0))
    except Exception as e:
        return {"agent": agent, "error": f"the judge's JSON could not be read: {e}", "raw": text[:2000]}
    (outdir / f"{agent}.json").write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return res


def overall(result):
    scores = [s.get("score") for s in result.get("scores", []) if isinstance(s.get("score"), int)]
    return min(scores) if scores else None


def render(results, heading="Agent"):
    """The summary table and one detail table per agent, as Markdown lines."""
    md = [f"| {heading} | " + " | ".join(DIMENSIONS) + " | Overall |", "|---|" + "---|" * (len(DIMENSIONS) + 1)]
    for r in results:
        if r.get("error"):
            md.append(f"| {r['agent']} | " + " | ".join("?" for _ in DIMENSIONS) + " | not scored |")
            continue
        by = {s["dimension"]: s for s in r["scores"]}
        scores = [by.get(d, {}).get("score") for d in DIMENSIONS]
        o = overall(r) or 0
        md.append(f"| {r['agent']} | " + " | ".join(str(s) if s else "?" for s in scores) + f" | **{o} {NAMES.get(o, '')}** |")
    clean = lambda t: str(t).replace("|", "/").replace("\n", " ")
    for r in results:
        md += ["", f"## {r['agent']}", ""]
        if r.get("error"):
            md += [f"Not scored: {r['error']}.", ""]
            continue
        md += ["| Dimension | Score | Reason | Evidence |", "|---|---|---|---|"]
        by = {s["dimension"]: s for s in r["scores"]}
        for d in DIMENSIONS:
            s = by.get(d)
            if not s:
                md.append(f"| {d} | ? | the judge gave no score | |")
                continue
            md.append(f"| {d} | {s['score']} {NAMES.get(s['score'], '')} | {clean(s.get('reason', ''))} | {clean(s.get('evidence', ''))} |")
    return md


def main():
    agents = sys.argv[1:] or list(AGENTS)
    for a in agents:
        if a not in AGENTS:
            sys.exit(f"STOP: unknown agent {a}. Choose from: {', '.join(AGENTS)}")
    if shutil.which("claude") is None:
        sys.exit("STOP: the claude command is not on PATH.")
    print(f"judging {', '.join(agents)} (each in a fresh session; this takes a few minutes)")
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        results = list(ex.map(judge, agents))

    md = ["# Sub-agent evaluation", "",
          f"Scored {datetime.now().strftime('%Y-%m-%d')} against `eval/subagents/rubric.md`. "
          "1 = Critical Failure, 2 = Requires Tuning, 3 = Production Ready. Overall is the lowest score.", ""] + render(results)
    bad = any(r.get("error") for r in results)
    (HERE / "report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    print(f"\nwritten: {HERE / 'report.md'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
