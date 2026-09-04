import { getAnthropic, MODEL } from "@/lib/anthropic";
import { toolsForLongTermMode } from "@/lib/tools";
import { executeToolUse, formatTrace } from "@/lib/tool-loop";
import { readMemory } from "@/lib/memory";
import { buildStickies, type ObservedToolCall } from "@/lib/stickies";
import type Anthropic from "@anthropic-ai/sdk";
import type { ChatMessage } from "@/components/ChatPane";

// Only remember_fact is available here, so a short loop is plenty (the capstone uses 6 for multi-tool research).
const MAX_ITERATIONS = 4;

export async function runLongTerm(messages: ChatMessage[], apiKey?: string) {
  const anthropic = getAnthropic(apiKey);
  const claudeMd = await readMemory();

  const system = [
    `You are a research assistant with LONG-TERM MEMORY but NO conversation history and NO research tools.`,
    `You cannot see earlier turns — treat each message as the start of a fresh session.`,
    `Your only durable context is <user_context> below, which is loaded from memory/CLAUDE.md on EVERY request.`,
    ``,
    `Rules:`,
    `1. Read <user_context> first and use it to answer (e.g. the user's name, what they research).`,
    `2. The instant the user states something durable about themselves or their work, call \`remember_fact\` once with a single short sentence so it survives future sessions.`,
    `3. You have no rag_search/web_search/browser tools. Do not claim to.`,
    ``,
    `--- USER CONTEXT (persistent memory) ---`,
    `<user_context>`,
    claudeMd.trim(),
    `</user_context>`,
  ].join("\n");

  const traces: string[] = [];
  const toolCalls: ObservedToolCall[] = [];

  // Stateless on the transcript: only the latest user message seeds the loop.
  const apiMessages: Anthropic.MessageParam[] = [
    { role: "user", content: messages[messages.length - 1]?.content ?? "" },
  ];

  for (let i = 0; i < MAX_ITERATIONS; i++) {
    const response = await anthropic.messages.create({
      model: MODEL,
      max_tokens: 1536,
      system,
      tools: toolsForLongTermMode as Anthropic.ToolUnion[],
      messages: apiMessages,
    });

    if (response.stop_reason !== "tool_use") {
      const text = response.content
        .filter((b): b is Anthropic.TextBlock => b.type === "text")
        .map((b) => b.text)
        .join("\n");
      return {
        content: text,
        traces,
        stickies: buildStickies({ mode: "long-term", toolCalls }),
      };
    }

    apiMessages.push({ role: "assistant", content: response.content });

    const toolResults: Anthropic.ToolResultBlockParam[] = [];
    for (const block of response.content) {
      if (block.type !== "tool_use") continue;
      toolCalls.push({
        name: block.name,
        input: block.input as Record<string, unknown>,
      });
      const result = await executeToolUse({
        name: block.name,
        input: block.input as Record<string, unknown>,
      });
      traces.push(formatTrace(block.name, block.input as Record<string, unknown>));
      toolResults.push({
        type: "tool_result",
        tool_use_id: block.id,
        // remember_fact returns a short string; no image branch needed (this mode has no browser tools).
        content: result.text.slice(0, 4000),
      });
    }

    apiMessages.push({ role: "user", content: toolResults });
  }

  return {
    content: "(stopped after max tool iterations)",
    traces,
    stickies: buildStickies({ mode: "long-term", toolCalls }),
  };
}
