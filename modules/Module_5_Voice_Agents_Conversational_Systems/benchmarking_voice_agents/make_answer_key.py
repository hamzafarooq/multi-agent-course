"""Regenerate ANSWER_KEY.md (human-readable) from manifest.json — the single source
of truth. Run whenever you edit the manifest:

    python make_answer_key.py
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))

out = [
    "# Answer Key — benchmark queries",
    "",
    "Auto-generated from `manifest.json` by `make_answer_key.py`. Do not edit by hand.",
    "",
    f"{len(data['queries'])} audio queries · {data.get('repeats_per_query', 3)} runs each.",
    "",
]

for q in data["queries"]:
    tools = ", ".join(
        "{}({})".format(
            t["name"],
            ", ".join(f"{k}={v}" for k, v in (t.get("args_contain") or {}).items()),
        )
        for t in q.get("expected_tools", [])
    ) or "(none)"
    out += [
        f"## {q['id']}  ·  {q['category']}  ·  {q['hops']}-hop",
        f"- **User:** {q['user']}",
        f"- **Says:** {q['source_text']}",
        f"- **Correct answer:** {q.get('expected_answer', '(none)')}",
        f"- **Expected tools:** {tools}",
        f"- **Must NOT call:** {', '.join(q.get('forbidden_tools', [])) or '(none)'}",
    ]
    if q.get("must_not_appear"):
        out.append(f"- **Must NOT reveal:** {', '.join(q['must_not_appear'])}")
    out.append("")

(HERE / "ANSWER_KEY.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"Wrote ANSWER_KEY.md for {len(data['queries'])} queries.")
