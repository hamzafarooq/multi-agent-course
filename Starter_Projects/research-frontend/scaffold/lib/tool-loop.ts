import { ragSearch } from "./rag";
import { navigate, clickByText, screenshot } from "./playwright";
import { appendFact } from "./memory";

export type ToolUse = { name: string; input: Record<string, unknown> };

export type ToolResult = {
  text: string;
  /** Raw base64 PNG (no data: prefix) when the tool produced a screenshot. */
  imageBase64?: string;
};

export async function executeToolUse(tool: ToolUse): Promise<ToolResult> {
  try {
    switch (tool.name) {
      case "rag_search": {
        const { query, limit } = tool.input as { query: string; limit?: number };
        const chunks = await ragSearch(query, limit ?? 3);
        return {
          text: chunks
            .map((c) => `## ${c.source} — ${c.heading}\n${c.content}`)
            .join("\n\n---\n\n") || "(no matching chunks)",
        };
      }
      case "browser_navigate": {
        const { url } = tool.input as { url: string };
        return { text: await navigate(url) };
      }
      case "browser_click": {
        const { text } = tool.input as { text: string };
        return { text: await clickByText(text) };
      }
      case "browser_screenshot": {
        // playwright.screenshot() returns "data:image/png;base64,<raw>"
        const dataUrl = await screenshot();
        const imageBase64 = dataUrl.replace(/^data:image\/png;base64,/, "");
        return {
          text: "Screenshot captured. The PNG is attached as an image block.",
          imageBase64,
        };
      }
      case "remember_fact": {
        const { fact } = tool.input as { fact: string };
        await appendFact(fact);
        return { text: `Persisted: ${fact}` };
      }
      default:
        return { text: `Unknown tool: ${tool.name}` };
    }
  } catch (err) {
    return { text: `Tool error: ${err instanceof Error ? err.message : String(err)}` };
  }
}

export function formatTrace(name: string, input: Record<string, unknown>): string {
  const args = Object.entries(input)
    .map(([k, v]) => `${k}=${JSON.stringify(v).slice(0, 80)}`)
    .join(", ");
  return `🔧 <strong>${name}</strong>(${args})`;
}
