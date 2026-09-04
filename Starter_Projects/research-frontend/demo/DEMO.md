# Demo script — Agentic AI PM course

Five tabs, a contrastive memory ladder. Each tab changes exactly one variable.
The collapsible **Lesson** panel at the top of every tab shows the same two
comparison tables (Behavior / Capabilities) with the current row highlighted.

## The headline: the 🔄 New session punchline

Run this two-turn script in **+ Short-term**, then in **+ Long-term**:

1. `My name is Aishwarya and I'm researching Luma AI.`
2. `What's my name, and what am I researching?`

Both recall it correctly. Now press **🔄 New session** in each tab and ask
turn 2 again:

| Tab | After 🔄 New session |
|---|---|
| **+ Short-term** | "I don't have that — this is a fresh conversation." Transcript was volatile; it died with the session. |
| **+ Long-term** | "You're Aishwarya, researching Luma AI." It re-read memory/CLAUDE.md from disk. Sticky: 📄 CLAUDE.md loaded (+ 💾 remember_fact on turn 1). |

That single contrast is the whole lesson: short-term = replayed transcript,
long-term = a persisted store re-injected every request.

---

## Tab 1 — LLM (stateless)

`What's my name?` after any earlier message → it cannot know. There is no
history and no memory; only the current message reaches the model.
Sticky: 🧠 **LLM only**.

## Tab 2 — + Short-term

The transcript is replayed every turn, so multi-turn conversation works.
Sticky every turn: 💬 **Short-term memory**. Press 🔄 → amnesia.

## Tab 3 — + Long-term

No transcript is replayed (each turn is a "fresh session"), but CLAUDE.md is
injected every request. State a durable fact → 💾 **remember_fact** writes it;
open the right-side panel to watch `## Known facts` grow. 🔄 does NOT wipe the
file — that is the point. No rag/web/browser here.

## Tab 4 — + Tools (stateless)

`What does our corpus say about Willow Voice's weaknesses?` → 🔧 `rag_search`.
`Open wisprflow.ai and screenshot the hero.` → 🔧 `browser_navigate` +
`browser_screenshot`. Grounded answers, but it has no memory of you or earlier
turns — ask a follow-up referencing a prior turn and it won't recall it.

## Tab 5 — + Tools + Memory (the capstone, unchanged)

Make `## Known facts` in `memory/CLAUDE.md` empty before starting.

1. `I need a competitor analysis for an AI dictation tool.` → scope question,
   no tools. Stickies: 📄 + 📘.
2. `Anchor on US enterprise legal teams; accuracy + on-device privacy; vs
   Wispr Flow and Superwhisper.` → 📄 + 📘 + 💾 remember_fact + 🔧 rag_search.
3. `What's the single strongest gap I can exploit against those two?` → uses
   persisted context, no re-scoping.

---

## Reset between demos

- **🔄 New session** (in-app button): clears the current tab's chat only.
  Does NOT touch CLAUDE.md.
- **Full reset of long-term memory:** open `memory/CLAUDE.md`, delete every
  bullet under `## Known facts` (keep the heading), reload the page.

## Sticky cheat sheet

| Icon | Kind | Meaning |
|---|---|---|
| 🧠 | LLM only | No memory, no tools. Training data only. |
| 💬 | Short-term | Full transcript replayed this turn. |
| 📄 | Memory | memory/CLAUDE.md injected into the system prompt this turn. |
| 📘 | Skill | skills/research/SKILL.md injected (capstone tab only). |
| 💾 | Persisted | remember_fact wrote a bullet to memory/CLAUDE.md. |
| 🔧 | Tool | A tool was called (Tools / capstone tabs only). |
