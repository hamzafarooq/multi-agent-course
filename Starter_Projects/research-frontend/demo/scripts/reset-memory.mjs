// Reset long-term memory for a fresh demo.
//
// Clears ONLY the "## Known facts" bullets in memory/CLAUDE.md.
// It does NOT touch the corpus/ datasets, lib/rag.ts, or anything RAG —
// retrieval data is intentionally left exactly as-is.
//
// Usage:  npm run reset:memory   (run from research-frontend/demo)

import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";

// Same path lib/memory.ts uses (cwd = package.json dir under npm run).
const FILE = path.join(process.cwd(), "memory/CLAUDE.md");
const FACTS_MARKER = "## Known facts";
const EMPTY_BODY = "\n\n_(this section grows over the conversation)_\n";

const current = await readFile(FILE, "utf-8");
const idx = current.indexOf(FACTS_MARKER);

if (idx === -1) {
  console.error(
    `reset:memory — could not find "${FACTS_MARKER}" in ${FILE}. ` +
      `Aborting so nothing is destroyed.`,
  );
  process.exit(1);
}

// Keep everything up to and including the heading; replace the rest.
const before = current.slice(0, idx + FACTS_MARKER.length);
await writeFile(FILE, `${before}${EMPTY_BODY}`, "utf-8");

console.log("reset:memory — Known facts cleared. RAG corpus untouched.");
