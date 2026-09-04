# Aurora Voice Pipeline

The pipeline is the local text and microphone runtime:

```text
microphone -> WebRTC VAD -> STT -> AgentRouter -> LLM -> RAG and tools -> TTS
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.env .env
```

Select `PROVIDER=mock`, `PROVIDER=openai`, or `PROVIDER=groq` in `.env`. Only a live provider requires an API key.

## Verify Offline

```bash
python smoke_test.py
python -m unittest -v test_features.py
PROVIDER=mock python voice_loop.py --text
```

## Run Live

```bash
python voice_loop.py --text
python voice_loop.py
```

Text mode verifies the model, tools, RAG, routing, and guardrails without microphone uncertainty. Voice mode adds local audio capture, endpointing, STT, TTS, and stage telemetry.

## Supporting Commands

Evaluate deterministic behavior:

```bash
cd ../evals
python run_evals.py --suite all
```

Estimate capacity:

```bash
python scale_check.py --dau 1000000
```

## Modules

| File | Responsibility |
|------|----------------|
| `agent.py` | Prompt, tools, RAG tool, routing integration, and conversation state |
| `providers.py` | Mock, OpenAI, and Groq adapters |
| `router.py` | English and Spanish session routing |
| `knowledge.py` | Local SQLite FTS5 retrieval with bilingual query expansion |
| `telemetry.py` | Structured turn events, timings, and optional JSONL output |
| `voice_loop.py` | Text or microphone turn loop and TTS playback |
| `scale_check.py` | DAU, concurrency, worker, request-rate, and cost model |
| `smoke_test.py` | Basic offline end-to-end assertion |
| `test_features.py` | Focused router, RAG, telemetry, and scale tests |

Use `TTS_BACKEND=system` during rehearsal to avoid cloud TTS cost. Verify current provider pricing and limits before estimating workshop or production spend.
