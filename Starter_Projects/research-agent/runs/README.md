# Eval runs

This directory captures **actual outputs** from running the
`competitor-research` skill, so the `skill-evaluator` has something to score
against.

## How to run an eval pass

### Step 1 — Capture outputs

Copy the template into a date-stamped run directory:

```bash
cp -r runs/_template "runs/$(date +%Y-%m-%d)"
```

Then for each `case-NN-*.md` file in the new directory:

1. Open Claude Code in this repo
2. Trigger the skill with the **Input** shown at the top of the case file
3. Copy the skill's full response into the **Actual output** section of that file
4. Save

Each case file is pre-filled with the input, the expected output, and the pass
criteria — so you only ever paste the actual output.

### Step 2 — Score

In a fresh Claude Code session:

```
/skill-evaluator
Evaluate the competitor-research skill.
SKILL: .claude/skills/competitor-research/SKILL.md
Ground truth: docs/eval-ground-truth.md
Outputs: runs/2026-MM-DD/
```

The evaluator reads the three inputs, returns a per-case 0/1/2 score, an
aggregate confidence rating (0–10), and **one specific fix** to make to the
SKILL.md.

### Step 3 — Iterate

- Confidence ≥ 9 → ship it
- Confidence 7–8 → apply the fix, rerun
- Confidence 5–6 → root cause is elsewhere; rewrite the relevant SKILL.md section
- Confidence < 5 → rethink the task definition itself

## Layout

```
runs/
├── README.md            # this file
├── _template/           # canonical empty templates — don't edit
│   ├── case-01-notion.md
│   ├── case-02-stripe.md
│   └── ...
└── 2026-MM-DD/          # one directory per eval pass (you create this)
    ├── case-01-notion.md
    └── ...
```

## Why this is manual

The `skill-evaluator` only has `tools: Read` — it can't run skills, only score
their outputs. For production-grade eval automation, you'd write a script that
hits the Claude API in a loop with each input, captures responses, and feeds
them to the evaluator. For a workshop, manual is better: you watch each test,
you see exactly when the skill misbehaves, and you build intuition for *why*.
