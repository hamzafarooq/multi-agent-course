# Meeting Notes Summarizer

Paste messy meeting notes, get a clean summary with key decisions and action items — no login, no setup, just paste and go.

## What it does

- Summarizes raw meeting notes into a 2-4 sentence overview
- Extracts key decisions made in the meeting
- Pulls out action items and infers owners from the text
- One-click copy of the full output

## How to run it

### 1. Get an OpenRouter API key

Sign up at [openrouter.ai](https://openrouter.ai) and create an API key. OpenRouter gives you access to models from OpenAI, Anthropic, Meta, and others through a single key.

### 2. Install dependencies

```bash
cd meeting-notes-summarizer
npm install
```

### 3. Set your API key

Copy the example env file and add your key:

```bash
cp .env.example .env
```

Open `.env` and replace `your_openrouter_api_key_here` with your actual key:

```
OPENROUTER_API_KEY=sk-or-...
MODEL=openai/gpt-4o-mini
```

The `MODEL` variable is optional — it defaults to `openai/gpt-4o-mini`. You can swap it for any model on OpenRouter (e.g. `anthropic/claude-3-haiku`, `meta-llama/llama-3.1-8b-instruct:free`).

### 4. Start the app

```bash
npm start
```

Open your browser and go to: **http://localhost:3000**

### For development (auto-restarts on file changes)

```bash
npm run dev
```

## Project structure

```
meeting-notes-summarizer/
├── server.js          # Express backend — handles API calls to Claude
├── public/
│   └── index.html     # Frontend — everything runs in this one file
├── .env.example       # Copy this to .env and add your API key
├── .gitignore
├── package.json
└── README.md
```

## Tech stack

- **Backend:** Node.js + Express
- **Frontend:** Vanilla HTML/CSS/JavaScript (no build step)
- **AI:** Any model via [OpenRouter](https://openrouter.ai) (default: `openai/gpt-4o-mini`)
