# ReAct vs Router, in VS Code

This folder has the same code as the two Module 3 Colab notebooks, as Python files you can run on your own machine after cloning this repo. They are class material and practice, not an assignment.

| Folder | Same as | What it does |
|---|---|---|
| [`1_python/`](1_python/) | [Notebook 1](../ReAct_vs_Router_1_Python.ipynb) | Three tools, a router and a ReAct loop in plain Python, both run on the same questions, then the 12-question eval |
| [`2_adk/`](2_adk/) | [Notebook 2](../ReAct_vs_Router_2_ADK.ipynb) | The same two designs in Google ADK 2.0 (an `Agent` and a `Workflow`) and the same eval |

Each file is split into cells by `# %%` lines. In VS Code, click **Run Cell** above a cell to run it on its own and see the output beside the code, the way a notebook works. Or run the whole file from a terminal.

## Setup (once)

You need Python 3.12 (3.11 works too) and two keys: an OpenAI key ([platform.openai.com](https://platform.openai.com)) and a SerpApi key ([serpapi.com](https://serpapi.com), free tier) for web search.

1. Clone the repo. In VS Code, open the Command Palette and run **Git: Clone** with `https://github.com/hamzafarooq/multi-agent-course`, then open the folder `FDE-03-assignments/ReAct_vs_Router_py`.
2. Copy `.env.example` to `.env` in this folder and paste your two keys into it. `.env` is git-ignored, so your keys stay on your machine.
3. Install the Python and Jupyter extensions in VS Code if you don't have them. **Run Cell** needs both.

Each part gets its own virtual environment, because ADK's packages and Phoenix's packages clash when they share one.

## Part 1: from scratch in Python

```bash
cd 1_python
python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python router_vs_react.py
```

Phoenix starts inside the script and prints its address (http://localhost:6006). When you run the whole file, it waits at the end so you can open the traces; press Enter to stop it. In VS Code, pick `.venv` as the interpreter (bottom right) before you click **Run Cell**.

## Part 2: with ADK

```bash
cd 2_adk
python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python router_vs_react_adk.py
```

To trace part 2 in Phoenix, start Phoenix first in a second terminal, then run the script. Use either of these:

```bash
uvx --from arize-phoenix phoenix serve            # if you have uv
../1_python/.venv/bin/phoenix serve               # or reuse part 1's environment
```

If Phoenix isn't running, the script says so and carries on without tracing.

## What's different from Colab

- Keys come from `.env` instead of Colab's Secrets panel.
- Installs come from `requirements.txt` instead of `!pip` cells.
- In part 2, `go(...)` replaces the notebook's top-level `await`, so the same line works in a plain script and in VS Code's interactive window.
- The animations and Phoenix inside the page are Colab-only. Here you open Phoenix in your browser.
- The full run makes about 60 model calls in part 1 and about 70 in part 2, mostly in the eval at the end. Run cell by cell if you only want the first sections.
