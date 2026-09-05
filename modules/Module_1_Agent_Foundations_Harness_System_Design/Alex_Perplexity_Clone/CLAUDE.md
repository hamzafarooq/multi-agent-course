# Alex — Perplexity-style reference app (Module 1)

## What this module is

A working four-level assistant called **Alex** — the world's simplest agent, and
at Level 1 not an agent at all. The model is identical at every level; what gets
switched on is the **harness** around it: history, then tool calling and the loop,
then retrieval. Unlike most of the course, this folder *does* contain a finished
app — the hands-on part is taking it apart, changing it, and seeing what breaks.

The first thesis the app is built to prove: **the harness, not the model, is what
makes something an agent.** Level 3's `run_tool_loop` is the whole difference.

The second: **RAG is string concatenation with a search step in front of it.** There is no special "retrieval channel" to a model.
Retrieved text is pasted into the prompt like any other text. The debug panel
exists so nobody has to take that on faith.

## Folder map

```
.claude/launch.json     VSCode launch config for the backend
backend/
  main.py                 FastAPI app: SSE streaming, the four levels, prompt assembly
  rag.py                  loads the prebuilt index, embeds the question, retrieves
  chunking.py             reads the PDF and data/, cuts overlapping 900-char windows
  embeddings.py           the two providers: openai over the API, local via nomic
  build_index.py          the offline index build. Run it when documents change
  gate.py                 the password gate, shared with the Search Lab
  tools.py                the web_search tool + Tavily client
frontend/
  index.html              markup, including the debug panel and RAG walkthrough modals
  app.js                  chat, SSE client, markdown renderer, debug panel, RAG walkthrough
  styles.css              all styling; light theme pinned, tokens at the top
data/
  *.md                    fictional ACME program documents
index/                    the built index: chunk text + one vector each. Gitignored
Project-Management-...pdf  the general project management reference
api/
  index.py                Vercel entrypoint. Mounts the Search Lab at /lab
search-lab/               keyword vs semantic retrieval, side by side. Its own app
```

## The four levels

Each level is one function in `main.py`, and they share one streaming helper:

| Level | Function | Sends | Tools |
|---|---|---|---|
| 1 | `run_level1` | current message only | none |
| 2 | `run_level2` | history + current message | none |
| 3 | `run_level3` | history + current message | `web_search` |
| 4 | `run_level4` | system prompt with excerpts + history + current | `web_search` |

Levels 3 and 4 share `run_tool_loop`. **Keep them cumulative** — Level 4 having
the web search tool is deliberate and matches the course README. If you add a
level, it must strictly add to the one before it.

## Conventions that matter here

**Everything the debug panel shows must be true.** The panel renders the actual
payload, and `/api/rag/score` calls the same `store.search()` the live chat uses.
If you change retrieval, the walkthrough follows automatically. Never let the
teaching surface drift from real behaviour — a demo that lies is worse than no
demo.

**Prompt engineering and context engineering stay visibly separate.** The system
prompt is assembled from labelled parts (`PERSONA_PART`, grounding rules,
retrieved excerpts), each tagged with its `kind`. That labelling is the lesson,
not decoration. New system content should be added as a labelled part, not
concatenated into an existing one.

**Citation style distinguishes sources.** Bracket `[1]` means a document,
markdown links mean the web. The prompt enforces it and the frontend renders
both. Do not blur them.

**No CDNs, no external runtime dependencies in the frontend.** The markdown
renderer is hand-rolled for this reason: the demo must work on a conference
network, or with no network at all. Google Fonts is the only external request,
and it degrades gracefully.

**Light theme is pinned** (`color-scheme: light`), because it is presented on
projectors in bright rooms. Do not reintroduce a `prefers-color-scheme` block.

## Retrieval details worth knowing before you change them

- `CHUNK_SIZE = 900`, `CHUNK_OVERLAP = 150`, `TOP_K = 8`, `MIN_SCORE = 0.08`.
- Each chunk is vectorised as `"{document title}\n{text}"`. Without that prefix,
  the 740-chunk PDF swamped the short ACME documents, which never repeat their
  own subject in the body.
- The disclaimer blockquote is stripped from `.md` files before indexing. It is
  identical across all five, so indexing it made every document's header chunk
  look alike and outrank real content.
- Markdown is split on `##` headings, so section structure decides chunking. If
  a document retrieves badly, look at its headings before touching the code.
- Level 4 follow-ups prepend the last two user turns to the retrieval query,
  because "what about the third one?" has nothing to match on by itself.

`MIN_SCORE` is a floor, not a relevance filter — an off-topic question can still
score 0.36. The real guard is that only excerpts the answer actually **cites**
are shown as sources.

## Running it

```bash
cd backend
uvicorn main:app --reload --port 8000
```

The index loads on a background thread at startup, so boot is instant.
`GET /api/health` reports readiness and document count.

It has to exist first. `index/` is gitignored (12MB of vectors), so a fresh
clone needs `python backend/build_index.py` once — chunking and embedding happen
there, offline, never at request time. That is why the deployed function needs
no PDF parser and no model weights.

Requires `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` in `.env` — Anthropic answers,
OpenAI embeds. `TAVILY_API_KEY` is optional; without it the web search returns
mock results and the UI labels them as mocked. `APP_PASSWORD` is unset locally
on purpose: the gate is for the deployment, and nobody should be typing a
password while building.

## When you change things

- Bump the `?v=` query strings in `index.html` for `app.js` and `styles.css`.
  Static files are served with `no-store`, but the version bump makes cache
  problems impossible to blame.
- Add documents by dropping `.md` or `.txt` into `data/`. Titles come from each
  file's `# H1`, not the filename. Then re-run `python backend/build_index.py` —
  a restart alone does nothing, because the app only ever loads `index/`.
- Sample data must stay clearly fictional and labelled. It describes a made-up
  customer and program; do not make it resemble a real contract or real people.

## What this module deliberately does not do

No reranker, no query rewriting, no hybrid scoring, no evaluation harness,
fixed-size chunking, and a numpy matrix instead of a vector database. These are
teaching choices, not oversights — the README says so plainly, and the gap
between this and production is the discussion the module is meant to start. Do
not silently "fix" them.

Retrieval itself is no longer on that list. It was TF-IDF, and is now embeddings
via `embeddings.py`; `search-lab/` is where the difference between the two is
demonstrated rather than asserted.
