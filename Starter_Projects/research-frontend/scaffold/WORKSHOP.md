# Workshop — Build the Research Frontend

You're starting from a working UI + corpus + memory templates. Your job is to
fill in the three mode handlers and their supporting libs. After each exercise,
run the app and play with the corresponding tab — the behavior should change.

## Setup

```bash
cd research-frontend/scaffold
npm install
npx playwright install chromium
cp .env.example .env.local   # fill in ANTHROPIC_API_KEY
npm run dev
```

Open http://localhost:3000.

---

## Exercise 1 — Warm-up: bare LLM call

**File:** `app/api/chat/modes/llm-only.ts`

**Goal:** Make Tab 1 actually call Claude.

**What you'll build:** A single `anthropic.messages.create` call with no
tools, returning the text content. ~10 lines.

**Hints:**
- Use `anthropic` and `MODEL` from `@/lib/anthropic`.
- The API expects `messages: [{ role, content }]` — translate from ChatMessage.
- `response.content` is an array of blocks; filter for `type === "text"`.

**Run it:** Ask Tab 1 *"Who are Wispr Flow's competitors?"* — expect a confident
but un-grounded answer with no tool traces.

**Stuck?** Peek at `research-frontend/demo/app/api/chat/modes/llm-only.ts`.

---

## Exercise 2 — Tools: RAG + Web Search + Browser

**Files:**
- `lib/rag.ts` — implement MiniSearch retrieval over the corpus
- `app/api/chat/modes/llm-tools.ts` — the tool_use loop

**Goal:** Make Tab 2 use the corpus, web search, and a real browser.

**What you'll build:**
1. `ragSearch(query, limit)` — index the 5 corpus markdown files and return top
   matches.
2. `runLlmTools` — call the API with `tools` from `@/lib/tools`, loop on
   `stop_reason === "tool_use"`, dispatch each `tool_use` via `executeToolUse`
   from `@/lib/tool-loop`, return when the model stops requesting tools.

**Hints:**
- See MiniSearch docs at https://lucaong.github.io/minisearch/
- Split each corpus file on `^## ` headings to create section-sized chunks.
- The tool_use loop pattern is in Anthropic's tool use docs — `tool_use` blocks
  go in the assistant message, `tool_result` blocks go back in the next user
  message with the matching `tool_use_id`.
- Stop after ~6 iterations to avoid runaway loops.

**Run it:** Ask Tab 2 the same question as Tab 1 — expect yellow tool-trace
boxes followed by an answer naming the four corpus competitors with sources.

**Stuck?** Peek at the corresponding `demo/` files.

---

## Exercise 3 — Memory: CLAUDE.md + SKILL.md + remember_fact

**Files:**
- `lib/memory.ts` — read/append for CLAUDE.md, read for SKILL.md
- `app/api/chat/modes/llm-tools-memory.ts` — system prompt with memory + skill

**Goal:** Make Tab 3 read persistent context, follow a procedure, and persist
new facts.

**What you'll build:**
1. `readMemory`, `readSkill`, `appendFact` — file I/O over `memory/CLAUDE.md`
   and `skills/research/SKILL.md`.
2. `runLlmToolsMemory` — load both files, compose
   `SKILL.md\n\n<user_context>\nCLAUDE.md\n</user_context>` as the system
   prompt, use `toolsForMemoryMode` (which adds `remember_fact`), same tool
   loop as Exercise 2.

**Hints:**
- `appendFact` should insert a bullet under `## Known facts`. Watch out for
  the `_(this section grows ...)_` placeholder text — remove it once you start
  appending real facts.
- The model decides when to call `remember_fact` based on CLAUDE.md's own
  persistence rules. Don't force it from code.

**Run it:** Ask Tab 3 *"I'm tracking the agent-voice-interface gap. What's
unclaimed?"* Expect a `remember_fact` trace and the right rail to gain a new
bullet. Then ask a follow-up that references your prior framing — the model
should pick it up from CLAUDE.md.

**Stuck?** Peek at the `demo/` versions.

---

## Stretch — Exercise 4: Embeddings instead of keywords

Swap `MiniSearch` for `voyage-3-lite` embeddings in `lib/rag.ts`. Set
`VOYAGE_API_KEY` in `.env.local`. Compute corpus embeddings on first run, cache
to `corpus/.embeddings.json`. Use cosine similarity.

Compare retrieval quality on these queries:
- "dictation pricing gap" (semantic — embeddings should win)
- "Wispr Flow" (exact term — keyword is fine)

---

## Stretch — Exercise 5: Managed RAG via Traversaal Pro

Upload `corpus/*.md` to https://pro.traversaal.ai/, get a Bearer token, set
`TRAVERSAAL_API_KEY` in `.env.local`. Replace `ragSearch` with a fetch to their
API. Same answer shape — different retriever.

Reflect: when would you build (MiniSearch / Voyage) vs. buy (Traversaal)?
