#!/usr/bin/env python3
"""Export every sub-agent and teammate run of THIS project into runs/<run id>.json.

Usage: python eval/export_runs.py [--list]

Claude Code keeps each agent's transcript under ~/.claude/projects/<project>/.
This reads the six agents' transcripts (spend-analyst, findings-analyst,
risk-assessor, planner, challenger, qa-reviewer) and writes one run log each,
in the course's run-log shape, so that:
  - quality/check.mjs can hold every run to the budget in expectations.json,
  - eval/build_report.py can check each agent's own envelope (perAgent),
  - you can pick the two trajectories you read end to end (trajectories.md).

Run log: {requestId, agent, description, startedAt, terminated ("done" or
"incomplete"), tokens (PEAK context of the run), outputTokens, wallClockSec,
toolCalls: [{name, ok, error, what, outputChars}]}. `what` is the tool input,
shortened; tool OUTPUTS are never copied (they hold data).

A run you keep as your FAILING trajectory and that did not finish (terminated:
"incomplete") goes in runs/failing/: quality/check.mjs grades every run in runs/*.json
and would fail it (rule A2), while build_report.py reads both folders. Re-exporting
never puts it back in runs/.
"""
import os as _os, subprocess as _sp, sys as _sys
if __name__ == "__main__" and _os.name == "nt" and not _sys.flags.utf8_mode:  # Windows: rerun in UTF-8 mode
    _sys.exit(_sp.call([_sys.executable, "-X", "utf8", *_sys.argv]))  # (£, →, curly quotes in the data)
import importlib.util, json, sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("subagent_eval", ROOT / "eval/subagents/run_eval.py")
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

AGENTS = ["spend-analyst", "findings-analyst", "risk-assessor", "planner", "challenger", "qa-reviewer"]


def parse(path, meta, agent):
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
                    what = (inp.get("command") or inp.get("file_path") or inp.get("pattern") or inp.get("skill")
                            or (f"to {inp.get('to')}: {inp.get('message')}" if inp.get("to") else "") or inp.get("description") or "")
                    calls.append({"id": b.get("id"), "name": b.get("name"), "what": base.short(what, 240)})
        elif o.get("type") == "user" and isinstance(content, list):
            for b in content:
                if isinstance(b, dict) and b.get("type") == "tool_result":
                    c = b.get("content")
                    s = c if isinstance(c, str) else json.dumps(c)
                    results[b.get("tool_use_id")] = (bool(b.get("is_error")), len(s), base.short(s, 200) if b.get("is_error") else "")
    secs = None
    try:
        secs = round((datetime.fromisoformat(t1.replace("Z", "+00:00")) - datetime.fromisoformat(t0.replace("Z", "+00:00"))).total_seconds())
    except Exception:
        pass
    tool_calls = []
    for c in calls:
        err, size, msg = results.get(c["id"], (False, 0, ""))
        tc = {"name": c["name"], "ok": not err, "what": c["what"], "outputChars": size}
        if err:
            tc["error"] = msg or "tool returned an error"
        tool_calls.append(tc)
    rid = f"{agent}-{(t0 or 'unknown')[:19].replace(':', '').replace('-', '')}-{path.stem.replace('agent-', '')[:6]}"
    return {
        "requestId": rid, "agent": agent, "description": meta.get("description", ""), "startedAt": t0,
        "terminated": "done" if meta.get("finished", True) else "incomplete",
        "tokens": peak, "outputTokens": out_tok, "wallClockSec": secs,
        "toolCalls": tool_calls, "errors": sum(1 for t in tool_calls if not t["ok"]),
    }


def export():
    out = ROOT / "runs"
    out.mkdir(exist_ok=True)
    runs = []
    for agent in AGENTS:
        for path, meta in base.find_runs(agent):
            if str(meta.get("agentType", "")) != agent:  # find_runs matches by prefix; keep exact names only
                continue
            r = parse(Path(path), meta, agent)
            if (out / "failing" / f"{r['requestId']}.json").exists():  # kept as your failing trajectory: leave it there
                runs.append(r)
                continue
            (out / f"{r['requestId']}.json").write_text(json.dumps(r, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            runs.append(r)
    return sorted(runs, key=lambda r: r["startedAt"] or "")


def main():
    dirs = base.transcript_dirs()
    runs = export()
    if not dirs:
        print("No Claude Code transcripts found for this folder. Open THIS folder in Claude Code (not a parent) and run the agents first.")
        return 1
    print(f"{len(runs)} agent run(s) exported to runs/ from {dirs[0]}")
    print(f"\n| Run id | Agent | Minutes | Tool calls | Errors | Peak context | Terminated |\n|---|---|---|---|---|---|---|")
    for r in runs:
        mins = "?" if r["wallClockSec"] is None else f"{r['wallClockSec'] / 60:.0f}"
        print(f"| {r['requestId']} | {r['agent']} | {mins} | {len(r['toolCalls'])} | {r['errors']} | {r['tokens']:,} | {r['terminated']} |")
    if runs:
        print("\nPick one successful and one failing run for trajectories.md (copy trajectories.template.md).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
