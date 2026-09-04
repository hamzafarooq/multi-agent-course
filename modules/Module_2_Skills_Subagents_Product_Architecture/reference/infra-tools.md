# Reference — The Six Infrastructure Tools

<!-- INSTRUCTOR: Background on the infra the Sprint Zero agents stand up and ship onto.
     Source: 4_infra_tools. Supporting context — pull in when a learner asks "what is Supabase /
     Stripe / auth and why does the build agent use it." -->

Six tools power almost every modern product. You don't operate them deeply — you need enough
to make informed decisions and read what the agents produce.

## Supabase — database without a database team
Database (tables), authentication, file storage, and real-time sync in one dashboard, free
until ~50k MAU. Tables look like spreadsheets. The question that matters: *"What tables do we
have?"* — that answer is your data model, a direct reflection of every spec decision. If
there's no `subscriptions` table, you haven't shipped subscriptions.

## Authentication — the gatekeeper you should never build yourself
Proves a user is who they say they are: issues a token, every later request carries it, the
backend checks it before anything sensitive. Deceptively hard — plain-text passwords, missing
login rate limits, no session expiry are the *default* when teams underestimate it.
- **Methods:** email+password, magic link, OAuth ("sign in with Google"), SSO (Okta/SAML).
- **Tools:** Supabase Auth (MVPs), Auth0/Okta (enterprise SSO), Clerk (drop-in React UX),
  NextAuth (native to Next.js).

## Stripe — payments and billing infrastructure
Card processing, tax in 100+ countries, invoices, retry logic, MRR dashboard. It also surfaces
product strategy: flat vs. usage-based pricing, free-trial duration (tracked by cohort), and
dunning (what happens when a card fails — directly tied to churn). **MRR lives in Stripe.**

## Git — time travel for your codebase
Tracks every change to every file. Each save is a commit (message + timestamp + author), so
the whole history is queryable. Branches are isolated workspaces (two features built at once
without breaking each other); commits are the atomic unit of change; reverting is free, which
is why engineers can move fast.

## GitHub — where code lives and teams collaborate
Git is version control; GitHub puts it on the internet for a team. A living record of what
shipped: read commit messages (better than a standup), comment on pull requests, link bugs to
the code that caused them, see who changed what and when.

## VS Code — where everything happens
The editor most engineers use — and where Claude Code runs. The whole workflow (writing code,
running tests, talking to Claude, reviewing diffs) happens in one window. Know how to open a
file, use the integrated terminal, and find the Claude Code tab.

## The bottom line
Together these give a small team — or one person with Claude Code — the infrastructure to ship
a production product without a dedicated DevOps team, DBA, or payments engineer. The leverage
has shifted.
