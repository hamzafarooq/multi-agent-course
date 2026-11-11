---
name: companion-explain
description: Explain an FDE, LLM, agent or Claude Code term from the companion in plain language, with a pointer to the book and the companion topic that covers it. Use when the student types /companion-explain <term or question>.
argument-hint: <term or question>
---

# /companion-explain <term or question>

The student asked about: `$ARGUMENTS`

1. Look the term up in `glossary.md`. Use its definition, topic and book section as your anchor, so your explanation matches the site and the book.

2. Answer in this shape, short:
   - **One-line definition** in plain English.
   - **An analogy or a concrete example**, ideally from the companion (Parcelly's `lookup_order`, the tip splitter, Tidewell's tickets) or from FDE work with a client.
   - **Why it matters in the bootcamp**: one sentence.
   - **Read more:** the book section and the companion topic, for example "Book §3.2 · 1.1". For terms the bootcamp covers later, name the module instead, for example "Module 3".

3. If the term isn't in the glossary, answer anyway in the same shape, and say if the companion doesn't cover it yet.

4. End with one quick question that checks understanding, for example "So if the model asks for `lookup_order`, who actually runs it?"
