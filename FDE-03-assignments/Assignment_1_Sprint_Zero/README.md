# Assignment 1: SPRINT ZERO

> Point a sub-agent product team at a product you want to build or reverse engineer. You
> choose the reference and the scope; the agents write the specs, build the app in parallel
> and test it; you judge the result and run it again until the core loop works.

This folder is only the brief. **The kit you work with lives in
[`Full_Stack_Projects/Sprint_Zero/`](../../Full_Stack_Projects/Sprint_Zero/). Use that folder
for this assignment.** Its [`README.md`](../../Full_Stack_Projects/Sprint_Zero/README.md) is
the full guide: every command, flag, stack option and failure state.

The assignment is open ended. There is no fixed product, no answer key and no grader. What
you hand in is your app working, and the specs that produced it.

---

## Start here

First, **copy `Full_Stack_Projects/Sprint_Zero/` into a new repository of your own** and open
*that* folder in Claude Code. Inside the course repo, Claude Code would also load the course
tutor's `CLAUDE.md`, and your build would land in the course repo instead of yours.

You need [Node.js](https://nodejs.org) 18 or newer, Claude Code, and the Playwright MCP
registered in Claude Code (so QA can drive a browser). The default build needs no account, no
keys and no `.env`.

In your copy of the kit, start Claude Code:

```bash
claude
```

Then give it a reference URL:

```
/sprint-zero https://twenty.com
```

It asks a few scoping questions in one message. Answer in a paragraph, and skip anything you
don't care about to take the default.

## Then read, in this order

| # | Read | Why |
|---|---|---|
| 1 | The kit's [`README.md`](../../Full_Stack_Projects/Sprint_Zero/README.md) | How the flow works, the scope levels, the build options, troubleshooting. ~15 min. |
| 2 | [`examples/ghost-lite/`](../../Full_Stack_Projects/Sprint_Zero/examples/ghost-lite/) | One complete run against ghost.org: the six specs, the code and QA's test. Run it before your own. |
| 3 | [`examples/ghost-lite/docs/scope.md`](../../Full_Stack_Projects/Sprint_Zero/examples/ghost-lite/docs/scope.md) | What a good scope looks like: one core loop, a long and specific excludes list. |
| 4 | The kit's [`CLAUDE.md`](../../Full_Stack_Projects/Sprint_Zero/CLAUDE.md) | The rules every agent follows. Read it to understand why the agents behave as they do. |

## What you build

| | |
|---|---|
| ✅ **Provided** | The `/sprint-zero` pipeline (seven slash commands), four sub-agents (`tech-lead`, `backend-engineer`, `frontend-engineer`, `qa-engineer`), the stack catalog, the presenter UI and the ghost-lite worked example. |
| 🔨 **Yours** | The product you pick, the scope (level, core loop, excludes), your review of the six specs, and the decision to rebuild when the result is off. |

Pick any product: your own idea with a reference close to it, or an existing app you want to
reverse engineer.

## The build, in one screen

1. **Run the worked example.** Start ghost-lite and log in, so you know what a finished run looks like.
2. **Pick your reference.** A landing page, an open-source tool or a competitor. A repo URL as a second argument helps.
3. **Scope it.** Run `/sprint-zero <url>`. Choose the `MVP` level, state the one core loop, and list everything you are cutting.
4. **Read the spec set.** Six docs land in `docs/`: scope, reference brief, PRD, decisions, user stories, API contract.
5. **Watch the build.** The tech lead briefs it, then the backend and frontend engineers build in parallel against the API contract.
6. **Read the QA report.** QA signs up, logs in, logs out, checks protected routes and runs your core loop in a real browser.
7. **Use the app.** It launches seeded with demo data. Log in with the credentials from the launch summary.
8. **Run it again.** Delete a spec that is wrong and re-run its command, then `/sprint-zero <url> --rebuild`. Use `--fresh` to start the specs over.

An `MVP` run takes ten to twenty minutes, so plan for more than one.

## How you prove it

- QA reports a pass on the auth flow and on your core loop.
- You can do the core loop yourself, by hand, in the running app.
- Every scope cut is written down in `docs/decisions.md`.

A working 80% at the chosen scope beats a broken 100%.

## How you submit

You hand in two things:

- A **60 to 90 second demo video** of your running app, showing the core loop.
- The **six spec docs** from your run (`docs/`).

This assignment is the exception to the course-wide rules in
[`SUBMISSION.md`](../../SUBMISSION.md): no Vercel URL and no `/evals` page are required. The
kit produces code and does not deploy it.

## Stuck?

The kit's README covers the failures that cost the most time under
[Troubleshooting](../../Full_Stack_Projects/Sprint_Zero/README.md#-troubleshooting) and
[Named failure states](../../Full_Stack_Projects/Sprint_Zero/README.md#named-failure-states):
a page that fails to load data, QA that skips the browser tests, and a run that stops partway
(re-run `/sprint-zero` and it picks up where it stopped).
