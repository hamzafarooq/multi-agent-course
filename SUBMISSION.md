# Submission Guidelines

One rule for every project in this course: **you submit a URL, and the URL proves itself.**

## What you submit

A single **Vercel link** to your deployed app. That's it. **No repo, no zip, no code.** Nobody reads
your source to grade you; the running product and its own evidence page are the submission. The app
must have two things a grader can open without asking you anything:

| Route | What it is |
|---|---|
| `/` | The working product. The grader uses it exactly the way a user would. |
| `/evals` | A sub page rendering your **Product Evaluation**: the scored rubric with evidence, the benchmark numbers against the declared SLA, the quality-gate results, your design decisions, the two trajectories you read, and your 60 to 90 second demo video (embedded). |

Behind the page, `GET /evals/report.json` returns the same thing machine-readable, so the grader's
tooling can pull it. Its shape:

```jsonc
{
  "assignment": "LUMINA",
  "student": "Priya Nair",
  "video": "https://youtu.be/…",
  "design": { /* the five questions: components, responsibilities, communication, state, trade-offs */ },
  "deployedAt": "2026-09-19T18:02:11Z",
  "rubric":  { /* eval/report.json: per-criterion points, status, evidence */ },
  "bench":   { /* benchmark output: percentiles, grounding, recall, cache, cost, pass: true */ },
  "quality": { /* reports/quality.json from quality/check.mjs: rule results, errors, warnings */ },
  "trajectories": {
    "successful": { "requestId": "req_…", "steps": [ /* every tool call, in order */ ], "notes": "what it taught me" },
    "failing":    { "requestId": "req_…", "steps": [ /* … */ ], "notes": "what it taught me" }
  }
}
```

The `/evals` page is **not** something you hand-write. Your project's eval skill
(for example `/fde-lumina-eval`) runs the gates against the deployed app and writes
`report.json`; the provided UI renders it. Numbers on that page come from a real run.
**Fabricated numbers are an automatic fail.**

## Where and when

Post the Vercel URL where your instructor tells you (the Maven assignment for the project, or the
cohort channel). The URL is the submission; nothing else needs attaching.

| Project | Starts | Due |
|---|---|---|
| LUMINA (Perplexity-style AI search) | Week 1 | before the Week 3 live session |
| ARGUS (multimodal RAG) | Week 3 | before the Week 5 live session |
| VOXA (voice agent) | Week 5 | before the Week 7 live session |
| EPYHIA (end-to-end AI agency) | Week 7 | demoed live on Demo Day, URL posted before the session |

Your app must be **up when it is graded**. Graders run the eval against your URL during the
grading window, so a sleeping or broken deploy scores what it shows. Vercel's free tier is enough
for the UI; backends may live on Vercel functions or Fly.io as your assignment specifies. The
Vercel URL is what you submit either way.

## Before you post the link

- [ ] `/` works for a stranger with no setup: fresh browser, no local services.
- [ ] `/evals` renders, `/evals/report.json` returns valid JSON, and every number on it came from a run against **this** deployment.
- [ ] The video is embedded and shows the product doing the assignment's required flow in 60 to 90 seconds.
- [ ] The **design section** answers the five questions in your words: components, responsibilities, communication, state, trade-offs. Write it before you build; paste it into your eval config so it lands on the page.
- [ ] Both **trajectories are readable on the page**, every step of one successful and one failing run, with what each taught you. This is the human gate; a page without them cannot score those points.
- [ ] No secrets are reachable from the deployed app. Keys live in the host's environment, never in client-side JavaScript, never echoed by an endpoint.

## How you get feedback

Reviews cite **rule IDs, then evidence**, per the [quality bar](README.md#the-quality-bar-how-work-is-judged-and-how-to-give-feedback):
"`A1`: the fetch on step 3 failed and returned an empty string the model read as a normal result."
Expect that shape, and use it when you review a classmate. Feedback lands as comments on your
submission within the following week, and the rubric rows marked Fail or Partial tell you what to
fix first.

## Resubmission and lateness

- You may redeploy and re-run your eval as many times as you like before the deadline. The
  grader takes what the URL shows at grading time.
- One resubmission is allowed after feedback, for the rows marked Fail or Partial, within one week. Redeploy, re-run the eval, and repost the same URL.
- Late without notice: the project is graded on the rubric's automated rows only. Talk to the
  instructor before the deadline if you need more time; life happens, silence doesn't.

## Per-project specifics

Each assignment's README has a **Submit** section with the project-specific flow the video must
show and the eval skill to run: [LUMINA](modules/Module_1_Agent_Foundations_Harness_System_Design/Assignment_1_Lumina/README.md#submit) ·
[ARGUS](FDE-01-assignments/Assignment_3_Moment_Search_Scaled/README.md) · [VOXA](FDE-01-assignments/Assignment_2_voice_agent/README.md) ·
[EPYHIA](FDE-01-assignments/Assignment_4_Final_Epyhia/README.md). Where an older README says
"submit `PRODUCT_EVAL.md` plus a video" or asks you to push a repo, read it as: that content now
lives at `/evals` on your deployed app, and the code stays yours.

## Why no code

Three reasons, and none of them is that the code doesn't matter.

1. **A running product is a harder claim than a repo.** Source can look immaculate and not work. A URL a stranger can open, under an eval that ran against that deployment, cannot.
2. **It's the forward-deployed reality.** Customers judge the thing that's up, not the branch.
3. **It keeps the evidence honest.** Every number on `/evals` came from your live app rather than a local run nobody can reproduce. That is the [quality bar](README.md#the-quality-bar-how-work-is-judged-and-how-to-give-feedback)'s first law: a thing that ran is not a thing that worked.

Keep your repo private if you like. Bring it to office hours when you want a pair of eyes on the code itself; that's a conversation, not a submission.
