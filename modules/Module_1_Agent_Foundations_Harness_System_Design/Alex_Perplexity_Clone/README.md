# Alex — the world's simplest agent

> A harness wrapped around one ordinary LLM call. Turn the harness on one layer
> at a time and watch a language model become an agent.

> **Module 1 reference app.** This is the finished Perplexity-style clone the
> [LUMINA PRD](../Assignment_1_Lumina/PRD.md) asks you to build your own version
> of. Clone it, run it locally, read the trace panel, then change it. Hosted copy:
> **https://lumina-perplexity-clone.vercel.app** (password-gated; the password is
> shared in the live session because live API keys sit behind it).
>
> Originally built as the Enterprise RAG module of a partner cohort; the text below
> keeps that framing where it still teaches.


Meet **Alex**, the world's simplest agent - and at Level 1, not an agent at all.

The model never changes. Same call, same weights, every level. What changes is the
**harness** wrapped around it: the conversation history, the tools, the loop that
runs them, and the retrieval step that decides what the model is allowed to see.
Strip the harness away and you are left with a chatbot.

`LLM only  ->  + history  ->  + tool calling and the loop  ->  + retrieval`

Levels 1 and 2 are a chatbot. **Level 3 is where it becomes an agent**: the model
decides for itself to call a tool, reads the result, and goes round again until it
stops asking. That is `run_tool_loop` in `backend/main.py` - about forty lines, and
the entire difference between a language model and an agent.

The second lesson is that RAG is **string concatenation with a search step in front
of it**. This app is built so you can prove both to yourself rather than take them
on faith.

## The four levels

| Level | What gets turned on | What you should notice |
|---|---|---|
| **1** | LLM only | Ask a question, then ask a follow-up. It has no idea what you just said. The payload really does contain one message. |
| **2** | + conversation history | Follow-ups work now. Nothing was "remembered" — the whole transcript is re-sent every single turn, and it grows. |
| **3** | + web search tool | Alex decides for itself whether it needs to search. The result comes back as **text**, appended to the same message list, and the whole thing is sent again. |
| **4** | + retrieval (RAG) | Excerpts from your documents are pasted into the system prompt. Alex answers from them first and only searches the web when they fall short. |

The levels are strictly cumulative. Level 4 still has Level 3's `web_search`
tool. Bracket citations like `[1]` mean the answer came from a document;
markdown links mean it came from the web.

## The two things to actually show people

**The debug panel** (sidebar checkbox) is the teaching surface, not a developer
tool. It shows the literal payload sent to the model for every turn of the
session, rendered as a conversation, with each message tagged:

- `appended this turn` — the message you just typed
- `re-sent from earlier turns` — history, replayed because the model forgot it
- `produced during this turn` — a tool request and its result
- `sent on every call` — the system prompt

Ask the same two questions at Level 1 and at Level 2, then compare the payloads
side by side. Watch the character count go from 69 to 242 to 8,000+. That is the
entire lesson about context, and nobody has to believe you — it is on screen.

The panel also splits the system prompt into its two halves:

| | What it is | Who wrote it |
|---|---|---|
| **Prompt engineering** | Alex's persona, the grounding rules, the citation rules | Us, by hand, identical on every call |
| **Context engineering** | The retrieved excerpts | Nobody — looked up per question and pasted in |

**"How RAG works"** (button at Level 4) walks through chunking, weighting, and
retrieval on the real index. Every number in it is read live from the running
system:

1. Pick a document.
2. See it cut into chunks, with the overlapping text between them highlighted.
3. See each chunk turned into the numbers a model actually compares — the
   vector it was embedded into.
4. Type a question and watch all ~780 chunks get scored and ranked, with the
   losers labelled `cut by top-k` or `below threshold`.

## The knowledge base

Two kinds of source, indexed together:

- `Project-Management-2nd-Edition-1729807212.pdf` — a general project management
  reference. Long prose, 740 chunks, cut into overlapping windows.
- `data/*.md` — a fictional **ACME Aerospace Systems** program: master services
  agreement, statement of work, two sets of meeting notes, and a risk register.
  Short, structured, one chunk per section.

> The ACME documents are **invented sample data**, labelled as such in every
> file. They exist so the demo answers questions a program team would really
> ask — *"what are the payment terms?"*, *"what is the highest risk right
> now?"* — instead of textbook definitions.

They interlock on purpose. A late deliverable shows up as an action item in the
kickoff notes, an escalation in the status review, and risk R-02 in the
register, so follow-up questions have to chain across documents.

Drop any `.md` or `.txt` file into `data/`, re-run `python backend/build_index.py`,
and it joins the index.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` in `.env` — Anthropic answers,
OpenAI embeds. `TAVILY_API_KEY` is optional; without it, web search returns
clearly-labelled mock results and the UI says so.

Then build the retrieval index, once:

```bash
python backend/build_index.py
```

`index/` is gitignored — 12MB of vectors that change whenever the documents do —
so a fresh clone starts without one and Level 4 has nothing to retrieve from.
The app says as much on startup, naming this exact command. Re-run it whenever
`data/` or the PDF changes.

To build it without an OpenAI key, use the offline model instead — it needs
`pip install -r search-lab/requirements.txt` for torch, and the app must then
also run with `EMBEDDING_PROVIDER=local`. An index is only searchable by the
model that built it — different models produce unrelated vectors, so `rag.py`
refuses the mismatch rather than returning quiet nonsense:

```bash
EMBEDDING_PROVIDER=local python backend/build_index.py
```

## Run

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Open http://localhost:8000.

The document index builds on a background thread at startup, so the app is
usable immediately. `GET /api/health` reports when it is ready.

## Deployed

| | |
|---|---|
| Assistant | https://lumina-perplexity-clone.vercel.app |
| Search Lab | https://lumina-perplexity-clone.vercel.app/lab |

Both sit behind one password, because live Anthropic, OpenAI and Tavily keys sit
behind them and an open URL is an open invitation to spend someone else's
credits. `APP_PASSWORD` mints a signed cookie; without it every `/api/` route
returns 401, including the chat stream. One login covers both apps.

The gate is deliberately off locally — `APP_PASSWORD` is unset in `.env`, so
nothing asks you for a password while you are building.

```bash
vercel --prod
```

## Try these

| Level | Ask this | Then this |
|---|---|---|
| 1 | What is the capital of France? | What city did I just ask about? |
| 2 | (same two) | Notice the second one works now — and why |
| 3 | What's happening in Boston this weekend? | Check whether the pill says **live** or **mocked** |
| 4 | What are the payment terms in the ACME contract? | What is the highest risk on the Sentinel program? |
| 4 | What is the weather right now? | Documents can't answer, so it searches the web |
| 4 | Who won the most recent Super Bowl? | Same fallback, different citation style |

## Also in this module: Search Lab

[`search-lab/`](search-lab/) is a frontend for
[`basic_keyword_semantic_search.py`](basic_keyword_semantic_search.py): keyword
retrieval and semantic retrieval, running side by side on the same documents for
the same question.

```bash
uvicorn --app-dir search-lab app:app --port 8010
```

Its own app, its own port. In the deployment it is served at
[`/lab`](https://lumina-perplexity-clone.vercel.app/lab) rather than as a second
Vercel project, because a project's bundle cannot reach above its root and the
lab imports this module's embeddings provider. It is deployable at all because
`EMBEDDING_PROVIDER` defaults to `openai`; the offline nomic model drags in
~525MB of torch, far past the function size limit. Locally either works.

Ask it `feline hunting rodents` and keyword search returns **nothing** while
nomic-embed-text finds the right document instantly. Ask `cat that chases mouse`
and keyword search returns the *wrong* document confidently. That gap is the
argument for everything below.

## What is deliberately naive

Worth saying out loud when you teach this, because the gap between this and a
production system is the interesting part:

- **No reranker.** Top-k by cosine similarity against one threshold, nothing
  more. No cross-encoder, no query rewriting, no hybrid keyword-plus-vector
  scoring — all three are standard in production and all three are absent.
- **No evaluation harness.** Faithfulness, coverage, and hallucination rates
  are exactly what Week 6 is about.
- **The vector store is a numpy matrix**, loaded from a JSON file and searched
  by one dot product against all 780 chunks. No Pinecone, no Chroma, no FAISS —
  on purpose, so nothing is hidden behind a service. It is also why the corpus
  size is the limit: this approach stops being reasonable a couple of orders of
  magnitude from here.
- **Chunking is fixed-size**, ~900 characters with 150 of overlap, blind to
  headings, tables and sentence boundaries. A clause split down the middle is
  retrieved as two half-answers.

## Project structure

```
backend/
  main.py         FastAPI app, SSE streaming, the four levels, prompt assembly
  rag.py          loads the prebuilt index, embeds the question, retrieves
  chunking.py     reads the PDF and data/, cuts them into overlapping windows
  embeddings.py   the two providers: openai over the API, local via nomic
  build_index.py  the offline build. Run it whenever the documents change
  gate.py         the password gate, shared with the Search Lab
  tools.py        the web_search tool and its Tavily client
frontend/
  index.html / styles.css / app.js   chat UI, debug panel, RAG walkthrough
data/
  *.md            the fictional ACME program documents
index/            the built index: chunk text plus one vector each. Gitignored
api/
  index.py        the Vercel entrypoint. Mounts the Search Lab at /lab
search-lab/
  app.py          keyword vs semantic retrieval, side by side
  frontend/       its UI
```
