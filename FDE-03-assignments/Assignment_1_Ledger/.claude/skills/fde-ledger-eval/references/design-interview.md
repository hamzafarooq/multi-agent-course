# The design interview

Five questions, one per DESIGN.md heading. Ask them one at a time, **after** reading the
student's `DESIGN.md` and their harness files, and make each one specific to what they wrote:
quote their own sentence back and ask about the part a spec could not have decided for them.
Record each answer **verbatim** in `design-interview.md` at the project root, in this shape:

```markdown
# Design interview

## Q1: <the question exactly as asked>
<the student's answer, verbatim, no edits, no summary>

## Q2: ...
```

The rules:

- You ask; you never answer, hint at the answer, or tidy their words.
- You do not score the answers. A person grades the `design` row and reads these alongside
  DESIGN.md (rule E3: a model may report, never decide).
- If they say "I don't know", record exactly that. It is information, not a failure of the step.

Question stems, to make specific:

| # | Heading | Stem |
|---|---|---|
| Q1 | Components | "You made X a skill and Y a sub-agent. What would break, or get worse, if X were part of Y's brief instead?" |
| Q2 | Responsibilities | "Your challenger's tools are …. Name one thing it cannot do because of that, and why you wanted it unable to." |
| Q3 | Communication | "The spend-analyst's output is missing a column the pack builder needs. Walk me through who notices, when, and what they do." |
| Q4 | State | "An agent's memory says one thing and today's input says another. Which wins, where is that written, and why?" |
| Q5 | Trade-offs | "You listed <their least-sure trade-off>. What evidence from your run would make you change it?" |
