import type Anthropic from "@anthropic-ai/sdk";
import { getAnthropic, MODEL } from "@/lib/anthropic";
import type { ChatMessage } from "@/components/ChatPane";
import { buildStickies } from "@/lib/stickies";

const SYSTEM = `You are a helpful research assistant. You have NO tools and NO persistent memory. Your only context is the conversation transcript you are given this turn — earlier messages are present only because they are replayed to you. Answer naturally using that transcript. If asked something only knowable from earlier in this conversation, use the transcript; if it is not in the transcript, say you don't have it.`;

export async function runShortTerm(messages: ChatMessage[], apiKey?: string) {
  const anthropic = getAnthropic(apiKey);
  const response = await anthropic.messages.create({
    model: MODEL,
    max_tokens: 1024,
    system: SYSTEM,
    // Short-term memory: the ENTIRE transcript is replayed every turn.
    messages: messages.map((m) => ({ role: m.role, content: m.content })),
  });

  const text = response.content
    .filter((b): b is Anthropic.TextBlock => b.type === "text")
    .map((b) => b.text)
    .join("\n");

  return { content: text, traces: [], stickies: buildStickies({ mode: "short-term" }) };
}
