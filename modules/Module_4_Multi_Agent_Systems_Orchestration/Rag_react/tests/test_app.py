"""
Headless tests for app.py (Streamlit AppTest) plus the golden-answer checker.

OpenAI, Qdrant and SerpApi are replaced with fakes, so the tests are free, fast,
deterministic, and don't need the Qdrant lock. Run from the Rag_react folder:
    .venv/bin/python -m pytest tests -q
"""

import json
import os
import sys
from types import SimpleNamespace

import pytest
from streamlit.testing.v1 import AppTest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import rag_helpers  # noqa: E402
import react_agent as ra  # noqa: E402

APP = os.path.join(ROOT, "app.py")
GOLDEN = ra.load_golden()
Q1, Q3 = ra.HARD_QUESTIONS[0], ra.HARD_QUESTIONS[2]

# What the two agents actually answered for Q1 in the saved notebook run.
PLAIN_Q1 = "Uber acquired **Transplace** for **$2.25 billion**, about **12.9%** of its **$17.5 billion** 2021 revenue."
REACT_Q1 = "Uber acquired **Transplace** for **$2.3 billion**, approximately **13.2%** of its **$17.455 billion** 2021 revenue."


class FakeQdrant:
    async def query_points(self, collection_name, query, limit, **kwargs):
        chunk = SimpleNamespace(payload={"content": "Revenue $ 13,000 $ 11,139 $ 17,455",
                                         "metadata": {"company": "Uber Technologies, Inc.", "fiscal_year": 2021}})
        return SimpleNamespace(points=[chunk] * limit)


def fake_react_agent(question, verbose=True, on_step=None, **kwargs):
    if on_step:
        on_step(1, "reply", "Thought: I need the acquisition price.\nAction: search_10k\n"
                            "Action Input: Uber 2021 Transplace purchase price")
        on_step(1, "observation", "[1] (Uber Technologies, Inc. FY2021) ... consideration transferred "
                                  "for Transplace was $ 2.3 billion.")
        on_step(2, "reply", "Thought: I have everything.\nFinal Answer: " + REACT_Q1)
    return REACT_Q1


@pytest.fixture
def app(monkeypatch, tmp_path):
    monkeypatch.setenv("DEMO_DIR", str(tmp_path))  # never touch the real demo_runs/
    monkeypatch.setattr(rag_helpers, "init_rag", lambda **kwargs: None)
    monkeypatch.setattr(rag_helpers, "_qdrant", FakeQdrant())
    monkeypatch.setattr(rag_helpers, "_get_text_embeddings", lambda text: [0.0] * 768)
    monkeypatch.setattr(rag_helpers, "route_query",
                        lambda q: {"action": "10K_DOCUMENT_QUERY", "reason": "Asks about Uber's 10-K."})
    monkeypatch.setattr(rag_helpers, "_rag_formatted_response", lambda q, ctx: PLAIN_Q1)
    monkeypatch.setattr(ra, "react_agent", fake_react_agent)
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    assert not at.exception, at.exception
    return at


# ── App ───────────────────────────────────────────────────────────────────────

def test_page_loads_with_all_six_examples(app):
    assert app.title[0].value == "RAG vs ReAct"
    options = app.selectbox[0].options
    assert len(options) == 7  # "Pick one…" + 6 questions
    assert [o.split(".")[0] for o in options[1:]] == ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"]


def test_ask_button_disabled_until_there_is_a_question(app):
    assert app.button[0].proto.disabled
    app.text_area[0].input("What was Uber's 2021 revenue?").run()
    assert not app.button[0].proto.disabled


def test_picking_an_example_fills_the_question(app):
    app.selectbox[0].select(next(o for o in app.selectbox[0].options if o.startswith("Q3."))).run()
    assert app.text_area[0].value == Q3


def test_run_shows_both_agents_trace_and_golden_check(app):
    app.selectbox[0].select(next(o for o in app.selectbox[0].options if o.startswith("Q1."))).run()
    app.button[0].click().run()
    assert not app.exception, app.exception

    text = " ".join(m.value for m in app.markdown)
    assert "10K_DOCUMENT_QUERY" in text                      # plain RAG route shown
    assert "search_10k" in text and "Transplace purchase price" in text  # ReAct step shown live
    assert any("Observation" in e.label for e in app.expander)
    assert app.success[0].value == "Final answer"

    assert any("Golden answer (Q1)" in s.value for s in app.subheader)
    table = app.table[0].value
    rows = {row["Key fact"]: (row["RAG"], row["ReAct"]) for _, row in table.iterrows()}
    assert rows["Company: Transplace"] == ("✅", "✅")
    assert rows["Price: $2.3 billion"] == ("❌", "✅")         # $2.25B is not the 10-K figure
    assert rows["Share of revenue: ≈13.1–13.2%"] == ("❌", "✅")


def test_can_ask_several_questions_in_a_row(app):
    for prefix in ("Q1.", "Q3.", "Q2."):
        pick(app, prefix)
        assert not app.button[0].proto.disabled
        app.button[0].click().run()
        assert not app.exception, app.exception
        assert app.success[0].value == "Final answer"
    assert any("Golden answer (Q2)" in s.value for s in app.subheader)


def test_diagrams_how_it_works_and_path_taken(app):
    charts = app.get("graphviz_chart")
    assert len(charts) == 2  # the two "How it works" diagrams
    pick(app, "Q1.")
    app.button[0].click().run()
    dots = [c.proto.spec for c in app.get("graphviz_chart")]
    assert len(dots) == 4
    assert "10K_DOCUMENT_QUERY" in dots[2]                      # RAG path: its one route
    assert "1 · search_10k" in dots[3] and "Final answer" in dots[3]  # ReAct path: its real steps


def test_custom_question_has_no_golden_panel(app):
    app.text_area[0].input("What was Uber's 2021 revenue?").run()
    app.button[0].click().run()
    assert not app.exception, app.exception
    assert not any("Golden answer" in s.value for s in app.subheader)


# ── Demo mode (record and replay) ─────────────────────────────────────────────

def pick(app, prefix):
    app.selectbox[0].select(next(o for o in app.selectbox[0].options if o.startswith(prefix))).run()


def fail(*args, **kwargs):
    raise AssertionError("demo mode must not call any API")


def test_good_live_run_is_saved_then_replayed_without_any_api_call(app, monkeypatch, tmp_path):
    pick(app, "Q1.")
    app.button[0].click().run()
    saved = json.loads((tmp_path / "Q1.json").read_text())
    assert saved["question"] == Q1 and saved["react"]["answer"] == REACT_Q1
    assert [e[1] for e in saved["react"]["events"]] == ["reply", "observation", "reply"]

    for name in ("route_query", "_rag_formatted_response", "_get_text_embeddings", "get_internet_content"):
        monkeypatch.setattr(rag_helpers, name, fail)
    monkeypatch.setattr(ra, "react_agent", fail)
    app.toggle[0].set_value(True).run()
    assert not app.button[0].proto.disabled
    assert not any("Saved run" in m.value for m in app.markdown)  # no status line on screen
    app.button[0].click().run()
    assert not app.exception, app.exception
    text = " ".join(m.value for m in app.markdown)
    assert "search_10k" in text and "Transplace purchase price" in text
    rows = {row["Key fact"]: (row["RAG"], row["ReAct"]) for _, row in app.table[0].value.iterrows()}
    assert rows["Price: $2.3 billion"] == ("❌", "✅")


def test_run_that_misses_golden_facts_is_not_saved(app, monkeypatch, tmp_path):
    monkeypatch.setattr(ra, "react_agent", lambda q, **kw: "Transplace, for $2.25 billion (12.9%).")
    pick(app, "Q1.")
    app.button[0].click().run()
    assert not (tmp_path / "Q1.json").exists()
    assert not any("demo mode" in c.value for c in app.caption)  # nothing shown on screen
    assert not app.toast


def test_demo_mode_without_a_recording_disables_the_button(app):
    pick(app, "Q2.")
    app.toggle[0].set_value(True).run()
    assert app.button[0].proto.disabled


# ── Golden answers ────────────────────────────────────────────────────────────

def test_golden_file_covers_every_question():
    assert set(GOLDEN) == set(ra.HARD_QUESTIONS)
    for gold in GOLDEN.values():
        assert gold["answer"] and gold["key_facts"] and gold["sources"]


@pytest.mark.parametrize("answer, expected", [
    (REACT_Q1, [True, True, True]),
    (PLAIN_Q1, [True, False, False]),
    ("Uber paid $2.3B (2,300 million) for Transplace: 13.18% of revenue.", [True, True, True]),
    ("It bought Transplace for 2.25 billion dollars, 12.9% of revenue.", [True, False, False]),
])
def test_check_answer_q1(answer, expected):
    assert [passed for _, passed in ra.check_answer(answer, GOLDEN[Q1])] == expected


def test_check_answer_q5_needs_two_real_risk_factors():
    gold = GOLDEN[ra.HARD_QUESTIONS[4]]
    two = "Driver classification as employees, and COVID-19. Guardrails would help."
    one = "Driver classification as employees. Guardrails would help."
    assert all(p for _, p in ra.check_answer(two, gold))
    assert [p for _, p in ra.check_answer(one, gold)] == [False, True]


# ── Timers and token cost ─────────────────────────────────────────────────────

class FakeClient:
    """Stands in for the OpenAI client: every call uses 1,000 input (200 cached) and 100 output tokens."""
    def __init__(self):
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        usage = SimpleNamespace(prompt_tokens=1000, completion_tokens=100,
                                prompt_tokens_details=SimpleNamespace(cached_tokens=200))
        return SimpleNamespace(usage=usage, choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))])


def test_each_panel_clock_freezes_with_a_check(app):
    pick(app, "Q1.")
    app.button[0].click().run()
    heads = [m.value for m in app.markdown if "class='panel-title'" in m.value]
    assert len(heads) == 2 and all("clock-done" in h and "✓" in h for h in heads)


def test_token_cost_is_counted_per_agent(monkeypatch, tmp_path):
    client = FakeClient()
    monkeypatch.setenv("DEMO_DIR", str(tmp_path))
    monkeypatch.setattr(rag_helpers, "init_rag", lambda **kwargs: None)
    monkeypatch.setattr(rag_helpers, "_openaiclient", client)
    monkeypatch.setattr(rag_helpers, "_qdrant", FakeQdrant())
    monkeypatch.setattr(rag_helpers, "_get_text_embeddings", lambda text: [0.0] * 768)

    def route(q):
        rag_helpers._openaiclient.chat.completions.create(model="m", messages=[])
        return {"action": "10K_DOCUMENT_QUERY", "reason": "10-K."}

    def answer(q, ctx):
        rag_helpers._openaiclient.chat.completions.create(model="m", messages=[])
        return PLAIN_Q1

    def agent(question, on_step=None, **kwargs):
        for _ in range(6):
            rag_helpers._openaiclient.chat.completions.create(model="m", messages=[])
        return fake_react_agent(question, on_step=on_step)

    monkeypatch.setattr(rag_helpers, "route_query", route)
    monkeypatch.setattr(rag_helpers, "_rag_formatted_response", answer)
    monkeypatch.setattr(ra, "react_agent", agent)
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    pick(at, "Q1.")
    at.button[0].click().run()
    assert not at.exception, at.exception

    metrics = {m.label: m for m in at.metric}
    rag = next(m for label, m in metrics.items() if label.startswith("RAG cost"))
    react = next(m for label, m in metrics.items() if label.startswith("ReAct cost"))
    # per call: 800 fresh x $0.20 + 200 cached x $0.02 + 100 out x $1.20 per 1M = $0.000284
    assert "2 LLM calls" in rag.label and rag.value == "$0.0006" and rag.proto.delta == "2,200 tokens"
    assert "6 LLM calls" in react.label and react.value == "$0.0017"
    assert react.proto.delta == "6,600 tokens · 3× RAG"
