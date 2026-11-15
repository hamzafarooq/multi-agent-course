# Module 2 lab · Expense check

Northwind Logistics, a delivery company, wants its expense claims checked against its own
policy. In class you build the harness for it in three moves, ten minutes each:

1. a **skill** that turns the policy into rules, every one with a word-for-word quote,
2. a **subagent** that checks all 40 claims against those rules, with Python it writes and runs,
3. an **eval** that tells you whether the skill is right, not just whether it ran.

It is the same shape as your assignment, Ledger, at a size you can finish in class. The
company and everyone in the data are made up.

## Start

Copy this folder somewhere outside the course repo and open **that folder** in VS Code with
Claude Code. Opened from inside the course repo, Claude Code would also load the course's own
`CLAUDE.md` and skills, and your eval would not be measuring your skill alone.

```bash
cp -R fde-companion-kit/labs/m2-expense-check ~/m2-expense-check
code ~/m2-expense-check
```

Python 3 is all you need. The tools use nothing outside the standard library.

## What's here

| File | What it is |
|---|---|
| `policy.md` | The travel and expense policy: 22 numbered clauses. Some are rules, some are not. |
| `claims.csv` | 40 expense claims from March and April 2026. |
| `schema.json` | The shape of `outputs/rules.json`, with a note on every field. |
| `.claude/skills/extract-rules/SKILL.md` | Build 1. A stub for you to fill in. |
| `.claude/agents/expense-checker.md` | Build 2. A stub for you to fill in. |
| `tools/verify_quotes.py` | Checks every quote against the policy, and that every clause is accounted for. |
| `tools/run_eval.py`, `tools/score_skill.py` | Build 3. The eval of your skill. |
| `answer-key.csv` | 14 clauses, decided by a person from the policy: rule or not, and the right fields. |
| `tools/check_flags.py`, `flags-key.csv` | Checks the subagent's flags against the claims that really break a rule. |

Don't edit the policy, the claims, the keys or the tools. The point of an answer key is that
nobody moves it after seeing the score.

## Build 1 · The skill (10 minutes)

A skill is a procedure you would otherwise type out every time. Open
`.claude/skills/extract-rules/SKILL.md`, read the TODO, then ask Claude Code:

> Read policy.md, schema.json and the TODO in .claude/skills/extract-rules/SKILL.md. Write the
> skill: the description first, then the procedure. Every clause must end up in rules or
> excluded, every quote copied word for word, and the skill must run tools/verify_quotes.py
> until it passes.

Read what it wrote. Fix the description yourself: it is the line Claude reads to decide when
the skill runs. Then start a new session and type `/extract-rules`. Open `outputs/rules.json`.

Done when `python3 tools/verify_quotes.py` prints `ALL CHECKS PASSED`.

## Build 2 · The subagent (10 minutes)

A subagent works in its own context and hands back only a summary. This one checks 40 claims,
which would fill your main session with tables. Open `.claude/agents/expense-checker.md`, then:

> Read the TODO in .claude/agents/expense-checker.md, claims.csv's header and
> outputs/rules.json. Write the subagent's brief. It writes and runs Python and never does
> maths in its head; thresholds come only from rules.json; it writes outputs/flags.csv. Give it
> only the tools it needs.

Then ask: *Use the expense-checker to check the claims.* Watch it work in its own context.

Done when `python3 tools/check_flags.py` prints `PASS`: every claim that breaks a rule caught,
no false alarms. Several claims sit exactly on a limit and break nothing. Does yours know?

## Build 3 · The eval (10 minutes)

Your skill ran and the rules look right. Are they right?

```bash
python3 tools/run_eval.py --runs 3
```

It runs `/extract-rules` three times, each in a fresh Claude Code session with no memory of
the last, and scores each run against `answer-key.csv`:

| Score | Question | Bar |
|---|---|---|
| found | Of the real rules in the key, how many did the skill turn into rules? | 90% |
| not invented | Of the key clauses it turned into rules, how many really are rules? | 90% |
| fields right | Are the thresholds, approver and action right? | 85% |

The weakest of the three runs is the one that counts: one good run can be luck. The bars were
set before anyone ran the skill, and they don't move.

Read what it missed, change one thing in your skill, and run it again.

## The shape of rules.json

```json
{
  "source": "policy.md",
  "rules": [
    {
      "rule_id": "R01", "clause": "2.3",
      "quote": "A receipt must be attached to any claim of $25 or more.",
      "applies_to": "any claim",
      "threshold_low": 25, "threshold_high": null, "inclusive": true, "unit": "USD",
      "approver": null, "action": "attach a receipt", "parameters": {}
    }
  ],
  "excluded": [
    { "clause": "1.1", "reason": "Says what the policy is for. Nothing is required of anyone." }
  ]
}
```

`schema.json` explains every field.

## For instructors

`instructor/` holds a working skill and subagent, kept outside `.claude/` so they don't load.
To use them, copy `instructor/skills` and `instructor/agents` into `.claude/`.
