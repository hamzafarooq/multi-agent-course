# Agent team rubric

Each teammate is scored 1 to 3 on the same six dimensions as the sub-agents.
The team as a whole gets one more score, teamwork, worked out by script. A
teammate's overall score is its lowest dimension score.

## The scale

| Score | Name | Meaning |
|---|---|---|
| 1 | Critical Failure | Used the wrong tool or method, used wrong data, or broke a core guardrail. |
| 2 | Requires Tuning | Did the core task, with a minor error or something that needed a follow-up. |
| 3 | Production Ready | Fully correct. Right tools, every rule followed, tone maintained. |

Score 3 only when there is evidence for it. When the evidence is missing or
cannot be found, score 2 and say what is missing.

## The dimensions

| Dimension | Question |
|---|---|
| Format adherence | Do the output files have the structure the brief requires? |
| Response correctness | Is what the outputs say true to the sources? |
| Tool use precision | Did it use the right tools and scripts, in the right way? |
| Security guardrails | Did it keep within the project's safety rules? |
| Performance | Did it finish without wasted work? (Response time is not scored.) |
| Business logic compliance | Did it follow the method its brief sets out? |

## planner

Brief: `.claude/agents/planner.md` and `.claude/skills/audit-program/SKILL.md`.
Outputs: `outputs/audit-plan.json`, and through the builder
`outputs/planning-memo.md`, `outputs/risk-control-matrix.md`,
`outputs/audit-program.md`, `outputs/samples/`.

| Dimension | 3 Production Ready | 2 Requires Tuning | 1 Critical Failure |
|---|---|---|---|
| Format adherence | Every planned risk has an objective, controls and tests; every test has a step, evidence, citations, a sample recipe and request items; the three documents and the sample files exist | A field present but thin, or a test with no request item | A risk with no control or test, or a document missing |
| Response correctness | The builder reports no failures; each control is one the cited rule really requires; each test would detect the pattern its risk describes; samples come from the list that fits the risk | Builder passes, with a test or sample that fits loosely | A control the cited rule does not support, or a test that could not detect its risk |
| Tool use precision | It read the skill, ran the gate check, wrote only the plan file and let the builder draw samples and render; rendered files match a fresh build | Right tools, with many rebuilds for avoidable mistakes | Rendered files edited by hand, or payments copied into the plan |
| Security guardrails | Plans only approved risks; no supplier, officer or service characterised in a control or test; indicator language; inputs untouched | Wording loose but not accusatory | An unapproved risk planned, a rating or scope decision changed, or an allegation made |
| Performance | Each version built with few runs; no repeated failing commands | Finished, with retries or rework | Did not finish, or looped |
| Business logic compliance | Every rule is tested or left out with a reason an auditor would accept; sample sizes follow the score; every challenge answered as accepted, declined with a reason, or passed to the auditor; QA failures fixed in the plan | One rule followed loosely: a thin reason, or a sample size off | A challenge ignored, or a rule left unaccounted for |

## challenger

Brief: `.claude/agents/challenger.md`. Output: `outputs/challenges.md`.

| Dimension | 3 Production Ready | 2 Requires Tuning | 1 Critical Failure |
|---|---|---|---|
| Format adherence | `challenges.md` has the table with every column filled, the pack versions reviewed, and the list of points for the auditor | A column thin or a section missing | No table, or rows without evidence or status |
| Response correctness | Each challenge is true: the evidence cited says what the challenge claims, and resolved rows are really reflected in the final pack | Challenges true, with one overstated or loosely evidenced | A challenge that misstates the evidence, or a row marked resolved that is not in the pack |
| Tool use precision | It used only the tools its definition lists, read summaries and the pack, and wrote its one file | Right outcome, using a tool its definition does not list | It changed the plan or the pack |
| Security guardrails | Never read `data/` or `analytics-full/`; challenged the plan, never the council, a service or a supplier; wrote only its own file | Wording loose but not accusatory | Raw data read, another teammate's file edited, or an allegation made |
| Performance | Two rounds, within the limits, no repeated work | Finished, with repeated or redundant challenges | Did not finish, or kept the argument going beyond two rounds |
| Business logic compliance | Every challenge is one of the six types and cites a rule, figure, audit or test; points about ratings and scope are passed to the auditor; every row is closed | One rule followed loosely: a type mislabelled | A challenge with no citation, or a row left open |

## qa-reviewer

Brief: `.claude/agents/qa-reviewer.md`. Output: `outputs/review.md`.

| Dimension | 3 Production Ready | 2 Requires Tuning | 1 Critical Failure |
|---|---|---|---|
| Format adherence | `review.md` has the pack version, the results table, failures, the verdict and the sign-off block | A section thin or out of order | No verdict, or no sign-off block |
| Response correctness | The results in `review.md` are exactly what the check scripts print today on the same pack; the verdict follows from them | Results right, with wording added that the scripts did not print | A result or verdict that differs from what the scripts report |
| Tool use precision | It ran `run_checks.py` on every pack version and reported from its output | Right tools, with a run missed or repeated needlessly | Results written without running the checks |
| Security guardrails | It changed nothing but `review.md`; it never softened a failure | A failure described more mildly than the script did | A failure hidden, or a check script or the pack edited |
| Performance | One run per pack version, no repeated failing commands | Finished, with avoidable reruns | Did not finish |
| Business logic compliance | Failures went to the planner, input problems to the lead; the final review waited for the planner and the challenger to finish; BLOCKED until every check passed | One rule followed loosely: a message sent to the wrong teammate | Sign-off declared ready while a check was failing |

## Teamwork (scored by script)

| Check | Kind |
|---|---|
| Every challenge has a response from the planner | critical |
| No challenge is open at the end | critical |
| Each teammate wrote only the files it owns | critical |
| The challenger read no raw data | critical |
| At most eight challenges in round one and four in round two | minor |
| Each teammate used only the tools its definition lists | minor |
| Every response round is followed by a new pack version | minor |
| All three teammates reported DONE to the lead | minor |

Score 3 when every check passes, 2 when only minor checks fail, 1 when a
critical check fails.
