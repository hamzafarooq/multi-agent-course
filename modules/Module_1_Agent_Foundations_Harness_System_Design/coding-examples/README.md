# Module 1 — Coding Examples

Hands-on notebooks for **Module 1: The Agent Loop, ReAct & the Harness**. They take you from
building a ReAct agent by hand to using two real agent frameworks, so you can see what the
loop looks like from scratch and what a framework adds on top.

## What's here

| Notebook | What it covers | Notes |
|----------|----------------|-------|
| `AgentPro Starter Code.ipynb` | Quick-start for [**AgentPro**](https://github.com/traversaal-ai/AgentPro), Traversaal.ai's open-source agent framework: clone, install, configure keys, run. | The same ideas, now via a framework. |
| `Agent Pro ReAct.ipynb` | A ReAct agent built from scratch — a `Tool` base class, an Ares internet-search tool, and the reason → act → observe loop wired up by hand. | **Start here** for the from-scratch loop. |
| `Smol Agents Updated.ipynb` | Intro to Hugging Face [**smolagents**](https://github.com/huggingface/smolagents) — the `CodeAgent` (acts by writing & running code) and a JSON agent. | A second framework, with a code-execution agent. |

## Suggested order

1. **`AgentPro Starter Code.ipynb`** — see the same pattern through a production framework.
2. **`Agent Pro ReAct.ipynb`** — build the loop yourself first; this is the core of the module.
3. **`Smol Agents Updated.ipynb`** — a second framework with a code-execution agent.

## Setup

Each notebook installs its own dependencies in the first cell (`!pip install ...`), so they
run as-is in **Google Colab** (preferred) or locally in Jupyter.

You'll need API keys depending on the notebook:

- **OpenAI** API key — used by the AgentPro / ReAct notebooks (`OPENAI_API_KEY`).
- **Ares** API key from [Traversaal](https://api.traversaal.ai/) — used by the internet-search tool.

In Colab, set keys via the 🔑 *Secrets* panel (`userdata.get('OPENAI_API_KEY')`); locally,
set them as environment variables. Don't hard-code keys into the notebooks.
