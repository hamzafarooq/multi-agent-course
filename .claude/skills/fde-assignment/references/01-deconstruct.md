# Stage 1: deconstruct the one-liner into the shape

Input: one line, the problem. Output: one page that can be approved or redirected in two
minutes. Nothing downstream is worth writing until this page is right.

**In learner mode, every heading below is a question you ask and they answer.** One at a
time. Do not propose the lesson, the cut or the capabilities; ask, wait, push back on vague
answers ("what would a stranger *see*?", "where does that come back later?", "what does a
naive build get wrong there?"), then write down what they decided in their words. If they are
stuck, show the matching paragraph of `00-how-lumina-happened.md` and ask the question again.

Read the module's `study-material/lesson.md` (or README if unauthored) first: the assignment
must exercise what that week teaches, and the capabilities table below has to point forward
at later modules and projects.

## 1. The product, in one paragraph and one line

Say what a stranger opens and uses. LUMINA: "Ask a question. Get an answer that streams in
as it is written, with citations you can click, built from a live web search and your own
uploaded documents. Ask a harder question and it decomposes it." Then the one-liner that
opens the SPEC: "...Two Express services, one MongoDB, one fixed contract, one deploy, one
benchmark that must pass."

Test: "a product a stranger can open and use", never "a notebook that calls an LLM".

## 2. The lesson

The single judgement the assignment teaches that a test cannot check. Write it as a
sentence with a failure on each side:

> Building both gears is the assignment. Knowing which a question deserves is the lesson.
> A system that runs deep machinery on "what port does mongod listen on?" is slow and
> uneconomic; one that never digs is useless on a real question.

Find it by asking: where does a naive build of this product spend money or time it should
not, and where does a cheap build fail a real user? The lesson sits between those two.
Voice agent: latency budget vs. interruption handling. RAG: recall vs. grounding. Agency:
autonomy vs. a spend gate. Every later decision (what to cut, the manual rubric row, the
bench's cleverest check) derives from this sentence.

## 3. Capabilities table

Four to six rows. Each names a capability, what it means in one line, and **where it comes
back** later in the course. A capability that returns nowhere is a candidate for the cut.

| Capability | What it means | Where it comes back |
|---|---|---|
| The loop | plan, choose tool, observe, repeat, stop; yours, bounded, honest about why it stopped | every project |
| ... | ... | ... |

## 4. Scenarios

Four or five, named A to E, each a user with a name doing one thing and seeing one
observable result (a citation resolving, a `p. 14`, a `$0.21` on `/stats`). Include:

- one scenario per capability;
- **one cheap-path scenario** that shows the lesson from the other side (LUMINA's E: "one
  search, one fetch, one sentence. Nobody decomposed anything. This is in the PRD on purpose").

## 5. Non-goals, and the cut

List what is out, each with a reason, in the "No X. Y is where you meet it" form. Then say
what you **cut** and what replaced it. LUMINA cut deck and image generation ("20 points
buying two API calls behind a cap") and gave the points to deep search. Every assignment
has this row; if you cannot name it, the scope is too wide.

## 6. The four rules that decide the grade

Reuse verbatim; they are the course's philosophy, not the assignment's:

- **Grounded or nothing.** Every claim resolves to something retrieved in that request.
- **Fail loud.** A provider exception reaches the caller as a `502`; never a plausible
  answer from a `try/catch`. Cite the Live Translate precedent (see `03-gates.md`).
- **Bounded and honest.** Caps exist; hitting one is a different outcome from finishing and
  the difference survives into the response.
- **Evidence over vibes.** Every grading number comes from a run against the deployed app,
  against thresholds declared before the first run.

Then add the assignment's own red lines (LUMINA: the server never upgrades a request to
deep; provided folders unmodified; no secret reachable from the browser).

## 7. Architecture split and stack

Default: browser talks only to a **gateway** (CORS, identity header, request id, validation,
rate limits, SSE pass-through); the gateway talks to an **agent service** that holds every
provider key and does the work; one database. Say **why two services** and **why one
database** in one paragraph each. Then the stack paragraph: taught path named and justified
("one language from the citation chip to the vector query"), and the sentence that the
contract is what is graded and a different stack is "your call to make and your risk to carry".

## 8. Provided vs built

Two lists. Provided: UI, contract, `501` skeletons, index script, bench, gold set, grader,
eval skill. Built by the student: the gateway and the agent service, named by folder.
Stage 6 turns this into the staff build list.

## 9. Grading sketch

Rows and points only, no `check` text yet: automated rows summing to about 80, two or three
manual rows summing to about 20, the bonus, the red lines. The lesson gets both an
automated row and a manual row (LUMINA: "deep search" 15 auto, "deep search quality" 5 human:
"better, not merely longer").

## Checklist before showing the page

- [ ] The lesson is one sentence with a failure on each side.
- [ ] Every capability names where it comes back; none is orphaned.
- [ ] There is a cheap-path scenario.
- [ ] Something was cut, and the points went somewhere named.
- [ ] Provided vs built is two lists, by folder.
- [ ] Points sum to 100 before bonus.

Show the page, then stop. Do not start stage 2 until the shape is approved or amended.
