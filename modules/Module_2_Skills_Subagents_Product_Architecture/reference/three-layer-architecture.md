# Reference — The Three-Layer Architecture

<!-- INSTRUCTOR: Background for what the Sprint Zero build agents actually produce.
     Source: 3_Three_layer_architecture. Supporting context, not a core lesson concept. -->

Every modern AI product runs on three layers. The Sprint Zero build agents (backend +
frontend) target the first two; the AI backend is where Claude itself lives.

## Layer 1 — Frontend (what the user experiences)
Everything the user sees and touches: buttons, forms, dashboards, loading states. Runs in the
browser or mobile app.
- **React** — compose pages from reusable components (LEGO blocks).
- **Next.js** — wraps React; adds routing, performance, server-side rendering. Most new products start here.
- **Tailwind CSS** — utility classes for styling without custom CSS.
- **Vercel** — one-command deploys; push to GitHub and it's live.

Decisions that live here: page load target (<2s), behavior when the API is slow (loading
states are product decisions), mobile/responsive from day one.

## Layer 2 — Backend (what happens when someone clicks)
The rulebook, running on a server. Validates requests, checks permissions, reads/writes the
database, sends emails, processes payments, returns a response. Each feature ≈ one endpoint.
- **Node.js** — JavaScript on the server; great for real-time.
- **Python** — default for AI and data-heavy work.
- **Express** — the common Node API framework.
- **Supabase** — managed DB + auth + file storage + real-time sync; most MVPs need nothing else.

Decisions that live here: what data we store (tables map to the data model), rate limits and
abuse handling, what happens when a third-party API goes down (retries, fallbacks).

## Layer 3 — AI Backend (where intelligence lives)
The new layer. Connect to a model like Claude, process text/images, run semantic search. It's
not magic — it's an API call with a prompt.
- **Claude API** — text in, text or structured data out; the model reasons, your backend manages the call.
- **Embeddings** — mathematical representations of text for semantic similarity / search.
- **RAG (Retrieval-Augmented Generation)** — give the model your data before it answers (Module 3).

Decisions that live here: which model (Opus thinks deeply, Sonnet executes, Haiku moves fast —
cost/quality tradeoffs), what goes in the prompt (prompt = product design), what data the model sees.

## The full picture

    User → [FRONTEND] React/Next.js → [BACKEND] Node + Express → [DATABASE] Supabase
         → [AI BACKEND] Claude API → [RESPONSE] JSON → frontend renders

Tooling underneath it all: **VS Code** (where code is written, and where Claude Code runs),
**GitHub** (storage, review, history), **CI/CD** (ships automatically on merge).
