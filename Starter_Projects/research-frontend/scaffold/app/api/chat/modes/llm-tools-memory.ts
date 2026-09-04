import type { ChatMessage } from "@/components/ChatPane";

export async function runLlmToolsMemory(_messages: ChatMessage[]) {
  // TODO Exercise 3 — Memory
  // Build on Exercise 2:
  // 1. Read memory/CLAUDE.md and skills/research/SKILL.md (see lib/memory.ts)
  // 2. Compose the system prompt: SKILL.md + <user_context>CLAUDE.md</user_context>
  // 3. Use toolsForMemoryMode (adds remember_fact) instead of toolsForToolsMode
  // 4. Same tool_use loop as Exercise 2
  return { content: "(unimplemented — see Exercise 3)", traces: [] };
}
