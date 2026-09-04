import type Anthropic from "@anthropic-ai/sdk";
import { getAnthropic, MODEL } from "@/lib/anthropic";
import type { ChatMessage } from "@/components/ChatPane";
import { buildStickies } from "@/lib/stickies";

export async function runLlmOnly(messages: ChatMessage[], apiKey?: string) {
  const anthropic = getAnthropic(apiKey);
  const response = await anthropic.messages.create({
    model: MODEL,
    max_tokens: 1024,
    system: `You are a research assistant with NO access to tools — no web search, no document retrieval, no memory, no current data. Your only source is your training knowledge (cutoff: early 2025).

For any question requiring fresh or specific information, START your reply with the limitation, then give the best partial answer you can. Example openings:
- "I can't access the web, so I can't verify current pricing. From my training data (early 2025)..."
- "I don't have a reliable source for this — here's what I recall, but treat it as fuzzy..."
- "I have no way to cite sources in this layer, so..."

Be honest about limits **up front**. Don't bury caveats at the end. After the honest opener, give the most useful answer you can from training data alone.`,
    // Stateless: only the latest user message reaches the model — no prior turns.
    messages: [
      {
        role: "user",
        content: messages[messages.length - 1]?.content ?? "",
      },
    ],
  });

  const text = response.content
    .filter((block): block is Anthropic.TextBlock => block.type === "text")
    .map((b) => b.text)
    .join("\n");

  return { content: text, traces: [], stickies: buildStickies({ mode: "llm" }) };
}
