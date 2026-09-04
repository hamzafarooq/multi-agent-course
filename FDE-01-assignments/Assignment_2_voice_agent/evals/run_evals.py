"""Run deterministic Aurora task and red-team evaluations with no API cost."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PIPELINE = ROOT / "pipeline"
if str(PIPELINE) not in sys.path:
    sys.path.insert(0, str(PIPELINE))

os.environ["PROVIDER"] = "mock"
os.environ.setdefault("TTS_BACKEND", "print")

from agent import Agent  # noqa: E402
from providers import make_provider  # noqa: E402
from telemetry import TurnTrace  # noqa: E402


def _tool_names(trace: dict) -> list[str]:
    return [
        event["attributes"].get("tool", "")
        for event in trace["events"]
        if event["name"] == "tool.requested"
    ]


def _check(expect: dict, reply: str, action: str | None, trace: dict) -> list[str]:
    failures: list[str] = []
    if "contains" in expect and expect["contains"].lower() not in reply.lower():
        failures.append(f"reply missing {expect['contains']!r}")
    for forbidden in expect.get("forbid", []):
        if forbidden.lower() in reply.lower():
            failures.append(f"reply contains forbidden text {forbidden!r}")
    if "action" in expect and action != expect["action"]:
        failures.append(f"action was {action!r}, expected {expect['action']!r}")
    if "tools" in expect:
        actual_tools = _tool_names(trace)
        if actual_tools != expect["tools"]:
            failures.append(f"tools were {actual_tools!r}, expected {expect['tools']!r}")
    if "language" in expect:
        actual_language = trace["attributes"].get("language")
        if actual_language != expect["language"]:
            failures.append(f"language was {actual_language!r}, expected {expect['language']!r}")
    if "sourceContains" in expect:
        sources = trace["attributes"].get("sources", [])
        if not any(expect["sourceContains"] in source for source in sources):
            failures.append(f"sources did not include {expect['sourceContains']!r}")
    return failures


def run_case(case: dict, verbose: bool = False) -> tuple[bool, list[str]]:
    agent = Agent(make_provider("mock"))
    failures: list[str] = []
    for index, turn in enumerate(case["turns"], start=1):
        trace = TurnTrace(session_id=f"eval-{case['id']}", turn_id=f"turn-{index}")
        reply, action = agent.respond(turn["user"], trace=trace)
        payload = trace.finish(action=action, sources=agent.last_sources)
        turn_failures = _check(turn.get("expect", {}), reply, action, payload)
        failures.extend(f"turn {index}: {failure}" for failure in turn_failures)
        if verbose:
            print(f"  caller: {turn['user']}")
            print(f"  agent:  {reply}")
            print(f"  tools:  {_tool_names(payload)}")
    return not failures, failures


def load_cases(suite: str) -> list[dict]:
    paths = []
    if suite in ("core", "all"):
        paths.append(Path(__file__).with_name("core.json"))
    if suite in ("red-team", "all"):
        paths.append(Path(__file__).with_name("red_team.json"))
    cases = []
    for path in paths:
        cases.extend(json.loads(path.read_text(encoding="utf-8")))
    return cases


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Aurora voice-agent evaluations")
    parser.add_argument("--suite", choices=("core", "red-team", "all"), default="all")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    passed = 0
    cases = load_cases(args.suite)
    for case in cases:
        ok, failures = run_case(case, verbose=args.verbose)
        print(f"{'PASS' if ok else 'FAIL'}  {case['id']}: {case['description']}")
        for failure in failures:
            print(f"      {failure}")
        passed += int(ok)

    print(f"\nScore: {passed}/{len(cases)} scenarios passed")
    raise SystemExit(0 if passed == len(cases) else 1)


if __name__ == "__main__":
    main()
