# Voice-Agent Benchmark — Cascade vs. Speech-to-Speech

A reproducible benchmark that runs the **same** customer-support agent through two voice
architectures on 15 audio queries (×3 runs each) and compares them on **cost, latency,
and agentic capability**.

- **Cascade** — STT → sanitize → A2A Judge (gate) → ADK agent (+MCP tools, Mem0) → TTS.
  A pipeline of separately-owned stages on port **:8000**.
- **Speech-to-Speech (S2S)** — Gemini Live, native audio in/out, tools via function
  calling, judge as a concurrent monitor. One model on port **:8001**.

Same tools, same database, same clips — so any difference is the *architecture*, not the task.

---

## 1. What's in this folder

| File | What it is |
|:--|:--|
| `manifest.json` | **Source of truth** — the 15 queries: id, user, spoken text, expected tools + args, forbidden tools, the correct `expected_answer`, audio paths. |
| `ANSWER_KEY.md` | Human-readable answer key (generated from the manifest by `make_answer_key.py`). |
| `queries.md` | Longer prose spec / rationale for each query. |
| `audio/qNN.wav` | The benchmark clips — 16 kHz mono PCM16, one per query. `audio/source_mp3/` keeps the originals. |
| `convert_audio.py` | Regenerates the WAVs from `source_mp3/` (one-off; already done). |
| `run_bench.py` | **Phase A** — drives both voice servers, one neutral stopwatch, reseeds the DB, writes raw runs. |
| `bench_grading.py` | The grading engine (shared library) — deterministic tool scorer + the LLM judge. |
| `each_question_acc.py` | **Phase B1** — grades every run (tools + judge + WER + leak), one row per query. |
| `final_metrics.py` | **Phase B2** — rolls the graded runs into a per-arch summary table. |
| `compare.py` | **Phase B3** — cross-arch table image + charts. |
| `reproduce.py` | **One command** that runs the whole pipeline (see §4). |
| `make_answer_key.py` | Regenerates `ANSWER_KEY.md` from the manifest. |
| `requirements.txt` | All Python deps — one venv runs everything. |
| `runs/<arch>/` | Raw run records + `final_metric/` results. **Regenerable, gitignored.** |
| `comparison/` | The output images: `comparison_table.png`, `comparison_chart.png`, `comparison_accuracy.png`. |

---

## 2. What it measures

Four quality numbers (plus WER, latency, cost, leaks). The two "quality" scorers are each
split into a **precision** and a **recall** axis:

| Metric | Plain meaning | How |
|:--|:--|:--|
| **Tool accuracy** (precision) | Of the tools it *called*, how many were warranted (right tool, right args)? | deterministic |
| **Tool recall** | Of the tools it *should* call, how many fired? | deterministic |
| **Response accuracy** (precision) | Of what it *said*, how much was correct — incl. **not claiming actions it never performed**? | LLM judge |
| **Response completeness** (recall) | Of the info/actions the answer *required*, how much did it actually convey/do? | LLM judge |
| STT WER | Recognition error rate (transcript vs. spoken text). | deterministic |
| Latency | Time to first audio (responsiveness) + time to finish. | neutral stopwatch |
| Cost | USD per turn (STT+agent+TTS; judge excluded). | server usage metadata |
| Data-isolation leaks | Did a reply reveal another user's data? | deterministic |

> A tool call fires **deterministically** (objective fact); the spoken answer is graded by an
> **LLM judge** because phrasing varies ("$120" vs "one hundred twenty dollars"). The judge is
> also shown the **actual tool calls**, so a reply that *claims* an action it never performed
> (e.g. "I've logged your return" with no `action-log` call) is penalised on accuracy.

---

## 3. Setup (once)

```bash
# from this folder
python -m venv .venv
.venv/Scripts/activate            # Windows;  source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt

cp .env.example .env              # then put your OpenAI key in .env (used by the LLM judge)
```

`.env` needs:
```
OPENAI_API_KEY=sk-...
OPENAI_JUDGE_MODEL=gpt-5
```

---

## 4. Run it

### Option A — one command (recommended)

**With both servers running (see §5), this does everything** — runs both architectures,
writes the runs, grades them, rolls up metrics, and builds the charts:

```bash
python reproduce.py               # full pipeline (servers MUST be up); resumes existing runs
python reproduce.py --fresh       # clear old runs + grades, then gather & judge everything anew
python reproduce.py --grade-only  # NO servers needed — just re-grade the runs on disk + rebuild charts
```

`reproduce.py` runs, in order: `run_bench.py` (both archs) → `each_question_acc.py` (grade
both) → `final_metrics.py` (both) → `compare.py`. If a server is down it stops immediately
with a preflight message telling you exactly what to start.

### Option B — step by step (same thing, by hand)

```bash
python run_bench.py --arch both --reseed --repeats 3   # gather (needs the live stack, §5)
python each_question_acc.py --arch cascade             # grade: deterministic tools + LLM judge
python each_question_acc.py --arch s2s
python final_metrics.py --arch cascade                 # roll up per-arch summary
python final_metrics.py --arch s2s
python compare.py                                      # cross-arch table + charts
```

**Where results land:** `runs/<arch>/final_metric/` (per-question + final metrics, as
json/csv/md) and `comparison/` (the images).

---

## 5. Starting the live stack (only needed for Phase A)

Phase A drives the two capstone servers, which share one Postgres + Toolbox + A2A judge.
Start them from the capstone folders (see their own `run.sh` / README):

- **`../advance-customer-support-agent-feature-A2A-MCP-ADK_cascading/`** → cascade web on **:8000**
- **`../advance-customer-support-agent-feature-A2A-MCP-ADK-s2s/`** → s2s voice on **:8001**

Both must be up at once, along with Postgres, Toolbox (**:5000**), and the A2A judge (**:10002**),
with **masking disabled** (`MASK=false`). `run_bench.py` logs in per query and reseeds the DB
itself; you don't touch the DB by hand.

---

## 6. Reproducibility — what's guaranteed, what isn't

**Guaranteed / controlled:**
- **Deterministic database.** `seed.sql` is fixed data (prices, statuses, ids); `run_bench.py`
  reseeds to that baseline before each architecture's pass, so both see an identical DB.
- **No memory contamination.** The servers only *read* memory (`search_memory`); they never
  *write* it during a run, and the Mem0 store is empty for the benchmark users — so every run
  starts from the same blank slate. (Start with an empty Mem0 for a clean reproduction.)
- **Fair, unbiased timing.** One neutral stopwatch times both archs identically (start = clip
  finished sending; stop = response done). The guardrail (judge) and the cascade's 1.5 s settle
  wait are **excluded** from latency and cost, so the numbers are pure STT+agent+TTS.
- **Same grader for both.** Tools are scored by identical deterministic rules; responses by one
  LLM judge with one prompt. Blocked turns score 0 on both sides.

**Inherently not bit-identical:**
- The agents and the LLM judge are **sampled models**, so exact text and scores vary run-to-run.
  We handle this by running **each query 3×** and reporting **mean ± std** — so the *conclusions*
  reproduce even though individual numbers wobble. With only 15 queries × 3, don't over-read a
  small gap; check the ± first.

---

## 7. The dataset & answer key

- Each `source_text` in the manifest is the **WER ground truth** for that clip — don't edit it.
- Each `expected_answer` is the single correct reply the judge grades against.
- Edit the manifest, then run `python make_answer_key.py` to refresh `ANSWER_KEY.md`.
- To rebuild the WAVs from the MP3 originals: `python convert_audio.py`.

---

## 8. Hop definition

**Hops = dependent data/action tool calls on the critical path**, excluding the always-on
`search_memory`.

- **1 hop** — one lookup (even if it needs multi-record math, like summing a total).
- **2 hops** — a dependent second call (an action that needs an id discovered by the first call,
  e.g. "cancel my *most recent* order" = list orders → find newest id → log the cancellation).
