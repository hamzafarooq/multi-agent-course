import type { ChatMessage } from "@/components/ChatPane";

export async function runLlmOnly(_messages: ChatMessage[]) {
  // TODO Exercise 1 — Warm-up
  // Call the Anthropic Messages API with no tools and no memory.
  // Use the shared client from "@/lib/anthropic" and the MODEL constant.
  // Hint: model, max_tokens, system, messages.
  // Return shape: { content: string, traces: string[] }
  return { content: "(unimplemented — see Exercise 1)", traces: [] };
}
