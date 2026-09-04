# User context

This file is the assistant's persistent memory across the conversation. The
system prompt loads it at the start of every turn. The `remember_fact` tool
appends to the "Known facts" section.

## How to update this file (rules for the assistant)

**Do:**
- Persist user goals, constraints, and stated preferences
- Persist competitors / products the user has already researched so we don't repeat ourselves
- Update an existing fact rather than appending a contradictory one
- Keep each fact atomic — one bullet, one claim, falsifiable

**Don't:**
- Persist trivia ("user said hi"), small talk, or one-off observations
- Persist anything private (emails, names, secrets) without explicit user confirmation
- Re-state what's already here in different words
- Persist guesses or inferences — only what the user has stated or what tools have confirmed

## Known facts

_(this section grows over the conversation)_
