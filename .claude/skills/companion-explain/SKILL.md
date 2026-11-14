---
name: companion-explain
description: Explain an FDE, LLM, agent or Claude Code term in plain words (like to a ten-year-old), with a data-science comparison when that helps, with a pointer to the book and the companion topic that covers it. Use when the student types /companion-explain <term or question>.
argument-hint: <term or question>
---

# /companion-explain <term or question>

The student asked about: `$ARGUMENTS`

1. Look the term up in `fde-companion-kit/glossary.md`. Use its plain words, data-science line, exact meaning and topic as your anchor, so your explanation matches the site and the book.

2. Answer in this shape, short:
   - **In plain words**: the glossary's explanation, the way you'd tell a ten-year-old.
   - **Coming from data science**: the glossary's line, when the student's role in `progress/learner-progress.md` says data, ML or analytics, or they ask for it. Otherwise skip it, or use a comparison from their own field.
   - **An analogy or a concrete example**, ideally from the companion (Parcelly's `lookup_order`, the tip splitter, Tidewell's tickets) or from FDE work with a client.
   - **Why it matters in the bootcamp**: one sentence.
   - **Read more:** the book section, the companion topic, and the term on https://companion.traversaal.ai/glossary/, for example "Book §3.2 · 2.2". For terms the bootcamp covers later, name the module instead, for example "Module 4".

3. If the term isn't in the glossary, answer anyway in the same shape, and say if the companion doesn't cover it yet.

4. End with one quick question that checks understanding, for example "So if the model asks for `lookup_order`, who actually runs it?"
