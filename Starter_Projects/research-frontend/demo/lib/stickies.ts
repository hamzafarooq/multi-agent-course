export type StickyKind = "llm-only" | "tool" | "memory" | "skill" | "remember" | "short-term";

export type Sticky = {
  kind: StickyKind;
  label: string;
  detail: string;
};

export type ObservedToolCall = {
  name: string;
  input: Record<string, unknown>;
};

export type BuildStickiesInput = {
  mode: "llm" | "short-term" | "long-term" | "tools" | "memory";
  toolCalls?: ObservedToolCall[];
  webSearchUsed?: boolean;
};

const LLM_ONLY: Sticky = {
  kind: "llm-only",
  label: "LLM only",
  detail:
    "No tools called, no memory read. Answer is from training data (cutoff ~early 2025) — no citations possible.",
};

const NO_TOOLS_NEEDED: Sticky = {
  kind: "llm-only",
  label: "No tools needed",
  detail: "The model answered from training data alone — it didn't call rag_search, web_search, or browser_*.",
};

const CLAUDE_MD: Sticky = {
  kind: "memory",
  label: "CLAUDE.md loaded",
  detail: "memory/CLAUDE.md injected into the system prompt every turn (always-on user context).",
};

const SKILL_LOADED: Sticky = {
  kind: "skill",
  label: "SKILL loaded",
  detail: "skills/research/SKILL.md injected into the system prompt — the model follows its procedure.",
};

// lib/stickies.test.ts asserts the word "transcript" appears in `detail` — wording is load-bearing.
const SHORT_TERM: Sticky = {
  kind: "short-term",
  label: "Short-term memory",
  detail:
    "The full conversation transcript is replayed in messages[] every turn. Volatile — a new session wipes it. No persisted store, no tools.",
};

function toolSticky(name: string, count: number, sample: ObservedToolCall): Sticky {
  const times = count > 1 ? ` (${count}×)` : "";
  switch (name) {
    case "rag_search": {
      const q = String(sample.input.query ?? "");
      return {
        kind: "tool",
        label: "rag_search",
        detail: `Searched the local corpus${times}${q ? `: "${q}"` : ""}.`,
      };
    }
    case "browser_navigate": {
      const url = String(sample.input.url ?? "");
      return {
        kind: "tool",
        label: "browser_navigate",
        detail: `Loaded ${url}${times} in a headless browser.`,
      };
    }
    case "browser_click": {
      const text = String(sample.input.text ?? "");
      return {
        kind: "tool",
        label: "browser_click",
        detail: `Clicked "${text}"${times} on the current page.`,
      };
    }
    case "browser_screenshot":
      return {
        kind: "tool",
        label: "browser_screenshot",
        detail: `Captured a screenshot${times} of the current page.`,
      };
    default:
      return {
        kind: "tool",
        label: name,
        detail: `Called ${name}${times}.`,
      };
  }
}

export function buildStickies(input: BuildStickiesInput): Sticky[] {
  if (input.mode === "llm") return [LLM_ONLY];
  if (input.mode === "short-term") return [SHORT_TERM];

  // long-term: only CLAUDE.md + remember_fact chips — tool/skill chips are never emitted.
  if (input.mode === "long-term") {
    const out: Sticky[] = [CLAUDE_MD];
    for (const c of input.toolCalls ?? []) {
      if (c.name !== "remember_fact") continue;
      out.push({
        kind: "remember",
        label: "remember_fact",
        detail: `Saved to memory/CLAUDE.md: "${String(c.input.fact ?? "")}"`,
      });
    }
    return out;
  }

  const calls = input.toolCalls ?? [];
  const grouped = new Map<string, ObservedToolCall[]>();
  for (const c of calls) {
    if (!grouped.has(c.name)) grouped.set(c.name, []);
    grouped.get(c.name)!.push(c);
  }

  const tool: Sticky[] = [];
  for (const [name, group] of grouped) {
    if (name === "remember_fact") continue;
    tool.push(toolSticky(name, group.length, group[0]));
  }
  if (input.webSearchUsed) {
    tool.push({
      kind: "tool",
      label: "web_search",
      detail: "Anthropic's hosted web search ran server-side and grounded the answer in live results.",
    });
  }

  if (input.mode === "tools") {
    if (tool.length === 0) return [NO_TOOLS_NEEDED];
    return tool;
  }

  const memory: Sticky[] = [CLAUDE_MD, SKILL_LOADED];
  const remembers = grouped.get("remember_fact") ?? [];
  for (const r of remembers) {
    const fact = String(r.input.fact ?? "");
    memory.push({
      kind: "remember",
      label: "remember_fact",
      detail: `Saved to memory/CLAUDE.md: "${fact}"`,
    });
  }

  return [...memory, ...tool];
}
