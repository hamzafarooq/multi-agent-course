# How LUMINA happened: the trail from one line to 8,600 words

Premise: problem solving with AI is as good as the spec you write. A coding agent builds what
you can state precisely and nothing you cannot. The one-liner was "build a Perplexity clone." Below is what was asked at each move, what the
answer was, and what that answer forced. Read it as a worked example of the six moves, not
as a template to copy: your product will give different answers to the same questions.

## Move 1: deconstruct

The problem is given and stays one line. The expansion comes from a fixed set of questions put
to it in order; none is "what should we build", all are "what does building *this* force".

**What does a stranger open and use?** Ask a question, get a streamed cited answer from the
web and your own documents; it remembers you. The bar is "a product a stranger can open and
use", and the SPEC says so in its first section: learners ship the loop "as a product, not a
notebook".

**What does the module teach, and does the product exercise it?** Week 1 is the agentic loop
and the harness. Perplexity is the loop seen from the outside: a query goes in, the system
decides what to search, reads, answers with proof. Then: where does each capability come back
later in the course? That produced the table (loop -> every project; search -> ARGUS, EPYHIA;
memory -> Module 2, VOXA; RAG -> ARGUS extends the exact contract). A capability with nothing
in that column was a cut candidate.

**Where does a naive build fail on both sides?** This question is what produces the lesson: run the heavy machinery on every question and
it is slow and uneconomic; never dig and it is useless on a real question. "Knowing which gear
a question deserves" became the sentence everything else derived from. Test yourself: can you
state your lesson with a failure on each side? If it has only one side, it is a feature.

**What got cut?** The first draft had slide-deck and image generation, twenty points. Asked
"what loop skill do these buy?" the answer was: two API calls behind a spend cap, teaching the
async pattern (which document ingestion already teaches) and the spend gate (which deep search
now carries). They were cut and the twenty points went to deep search: fifteen automated, five
to a human asking "is the deep answer better or just longer?" The cheap-gear scenario ("what
port does mongod listen on?", one search, one sentence, nobody decomposed anything) was added
to the PRD on purpose to show the lesson from the other side.

**Why two services, why one database?** Browser-facing concerns are not AI concerns, and keys
must never live where the browser can reach; so a gateway and an agent service. Atlas Vector
Search puts the embedding next to the chunk text and its page number, so a citation is one
document read, not a join across two stores; so one database. Each got one paragraph of "why",
because a rule without a why is what students correctly resent.

## Move 2: contract

The UI was going to be provided, so the question was literal: what will it call? Every route
was written as a jsonc line with its status code. The SSE event order came from the UI's
needs: `sources` before the first `token` so chips can render as text arrives; `plan` before
any retrieval because a plan emitted after the fetches is a rationalisation. Both later became
bench checks. Each ordering rule that encodes the lesson became the bench's sharpest assertion.

`done` had to carry every number the SLA would measure (`latencyMs`, `ttftMs`, `tokens`,
`costUsd`, `terminated`) plus `depth`, because without depth nobody can tell an expensive
legitimate deep run from a quick run that ran away. `/health` was first written with an enum
for the vector store; that was the one real stack lock in the whole contract, and it was
widened to a free string when a student asked whether MERN was graded or taught.

## Move 3: numbers

Numbers were chosen from tolerance and economics, with a reason each: TTFT p95 2.5 s is "the
'it's thinking' window a user tolerates"; `202` in under 300 ms "proves work is off the
request path". The row that measures the lesson directly is `min_deep_source_ratio: 2.0`, the
same question run at both depths, deep must surface twice the distinct sources: "deep that
reads no more than quick is only slower, and this is the number that catches it." Latency and
cost are reported per gear, never blended, because a blended average is how a slow quick
search hides behind a fast deep one.

## Move 4: evals and quality assurance

The question was: what *measures* each number? Latency the bench times client-side through the
gateway, per gear. Grounding is arithmetic: re-fetch the page, normalize, require about twelve
consecutive matching tokens; a publisher that blocks the bench makes a citation unverifiable,
not wrong, and those are excluded and reported. Recall needs a gold set, so one was built: 39
questions over four CC-BY documents, two rendered to PDF so the page numbers cannot move, with a
validator that re-checks every anchor. The lesson got its own instrument, the same question run
through both gears. Quality assurance sits beside the bench as case law: `quality/rules.json`,
where every rule cites the incident that created it, and `check.mjs`, which applies the rules to
the run logs. The six gates run in order, each one blocking, ending at the one gate that cannot
be automated: a person reads one successful and one failing trajectory end to end. The rule "a
judge model may report, never block" came from a ported precedent where three detectors returned
confident wrong answers; the fix was to stop detecting and assert arithmetic.

Two traps were found only by running the grader against a stub backend. P1 wants a failing
trajectory kept; A2 fails any run not terminated `done`; the fix was `runs/failing/`, read by
the report builder and not by the trajectory rules. `mustNotCallTools` is global but
`plan_research` is forbidden only to quick runs; the fix was to leave the list empty, say why in
the JSON, and assert the conditional version in the bench. Eight bugs in total, two of which
would have failed every correct submission. The grader did not work until it was run.

## Move 5: documents

The first LUMINA was one 14,000-word PRD. A student said it was too prescriptive and too
verbose for a human, and asked to see the UI first, then the contract, then the non-functional
half. The density was deliberate, so a coding agent would not skip a requirement, which is
exactly why it had to be split rather than trimmed: one document cannot be a fifteen-minute
brief and an exhaustive machine spec. So `PRD.md` for humans with no digits, `SPEC.md` for
agents with every status code once, `AGENTS.md` as the always-loaded non-negotiables,
`TECHNICAL.md` for the build, `README.md` as a front door under 800 words, `DESIGN.template.md`
for the part that is genuinely the student's. The ladder came out 781 -> 1,433 -> 4,349 ->
1,357 -> 8,600 words, and a student never has to open the last one.

The Live Translate story went under "Fail loud" because a previous cohort's translator served
English for weeks behind a `try/except` that returned the input untouched. Rules with a real
incident behind them get followed; rules without one are preferences.

## Move 6: scaffold

The PRD listed the UI, contract, skeletons, bench, gold set and grader as "provided", and none
existed; a student following the README hit six missing directories. They were built in one
pass, `501` skeletons first so the README's step one ("run it, click everything") became true.
The submission became one URL whose `/evals` page proves itself, so that no number on the page
could come from anywhere but a run against the deployed app.

## What to take from this

- The detail is downstream of the lesson. Find the lesson first.
- Ask "where does this come back?" of every capability; cut what returns nowhere.
- Write the contract as if the UI existed. Order rules are your best gates.
- Choose numbers from the why column, before the first run, and put them in one file.
- Two readers, six documents, numbers first, README last.
- Run the grader against a stub before anyone sees it. It will be wrong.
