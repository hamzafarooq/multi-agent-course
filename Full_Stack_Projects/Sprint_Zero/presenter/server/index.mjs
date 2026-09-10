import express from "express";
import chokidar from "chokidar";
import { createServer } from "node:http";
import { promises as fs } from "node:fs";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..", "..");
const PRESENTER_DIR = path.resolve(__dirname, "..");
const DIST_DIR = path.join(PRESENTER_DIR, "dist");
const DOCS_DIR = path.join(ROOT, "docs");
const STATUS_DIR = path.join(ROOT, ".sprint-zero");
const STATUS_FILE = path.join(STATUS_DIR, "status.json");
const SERVER_DIR = path.join(ROOT, "server");
const CLIENT_DIR = path.join(ROOT, "client");

const SAMPLE_DIR = path.join(PRESENTER_DIR, "sample");
const SAMPLE_DOCS_DIR = path.join(SAMPLE_DIR, "docs");
const SAMPLE_STATUS_FILE = path.join(SAMPLE_DIR, "status.json");

// Demo mode: with no real run on disk, serve the committed sample run so all
// three tabs work — for a class demo, or a deploy where there is no filesystem
// to watch. A real run always wins. SPRINT_ZERO_DEMO=0 turns it off entirely.
const DEMO_ENABLED = process.env.SPRINT_ZERO_DEMO !== "0";

const DOC_FILES = [
  "scope.md",
  "reference-brief.md",
  "prd.md",
  "decisions.md",
  "user-stories.md",
  "api-contract.md",
];

/* ----------------------------- state ------------------------------- */

const EMPTY_STATUS = {
  phase: "idle",
  docs: [],
  build: { backend: "idle", frontend: "idle" },
  appUrl: null,
  credentials: null,
  projectName: null,
  failure: null,
};

async function readStatus() {
  try {
    const raw = await fs.readFile(STATUS_FILE, "utf8");
    const parsed = JSON.parse(raw);
    const docs = await listDocs(DOCS_DIR);
    const config = await readConfig(DOCS_DIR);
    return { ...EMPTY_STATUS, ...parsed, docs, config };
  } catch {
    const docs = await listDocs(DOCS_DIR);
    if (docs.length) {
      // scope.md exists but no status file yet: we're past scoping
      const config = await readConfig(DOCS_DIR);
      return { ...EMPTY_STATUS, phase: "research", docs, config };
    }
    return (await readSampleStatus()) ?? { ...EMPTY_STATUS, phase: "idle", docs };
  }
}

// The build configuration lives in docs/scope.md. Surface it so the UI can name
// the real stack instead of assuming node-react + supabase.
async function readConfig(dir) {
  try {
    const md = await fs.readFile(path.join(dir, "scope.md"), "utf8");
    const pick = (label) => md.match(new RegExp(`\\*\\*${label}:\\*\\*\\s*\`?([\\w-]+)`))?.[1] ?? null;
    const level = md.match(/## Build level\s+\*\*(\w+)\*\*/)?.[1] ?? null;
    const projectType = pick("Project type");
    const stack = pick("Stack profile");
    const dataLayer = pick("Data layer");
    if (!projectType && !stack && !dataLayer && !level) return null;
    return { projectType, stack, dataLayer, level };
  } catch {
    return null;
  }
}

// The committed sample run. Returned only when the real run is absent, and
// flagged `demo: true` so the UI can label it as a recording, not a live run.
async function readSampleStatus() {
  if (!DEMO_ENABLED) return null;
  try {
    const parsed = JSON.parse(await fs.readFile(SAMPLE_STATUS_FILE, "utf8"));
    const docs = await listDocs(SAMPLE_DOCS_DIR);
    if (!docs.length) return null;
    const config = await readConfig(SAMPLE_DOCS_DIR);
    return { ...EMPTY_STATUS, ...parsed, docs, config, demo: true };
  } catch {
    return null;
  }
}

async function usingSample() {
  if (!DEMO_ENABLED) return false;
  if (existsSync(STATUS_FILE)) return false;
  return (await listDocs(DOCS_DIR)).length === 0;
}

async function listDocs(dir) {
  try {
    const entries = await fs.readdir(dir);
    return DOC_FILES.filter((name) => entries.includes(name));
  } catch {
    return [];
  }
}

/* --------------------------- SSE clients --------------------------- */

const sseClients = new Set();

function broadcast(status) {
  const payload = `event: status\ndata: ${JSON.stringify(status)}\n\n`;
  for (const res of sseClients) {
    try {
      res.write(payload);
    } catch {
      /* ignore */
    }
  }
}

let broadcastTimer = null;
function scheduleBroadcast() {
  if (broadcastTimer) return;
  broadcastTimer = setTimeout(async () => {
    broadcastTimer = null;
    const status = await readStatus();
    broadcast(status);
  }, 120); // coalesce rapid file events
}

/* ----------------------------- watcher ----------------------------- */

function startWatcher() {
  const paths = [DOCS_DIR, STATUS_DIR, SERVER_DIR, CLIENT_DIR].filter(Boolean);

  const watcher = chokidar.watch(paths, {
    ignored: (p) =>
      p.includes("node_modules") ||
      p.includes(".git") ||
      p.endsWith(".DS_Store") ||
      p.includes("playwright-report") ||
      p.includes("test-results"),
    persistent: true,
    ignoreInitial: true,
    depth: 3,
  });

  watcher.on("all", () => scheduleBroadcast());
  watcher.on("error", (err) => {
    console.error("[presenter] watcher error:", err);
  });
}

/* ----------------------------- server ------------------------------ */

const app = express();
app.use(express.json({ limit: "256kb" }));

app.get("/api/state", async (_req, res) => {
  res.json(await readStatus());
});

app.get("/api/stream", (req, res) => {
  res.writeHead(200, {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache, no-transform",
    Connection: "keep-alive",
    "X-Accel-Buffering": "no",
  });
  res.write(": connected\n\n");

  sseClients.add(res);

  // Push initial state immediately
  readStatus().then((s) => {
    res.write(`event: status\ndata: ${JSON.stringify(s)}\n\n`);
  });

  // Heartbeat so proxies don't drop the connection
  const heartbeat = setInterval(() => {
    try {
      res.write(": ping\n\n");
    } catch {
      /* ignore */
    }
  }, 20_000);

  req.on("close", () => {
    clearInterval(heartbeat);
    sseClients.delete(res);
  });
});

app.get("/api/doc/:name", async (req, res) => {
  const name = req.params.name;
  if (!DOC_FILES.includes(name)) {
    res.status(404).type("text/plain").send("Unknown doc");
    return;
  }
  const dir = (await usingSample()) ? SAMPLE_DOCS_DIR : DOCS_DIR;
  try {
    const raw = await fs.readFile(path.join(dir, name), "utf8");
    res.type("text/plain").send(raw);
  } catch {
    res.status(404).type("text/plain").send("Not written yet");
  }
});

const PROJECT_TYPES = ["web-app", "api-service", "cli-tool"];
const STACKS = ["node-react", "nextjs", "python-react"];
const DATA_LAYERS = ["local", "supabase"];

const STACK_LABELS = {
  "node-react": { backend: "an Express API", frontend: "a React + Vite UI", cli: "a Node CLI" },
  nextjs: { backend: "Next.js route handlers", frontend: "Next.js pages", cli: "a Node CLI" },
  "python-react": { backend: "a FastAPI backend", frontend: "a React + Vite UI", cli: "a Python CLI" },
};

function describeConfig(projectType, stack, dataLayer) {
  const l = STACK_LABELS[stack];
  const data =
    dataLayer === "local"
      ? "data and auth stored locally in SQLite (no external account needed)"
      : "data and auth in a hosted Supabase project (needs a .env)";
  if (projectType === "cli-tool") return `${cap(l.cli)} with ${data}. No server, no browser.`;
  if (projectType === "api-service") return `${cap(l.backend)} with ${data}. No frontend.`;
  if (stack === "nextjs") return `One Next.js app serving both UI and API on one port, with ${data}.`;
  return `${cap(l.frontend)} talking to ${l.backend}, with ${data}.`;
}

function cap(s) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

const LEVEL_DESCRIPTIONS = {
  clickable: "A walkthrough with fake data and no real auth, for pitching and flow reviews.",
  MVP: "Real auth and real data on one core loop, end to end.",
  Prod: "MVP plus error handling, validation, and loading states, ready for 5 to 10 real users.",
};

app.post("/api/scope", async (req, res) => {
  const body = req.body ?? {};
  const projectName = (body.projectName || "").trim();
  const companyUrl = (body.companyUrl || "").trim();
  const repoUrl = (body.repoUrl || "").trim();
  const level = body.level;
  const projectType = body.projectType || "web-app";
  const stack = body.stack || "node-react";
  const dataLayer = body.dataLayer || "local";
  const coreLoop = (body.coreLoop || "").trim();
  const excludes = (body.excludes || "").trim();

  if (!companyUrl) return res.status(400).send("companyUrl is required");
  if (!["clickable", "MVP", "Prod"].includes(level))
    return res.status(400).send("level must be clickable, MVP, or Prod");
  if (!PROJECT_TYPES.includes(projectType))
    return res.status(400).send(`projectType must be one of ${PROJECT_TYPES.join(", ")}`);
  if (!STACKS.includes(stack)) return res.status(400).send(`stack must be one of ${STACKS.join(", ")}`);
  if (!DATA_LAYERS.includes(dataLayer))
    return res.status(400).send(`dataLayer must be one of ${DATA_LAYERS.join(", ")}`);
  if (!coreLoop) return res.status(400).send("coreLoop is required");

  const companyUrlNormalized = ensureScheme(companyUrl);
  const repoUrlNormalized = repoUrl ? ensureScheme(repoUrl) : "";

  const excludeLines = excludes
    ? excludes
        .split(/\n+/)
        .map((s) => s.trim())
        .filter(Boolean)
        .map((s) => `- ${s.replace(/^[-*•]\s*/, "")}`)
        .join("\n")
    : "None specified.";

  // Same structure /sprint-zero-scope writes, so every downstream command reads it identically.
  const assumptions = [];
  if (projectType !== "web-app")
    assumptions.push(`- [ASSUMED] \`${projectType}\` has no frontend, so the stack profile's frontend half is ignored and there is no browser auth dance.`);
  if (projectType === "cli-tool" && dataLayer === "supabase")
    assumptions.push("- [ASSUMED] A CLI with the `supabase` data layer is unusual; the CLI will read the Supabase keys from `.env`.");
  if (stack === "nextjs" && projectType === "web-app")
    assumptions.push("- [ASSUMED] With `nextjs`, UI and API live in one app on one port; there is no separate `server/` and `client/` split.");

  const scopeMd = `# Sprint Zero — Scope

## Reference

- **Company URL:** ${companyUrlNormalized}
- **Repo URL:** ${repoUrlNormalized || "not provided"}

## Build configuration

- **Project type:** ${projectType}
- **Stack profile:** ${stack}
- **Data layer:** ${dataLayer}

${describeConfig(projectType, stack, dataLayer)}

## Build level

**${level}**

${LEVEL_DESCRIPTIONS[level]}

## Core loop

${coreLoop}

## Excludes

${excludeLines}
${assumptions.length ? `\n## Assumptions made during scoping\n\n${assumptions.join("\n")}\n` : ""}`;

  await fs.mkdir(DOCS_DIR, { recursive: true });
  await fs.writeFile(path.join(DOCS_DIR, "scope.md"), scopeMd, "utf8");

  // Stash project name into a meta file so the orchestrator can pick it up
  await fs.mkdir(STATUS_DIR, { recursive: true });
  await fs.writeFile(
    path.join(STATUS_DIR, "meta.json"),
    JSON.stringify(
      { projectName, companyUrl: companyUrlNormalized, repoUrl: repoUrlNormalized, projectType, stack, dataLayer, level },
      null,
      2
    ),
    "utf8"
  );

  // Optimistic status: advance UI immediately so the user doesn't stare at a loading state
  // waiting for the orchestrator to poll the filesystem.
  const existing = await readStatus();
  const optimistic = {
    ...existing,
    phase: "research",
    step: "reference-brief",
    stepNumber: 2,
    message: "Scope written. Waiting for the orchestrator to pick it up.",
    projectName,
    timestamp: new Date().toISOString(),
  };
  broadcast(optimistic);

  res.json({ ok: true });
});

/* ---------------------- static assets (prod) ----------------------- */

if (existsSync(DIST_DIR)) {
  app.use(express.static(DIST_DIR, { index: false, maxAge: "1h" }));
  app.get("*", (_req, res) => {
    res.sendFile(path.join(DIST_DIR, "index.html"));
  });
} else {
  app.get("/", (_req, res) => {
    res.type("text/plain").send(
      "presenter/dist not found. Run `npm run build` in presenter/, or start the Vite dev server with `npm run dev:web` on port 4001."
    );
  });
}

/* ----------------------------- boot -------------------------------- */

function startOnPort(port, attemptsLeft = 20) {
  const server = createServer(app);
  server.on("error", (err) => {
    if (err.code === "EADDRINUSE" && attemptsLeft > 0) {
      startOnPort(port + 1, attemptsLeft - 1);
    } else {
      console.error("[presenter] fatal:", err);
      process.exit(1);
    }
  });
  server.listen(port, "127.0.0.1", () => {
    const url = `http://localhost:${port}`;
    console.log(`[presenter] serving ${url}`);
    // Stable marker other processes can read
    fs
      .mkdir(STATUS_DIR, { recursive: true })
      .then(() =>
        fs.writeFile(path.join(STATUS_DIR, "presenter.json"), JSON.stringify({ url, port }), "utf8")
      )
      .catch(() => {});
  });

  process.on("SIGINT", () => {
    server.close(() => process.exit(0));
  });
  process.on("SIGTERM", () => {
    server.close(() => process.exit(0));
  });
}

function ensureScheme(url) {
  if (/^https?:\/\//i.test(url)) return url;
  return `https://${url}`;
}

startWatcher();
startOnPort(Number(process.env.PORT) || 4000);
