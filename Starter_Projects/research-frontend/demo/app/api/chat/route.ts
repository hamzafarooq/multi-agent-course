import { NextRequest, NextResponse } from "next/server";
import { runLlmOnly } from "./modes/llm-only";
import { runLlmTools } from "./modes/llm-tools";
import { runLlmToolsMemory } from "./modes/llm-tools-memory";
import { runShortTerm } from "./modes/short-term";
import { runLongTerm } from "./modes/long-term";

export const runtime = "nodejs";

export async function POST(req: NextRequest) {
  const { mode, messages, apiKey } = await req.json();
  try {
    switch (mode) {
      case "llm":
        return NextResponse.json(await runLlmOnly(messages, apiKey));
      case "short-term":
        return NextResponse.json(await runShortTerm(messages, apiKey));
      case "long-term":
        return NextResponse.json(await runLongTerm(messages, apiKey));
      case "tools":
        return NextResponse.json(await runLlmTools(messages, apiKey));
      case "memory":
        return NextResponse.json(await runLlmToolsMemory(messages, apiKey));
      default:
        return NextResponse.json({ error: `Unknown mode: ${mode}` }, { status: 400 });
    }
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}
