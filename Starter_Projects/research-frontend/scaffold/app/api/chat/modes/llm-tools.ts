import type { ChatMessage } from "@/components/ChatPane";

export async function runLlmTools(_messages: ChatMessage[]) {
  // TODO Exercise 2 — Tools
  // 1. Implement lib/rag.ts (see its TODO) so rag_search has something to call
  // 2. Loop: call anthropic.messages.create with tools from "@/lib/tools",
  //    if stop_reason === "tool_use", execute each tool_use block via
  //    executeToolUse in "@/lib/tool-loop", append tool_results, loop.
  // 3. Stop when stop_reason !== "tool_use" or after MAX_ITERATIONS.
  // 4. Return { content, traces } — traces are formatted via formatTrace.
  return { content: "(unimplemented — see Exercise 2)", traces: [] };
}
