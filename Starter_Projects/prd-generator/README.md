# PRD Generator

The `prd-generator` skill as a running app. You fill in a product idea, Claude writes the
full PRD (problem → goals → non-goals → user stories → Given/When/Then acceptance criteria →
risks → open questions → metrics), streaming into the page as it writes. Copy it as Markdown
or download it as `prd-<slug>.md`.

One file, no build step, no dependencies: [index.html](index.html).

## Run it

From this folder:

```bash
python3 -m http.server 5173
```

Then open **http://localhost:5173**.

Any static server works (`npx serve .`, `php -S localhost:5173`) — but it has to be a server.
Double-clicking `index.html` opens it as `file://`, and the browser will block the API call
with a CORS error. If the page loads but generating fails with a network error, that's almost
always this.

## Try it with no key

Click **Try the demo**, under the Generate button. It fills the form with a sample product
(DataPulse, a plain-English data-query tool) and renders its PRD instantly — no key, no
network call, nothing to spend. The output is labelled *Sample PRD — pre-written, no API call
made* so you can never mistake it for a live generation.

The PRD text is a real Claude output, saved into `DEMO_PRD` at the bottom of
[index.html](index.html). Read it to see what good output looks like before you pay for your
own.

## Add your key

Get one at [console.anthropic.com](https://console.anthropic.com/settings/keys) — it starts
with `sk-ant-`. Paste it into the **API Key** field in the top right. It's saved to
`localStorage`, so it survives a refresh on your machine and never leaves your browser except
in the call to Anthropic. There is no `.env` and no server to configure.

Then fill in your own product and hit **Generate PRD**. Everything after that is live.

## The part worth understanding

The live path is one `fetch` to `POST https://api.anthropic.com/v1/messages` with
`stream: true`, and a loop that reads SSE lines and appends every `content_block_delta` to a
string. That's it — no framework, no SDK, no backend:

```js
'x-api-key': apiKey,
'anthropic-version': '2023-06-01',
'anthropic-dangerous-direct-browser-access': 'true',
```

That third header is the one to notice. Anthropic blocks browser calls by default, and the
header name is a warning, not a feature: **a key in browser JavaScript is a key you have
given away.** Anyone who opens devtools on a deployed copy of this page reads it, and spends
it. This app is safe here only because "deployed" means your own laptop and the key is your
own.

The production shape is a thin backend: your server holds the key, the browser calls your
server, your server calls Anthropic. [`meetingmemo`](../meetingmemo/) and
[`meeting-notes-summarizer`](../meeting-notes-summarizer/) in this folder are both built that
way — read one of them next to this file and the difference is the whole lesson.

Model: `claude-opus-5`, at `effort: "low"` so the first tokens land fast enough to feel live.
Raise it in [index.html](index.html) if you want more considered PRDs and can wait longer.

## Things to try

- Change the prompt (search `index.html` for `const prompt`) and watch the PRD structure change — this is the skill's
  `SKILL.md` turned into a prompt string. Compare the two: `.claude/skills/prd-generator/SKILL.md`.
- Add a section the prompt doesn't ask for (pricing, GTM, a rollout plan).
- Feed the output to the `prd-reviewer` subagent and see what it flags as missing.
