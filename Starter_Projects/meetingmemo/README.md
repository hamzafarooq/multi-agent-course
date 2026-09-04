# MeetingMemo

Converts raw meeting notes into a structured standup update. Built live in Module 4 in 30 minutes.

## Run it locally

```bash
npm install
cp .env.example .env.local
# add your ANTHROPIC_API_KEY to .env.local
npm run dev
```

Open `http://localhost:3000`, paste in meeting notes, click Generate.

## Deploy to Vercel

```bash
npm i -g vercel
vercel link
vercel env add ANTHROPIC_API_KEY
vercel --prod
```

## How it works

1. User pastes meeting notes into the textarea
2. Frontend sends a POST to `/api/generate`
3. API route calls Claude with a system prompt that enforces the standup format
4. Claude returns three sections: What we decided / What I'm doing next / What's blocked
5. Frontend renders the output

The key file is `app/api/generate/route.ts` — read it. Every Claude-powered API route you ever build follows this same pattern.
