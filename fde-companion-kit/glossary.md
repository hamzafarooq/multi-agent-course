# Glossary

Every term in the companion, in plain words. `/companion-explain` uses this file, and it matches the glossary on the companion site (https://companion.traversaal.ai/glossary/), so the words here match the videos and the reading.

Each term has: **In plain words** (how you'd explain it to a ten-year-old), **Coming from data science** (the same idea in terms a data scientist knows), and **Exactly** (the precise meaning).

## The job

### FDE

- **In plain words:** An engineer who goes to work with a customer, sits with their team, and builds the AI system they actually need, instead of a one-size-fits-all product from far away.
- **Coming from data science:** Like an embedded data scientist on a business team, except you ship and run the production system, not just the analysis.
- **Exactly:** An engineer who deploys and adapts AI systems inside a client's environment, owning the problem from discovery to production.
- **Where:** 1.1 What an FDE does

### PRD and spec

- **In plain words:** The PRD says what to build and why, written for people. The spec says exactly what must be true, so a coding agent can build it without guessing.
- **Coming from data science:** The PRD is your problem-framing doc; the spec is the precise requirements plus acceptance tests, like a data contract with its test suite.
- **Exactly:** Every project here ships both: PRD.md for humans, SPEC.md (with AGENTS.md) for the coding agent. Where they disagree, the spec wins.
- **Where:** 1.2 A first look at system design

### SLA

- **In plain words:** A promise about how well the app works: how fast it answers, how often it's up, how often it's right.
- **Coming from data science:** Service-level targets such as p95 latency and quality thresholds. In this course you prove them with a benchmark, the way you report metrics on a holdout set.
- **Exactly:** The declared targets a system must meet, checked by each project's benchmark.
- **Where:** 1.2 A first look at system design

## The model

### LLM

- **In plain words:** A super-powered autocomplete. It has read a huge amount of text and guesses the next word, again and again, until it has an answer. On its own it can only write text: it can't open files or press buttons.
- **Coming from data science:** A very large autoregressive sequence model: it outputs a probability distribution over the next token, and generation is repeated sampling from it. The weights are frozen when you use it.
- **Exactly:** A model that predicts the next token of text. Text in, text out. It doesn't read files, run commands or remember anything by itself.
- **Where:** 2.1 How LLMs work · Book §3.1

### Token

- **In plain words:** The pieces a model chops text into, often a word or part of one: "unbelievable" might be "un" + "believ" + "able". Models read, write and charge by the token.
- **Coming from data science:** The tokenizer's output: subword units (BPE), about ¾ of an English word each. Think of the vocabulary after your text vectorizer, but in subwords.
- **Exactly:** The unit a model reads and writes, roughly ¾ of an English word. Price, speed and limits are all counted in tokens.
- **Where:** 2.1 How LLMs work · Book §3.1

### Context window

- **In plain words:** How much the model can see at once, like the size of its desk. Everything it needs has to fit on the desk; whatever falls off, it can't see.
- **Coming from data science:** The model's maximum sequence length in tokens, input and output together. Past it, data is truncated: there's no look-back.
- **Exactly:** The maximum number of tokens the model can consider in one call, including its own answer. Outside the window, nothing exists.
- **Where:** 2.1 How LLMs work · Book §3.1

### Statelessness

- **In plain words:** The model forgets you after every message. A chat only seems to remember because the app sends the whole conversation again each time.
- **Coming from data science:** Inference is a pure function, like model.predict(): nothing is kept between calls. Apparent memory is you re-sending the inputs.
- **Exactly:** Each API call is independent. Apparent memory is the application resending earlier text.
- **Where:** 2.1 How LLMs work · Book §3.1

### System prompt

- **In plain words:** The instructions an app gives the model before you say anything: who it is, what it should and shouldn't do. You usually don't see it.
- **Coming from data science:** A fixed prefix on every input that conditions the task, like a config that applies to the whole run.
- **Exactly:** Instructions placed before the conversation on every call; part of the context.
- **Where:** 2.1 How LLMs work

### Temperature

- **In plain words:** A creativity dial. Turned low, it picks the safest next word every time; turned high, it takes more chances.
- **Coming from data science:** The softmax temperature when sampling the next token (logits ÷ T). Near 0 is close to argmax; higher flattens the distribution. Outputs stay stochastic, which is why you evaluate over many runs.
- **Exactly:** How random the next-token choice is. Low for extraction and code, higher for ideas. Never fully deterministic, which is why evals matter.
- **Where:** 2.1 How LLMs work · Book §3.1

### Token cost

- **In plain words:** You pay for every piece of text you send and every piece you get back, every time. Sending the whole chat history again costs again.
- **Coming from data science:** Pay per inference, priced by input plus output tokens (output costs more). Compute cost per prediction that grows with sequence length.
- **Exactly:** You pay per input and output token on every call. Resent history and stuffed documents add up fast.
- **Where:** 2.1 How LLMs work · Book §3.1

### Open vs. closed models

- **In plain words:** Closed models (Claude, GPT) you rent over the internet. Open models (Llama, Qwen) you can download and run on your own computers.
- **Coming from data science:** Closed is API-only, like a hosted prediction service. Open-weight gives you the checkpoint, like a pretrained model from Hugging Face that you serve yourself.
- **Exactly:** Closed models are API-only. Open-weight models can run on your own infrastructure for control, data residency and cost.
- **Where:** 2.1 How LLMs work · Book §3.1

### Hallucination

- **In plain words:** When the model makes something up and says it confidently.
- **Coming from data science:** Fluent but ungrounded output: likely under the model, not true. The reason for grounding (RAG) and evals.
- **Exactly:** Output that sounds right but isn't supported by the input or by fact.
- **Where:** 2.1 How LLMs work

### Fine-tuning

- **In plain words:** Training a model a bit more on your own examples so it gets better at your task.
- **Coming from data science:** Continued training of pretrained weights on task data; you know this one. In agent work, try prompting, tools and RAG first, and fine-tune when they fall short.
- **Exactly:** Updating a model's weights on your data. Changes the model; prompting, tools and RAG change only its input.
- **Where:** 2.1 How LLMs work

## Agents

### Agent

- **In plain words:** An LLM that can do things, not just talk. It gets tools (like "look up an order"), uses one, looks at what came back, and decides what to do next, until the job is done.
- **Coming from data science:** A policy in a loop: observe the state, choose an action (a tool call), get an observation back, repeat. Like an RL agent's loop, except the policy is a prompted LLM, not a trained one.
- **Exactly:** An LLM given tools and run in a loop that feeds results back, so it can act, observe and adjust instead of only replying.
- **Where:** 2.2 What turns an LLM into an agent · Book §3.1–3.2

### Agentic

- **In plain words:** Describes software where the AI decides the steps itself, instead of a person writing every step in advance.
- **Coming from data science:** Control flow chosen by the model at run time, rather than a fixed DAG you wrote in advance.
- **Exactly:** Using an agent loop: the model picks the next action from what it has observed.
- **Where:** 2.2 What turns an LLM into an agent

### Context

- **In plain words:** Everything on the model's desk this turn: its instructions, the chat so far, the list of tools, and what the tools sent back. If it's not on the desk, the model doesn't know it.
- **Coming from data science:** The full input sequence at one step: the feature vector for this prediction. Context engineering is feature engineering for LLMs.
- **Exactly:** Everything the model sees on a turn: system prompt, history, tool descriptions and tool results. The agent's entire world. The C in CTL.
- **Where:** 2.2 What turns an LLM into an agent · Book §3.1–3.2

### Tools

- **In plain words:** Buttons the model can ask to press, like "look up order" or "read file". The model says which button and with what; your code actually presses it and tells the model what happened.
- **Coming from data science:** Functions described by a JSON schema. The model outputs a structured call (name and arguments), your runtime executes it and appends the result to the context. The model never runs code itself.
- **Exactly:** Functions you define and describe. The model requests a call; your code decides whether to run it and returns the result. The T in CTL.
- **Where:** 2.2 What turns an LLM into an agent · Book §3.1–3.2

### Agent loop

- **In plain words:** Read → Plan → Act → Observe → Repeat. Like a puzzle: look, think, try a move, see what happened, go again, until it's solved or you run out of tries.
- **Coming from data science:** The while-loop around inference: while not done and steps < max, call the model, run the tool, append the result. An iterative process with a stopping rule, where each step is a tool call.
- **Exactly:** Read → Plan → Act → Observe → Repeat, until the model answers without a tool call or a step limit is hit. The L in CTL.
- **Where:** 2.2 What turns an LLM into an agent · Book §3.2

### CTL

- **In plain words:** The three things that make an agent: what it can see (Context), what it can do (Tools), and how it keeps going (Loop).
- **Coming from data science:** Inputs, actions and the control loop: the whole agent described in three parts.
- **Exactly:** Context, Tools, Loop: the course's short way to describe any agent.
- **Where:** 2.2 What turns an LLM into an agent · Book §3.1–3.2

### ReAct

- **In plain words:** A way of working: think out loud, do one thing, look at the result, think again.
- **Coming from data science:** Reason + Act (Yao et al., 2022): interleaving reasoning with actions. The paper behind most agent loops.
- **Exactly:** The reason-then-act-then-observe pattern most agent loops follow.
- **Where:** 2.2 What turns an LLM into an agent · Book §3.1–3.2

### Trace

- **In plain words:** A diary of everything the agent did: what it saw, what it chose, what came back. When something goes wrong, you read the diary.
- **Coming from data science:** Experiment tracking for a single run, step by step (inputs, outputs, latency and cost at each step), like MLflow logging. The thing you debug from.
- **Exactly:** The log of every step an agent took. The first thing you open when an agent misbehaves.
- **Where:** 2.2 What turns an LLM into an agent · Book §3.1–3.2

### Trajectory

- **In plain words:** The path the agent took to its answer, step by step. Two agents can reach the same answer by very different paths.
- **Coming from data science:** The sequence of (state, action, observation), as in RL. Evaluating it checks the process, not just the final label.
- **Exactly:** The ordered steps of one agent run; every project asks you to read two.
- **Where:** 2.2 What turns an LLM into an agent

## The harness

### Harness

- **In plain words:** The model is a brain in a jar. The harness is the body around it: hands (tools), eyes (reading files), rules about what it may touch (permissions) and a notebook (memory). It also runs the loop. Claude Code is a harness.
- **Coming from data science:** Everything around model.predict() that makes it useful in production: the loop, I/O, data access, permissions, logging. The serving stack around a model, where most of the engineering lives.
- **Exactly:** The runtime scaffolding around a model that manages the loop, tools, permissions and context. The model is the brain; the harness is the body.
- **Where:** 2.3 The harness and Claude Code · Book §3.3–3.4

### Permissions

- **In plain words:** Rules about what the agent may do on its own and what it has to ask you first, like "ask before deleting anything".
- **Coming from data science:** Access control on actions: allow, ask or deny, checked before any tool runs. IAM roles for the agent.
- **Exactly:** Gates between the model and risky actions (running commands, deleting files, pushing). The harness asks; you decide.
- **Where:** 2.3 The harness and Claude Code · Book §3.3–3.4

### Memory

- **In plain words:** The model forgets everything when a session ends. Memory is the notes the harness keeps and hands back next time, like a notebook it reads every morning.
- **Coming from data science:** State persisted outside the model and put back into the context: files like CLAUDE.md, a database, a vector store. Not the weights: the model doesn't learn, you feed it its notes.
- **Exactly:** What survives between sessions. The model has none; the harness provides it via CLAUDE.md, skills and commands.
- **Where:** 2.3 The harness and Claude Code · Book §3.3–3.4

### Claude Code

- **In plain words:** Anthropic's agent that works inside your code editor. You ask in plain words; it reads files, runs commands and edits code, and asks before risky moves.
- **Coming from data science:** A ready-made harness for software work: an LLM plus tools (files, shell, search), permissions and memory, in VS Code or the terminal.
- **Exactly:** Anthropic's agentic coding harness: the agent loop with tools for files, commands and search, plus permissions and memory, in a chat panel in your editor.
- **Where:** 2.3 The harness and Claude Code · Book §3.3–3.4

### Plan mode

- **In plain words:** "Tell me your plan before you touch anything." Claude writes the plan, and nothing changes until you say go.
- **Coming from data science:** A dry run: propose the changes, review them, then execute. Like reviewing a migration before applying it.
- **Exactly:** Claude Code proposes a plan without changing anything until you approve it. Use it for anything bigger than one file.
- **Where:** 2.3 The harness and Claude Code · Book §3.3–3.4

### Slash command

- **In plain words:** A shortcut you type that starts with "/", like /companion. It runs a saved set of instructions.
- **Coming from data science:** A named, reusable prompt: a saved function you call by name.
- **Exactly:** A command in Claude Code that runs a saved prompt or skill.
- **Where:** 2.4 CLAUDE.md and Skills

### Hooks

- **In plain words:** Little rules that run by themselves at set moments, like "every time a file changes, run the tests".
- **Coming from data science:** Callbacks on events (before or after a tool call), like callbacks in a training loop.
- **Exactly:** Scripts the harness runs automatically on events such as a tool call or the end of a turn.
- **Where:** 2.4 CLAUDE.md and Skills

## Extending an agent

### CLAUDE.md

- **In plain words:** A note in the project folder that Claude reads first, every time: what this project is, how to run it, what not to do. Like a welcome note for a new teammate.
- **Coming from data science:** A README written for the agent and loaded into its context every session: persistent config plus domain knowledge.
- **Exactly:** A project file the harness loads into context at the start of every session: what this is, how it's built, how to run it, what to avoid.
- **Where:** 2.4 CLAUDE.md and Skills · Book Ch 2

### Skills

- **In plain words:** A recipe card Claude pulls out when it needs it: the steps for one job, plus any files that job needs. Write it once, reuse it forever.
- **Coming from data science:** A packaged, reusable procedure (instructions and scripts) loaded only when relevant, like a library the agent imports on demand, so the context stays small.
- **Exactly:** A named, packaged workflow (SKILL.md plus optional files) Claude runs on request. One word, infinite reuse.
- **Where:** 2.4 CLAUDE.md and Skills · Book Ch 4

### MCP

- **In plain words:** A universal plug. Any tool built for it (a browser, a database, Slack) plugs into any agent that speaks it, like USB for AI tools.
- **Coming from data science:** A standard client–server protocol for exposing tools and data to any harness. Like ODBC or JDBC for databases: write the connector once, every client can use it.
- **Exactly:** Model Context Protocol: a standard way to plug new tools into any harness, such as a browser, a database or Slack.
- **Where:** 2.5 MCP and Subagents · Book §3.12

### Subagents

- **In plain words:** Helpers the main agent sends off to do one job at their own clean desk. They come back with just the answer, so the main agent's desk stays tidy.
- **Coming from data science:** A worker with its own context, tools and model that returns a summary. Like the map step in map-reduce: do the heavy work in isolation, send back something small.
- **Exactly:** Specialists with their own context window, tools and model. They keep big or separable tasks out of your main context.
- **Where:** 2.5 MCP and Subagents · Book Ch 5

### Pipelines and agent teams

- **In plain words:** Several agents working together, like an assembly line: one researches, one writes, one checks.
- **Coming from data science:** A fixed DAG of agents (a pipeline) or agents coordinating as they go (a team), like the stages of an ML pipeline where each stage is an agent.
- **Exactly:** Several agents chained or collaborating: research → write → review. The bridge into multi-agent systems in Module 5.
- **Where:** 2.5 MCP and Subagents · Book Ch 6

### Orchestration

- **In plain words:** The conductor who decides which agent does what and when, and collects the results.
- **Coming from data science:** Workflow orchestration, like Airflow or Prefect, except the tasks are agents and the orchestrator can itself be an LLM picking the next step.
- **Exactly:** Coordinating several agents: routing work, passing state and combining results.
- **Where:** Module 5

## The product

### API and API key

- **In plain words:** An API is a menu of things one program can ask another to do. An API key is your password for it, and whoever has your key gets your bill.
- **Coming from data science:** The HTTP interface you call for predictions, like a hosted model endpoint; the key authenticates and bills you. Never put it in a notebook you share or in frontend code.
- **Exactly:** How programs talk to each other over the web, and the secret that identifies the caller.
- **Where:** 3.1 Full-stack AI architecture

### Endpoint

- **In plain words:** One address on an API that does one thing, like /orders or /chat.
- **Coming from data science:** A URL and method mapped to one function, like a model server's /predict route.
- **Exactly:** A single route of an API.
- **Where:** 3.1 Full-stack AI architecture

### Frontend

- **In plain words:** The part you see and click: pages, buttons, the chat box. It runs in your browser.
- **Coming from data science:** The dashboard layer, like a Streamlit app's UI, except anyone can read its code, so it never holds secrets.
- **Exactly:** What users touch: React in the browser. Never holds secrets.
- **Where:** 3.1 Full-stack AI architecture · Book §3.5–3.10

### Backend

- **In plain words:** The kitchen behind the restaurant: it stores the data, checks who you are, does the real work and keeps the secret keys.
- **Coming from data science:** The server: business logic, database, authentication. The service that wraps your model and data behind an API.
- **Exactly:** The API behind the click: auth, data, business logic, and the place your API keys live.
- **Where:** 3.1 Full-stack AI architecture · Book §3.5–3.10

### AI backend

- **In plain words:** The part of the kitchen where the AI cooks: model calls, agents, search. It's kept separate so it can grow or be swapped.
- **Coming from data science:** Your model-serving service: inference, retrieval and agents behind their own API, scaled on their own.
- **Exactly:** Where the intelligence runs: LLM calls, agents, retrieval. Often its own service so it can scale and be swapped.
- **Where:** 3.1 Full-stack AI architecture · Book §3.5–3.10

### Streaming

- **In plain words:** Showing the answer word by word as it's written, instead of making you wait for all of it.
- **Coming from data science:** Sending tokens as they're sampled instead of one response at the end. It cuts time to first token, not total time.
- **Exactly:** Sending the model's answer token by token as it's generated, so users see progress instead of a spinner.
- **Where:** 3.1 Full-stack AI architecture · Book §3.5–3.10

### Docker

- **In plain words:** A lunchbox for an app: the app plus everything it needs, packed so it runs the same on any computer.
- **Coming from data science:** A reproducible environment, like a pinned conda environment plus the OS, packed into one image. "Works on my machine", solved.
- **Exactly:** Packages an app and everything it needs into an image that runs the same everywhere as a container.
- **Where:** 3.1 Full-stack AI architecture · Book §3.5–3.10

### Deploy

- **In plain words:** Putting your app on the internet with a web address so other people can use it.
- **Coming from data science:** From notebook to production: the app runs on a server at a URL, like serving a model instead of running it locally.
- **Exactly:** Putting your app on a server with a public URL so the client can use it. Every project here is submitted as a deployed link.
- **Where:** 3.1 Full-stack AI architecture · Book §3.5–3.10

## Later in the bootcamp

### RAG

- **In plain words:** An open-book test. Before answering, the agent looks up the few pages that matter and reads them, instead of guessing from memory or reading the whole library.
- **Coming from data science:** Retrieve, then generate: embed the documents, retrieve the top k by similarity (vector search, BM25 or both), put them in the prompt, generate. A search and ranking system feeding the LLM, so precision and recall at k matter, as in information retrieval.
- **Exactly:** Retrieval-augmented generation: fetch only the relevant documents and put them in context, instead of everything.
- **Where:** Module 4

### Embeddings and vector databases

- **In plain words:** Turning text into lists of numbers so that similar meanings land close together. A vector database stores them and finds the closest ones fast.
- **Coming from data science:** Dense representations you already know, plus an approximate nearest-neighbour index (FAISS, Qdrant). The retrieval half of RAG.
- **Exactly:** Vectors that represent meaning, and the store that searches them by similarity.
- **Where:** Module 4

### Evals

- **In plain words:** Tests for AI. You give it lots of example jobs and score how it did, so you notice when a change makes it worse.
- **Coming from data science:** Model evaluation on a test set, but scored on outcomes and on the path the agent took, often with an LLM as the judge. Regression tests for a stochastic system.
- **Exactly:** Systematic tests of an agent's outcomes and trajectories, so you catch regressions before your client does.
- **Where:** Every module, from the first project

### Golden dataset

- **In plain words:** A set of real questions with the answers a good expert would give. You run it again and again to check you're still right.
- **Coming from data science:** Your labelled, versioned test set, curated with domain experts. Fixed, and never trained on.
- **Exactly:** Real cases with the answer a good person would give, run again and again to measure a system.
- **Where:** Module 4, first seen in 6.1

### Guardrails

- **In plain words:** Safety fences: checks on what goes in and what comes out, so the agent doesn't say or do something it shouldn't.
- **Coming from data science:** Input and output classifiers and rules (Llama Guard, PII filters) around the model, like validation checks on a pipeline.
- **Exactly:** Checks on inputs and outputs that block unsafe or off-policy behaviour.
- **Where:** First seen in 6.1

### Observability

- **In plain words:** A dashboard that shows what your agents are doing right now: how fast, how much it costs, where it breaks.
- **Coming from data science:** Production monitoring (traces, latency, cost, quality drift per request): model monitoring, extended to every step of the agent.
- **Exactly:** Tracing, dashboards, latency, cost and quality per request, for agents in production.
- **Where:** Module 6

### A2A

- **In plain words:** A shared language so agents built by different teams can hand work to each other.
- **Coming from data science:** Agent-to-Agent protocol: a standard API for one agent service to find and call another, like microservices with a common contract.
- **Exactly:** Agent-to-agent protocol for coordinating independent agent services.
- **Where:** Module 5
