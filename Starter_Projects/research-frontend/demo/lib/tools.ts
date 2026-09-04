import type Anthropic from "@anthropic-ai/sdk";

export const ragSearchTool: Anthropic.Tool = {
  name: "rag_search",
  description:
    "Search the local Wispr Flow / dictation-space corpus for relevant chunks. Use FIRST for any question about known competitors or their positioning, pricing, weaknesses.",
  input_schema: {
    type: "object",
    properties: {
      query: { type: "string", description: "Natural-language query." },
      limit: { type: "number", description: "Max chunks to return (default 3)." },
    },
    required: ["query"],
  },
};

export const webSearchTool = {
  type: "web_search_20250305" as const,
  name: "web_search",
  max_uses: 5,
};

export const browserNavigateTool: Anthropic.Tool = {
  name: "browser_navigate",
  description:
    "Open a URL in a headless browser and return its text content. Use when you need fresh data, JS-rendered pages, or content not in the corpus.",
  input_schema: {
    type: "object",
    properties: { url: { type: "string" } },
    required: ["url"],
  },
};

export const browserScreenshotTool: Anthropic.Tool = {
  name: "browser_screenshot",
  description: "Take a screenshot of the most recently navigated page. Returns a data URL.",
  input_schema: { type: "object", properties: {} },
};

export const browserClickTool: Anthropic.Tool = {
  name: "browser_click",
  description: "Click an element by visible text on the current page, then return updated content.",
  input_schema: {
    type: "object",
    properties: { text: { type: "string", description: "Visible text of the target element." } },
    required: ["text"],
  },
};

export const rememberFactTool: Anthropic.Tool = {
  name: "remember_fact",
  description:
    "Persist a single short sentence to memory/CLAUDE.md when the user reveals something durable about their research focus, constraints, or strategic angle. Follow the persistence rules in CLAUDE.md. Do NOT use for small talk or query phrasing.",
  input_schema: {
    type: "object",
    properties: { fact: { type: "string", description: "One sentence to persist." } },
    required: ["fact"],
  },
};

export const toolsForToolsMode: (Anthropic.Tool | typeof webSearchTool)[] = [
  ragSearchTool,
  webSearchTool,
  browserNavigateTool,
  browserScreenshotTool,
  browserClickTool,
];

export const toolsForMemoryMode = [...toolsForToolsMode, rememberFactTool];

export const toolsForLongTermMode = [rememberFactTool];
