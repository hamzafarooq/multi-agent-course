import { NextRequest, NextResponse } from "next/server";
import { runLlmOnly } from "./modes/llm-only";
import { runLlmTools } from "./modes/llm-tools";
import { runLlmToolsMemory } from "./modes/llm-tools-memory";

export const runtime = "nodejs";

export async function POST(req: NextRequest) {
  const { mode, messages } = await req.json();
  try {
    switch (mode) {
      case "llm":
        return NextResponse.json(await runLlmOnly(messages));
      case "tools":
        return NextResponse.json(await runLlmTools(messages));
      case "memory":
        return NextResponse.json(await runLlmToolsMemory(messages));
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
