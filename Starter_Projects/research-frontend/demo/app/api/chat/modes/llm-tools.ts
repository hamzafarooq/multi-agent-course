import { getAnthropic, MODEL } from "@/lib/anthropic";
import { toolsForToolsMode } from "@/lib/tools";
import { executeToolUse, formatTrace } from "@/lib/tool-loop";
import { buildStickies, type ObservedToolCall } from "@/lib/stickies";
import type Anthropic from "@anthropic-ai/sdk";
import type { ChatMessage } from "@/components/ChatPane";

const MAX_ITERATIONS = 6;

const SYSTEM = `You are a research assistant. Use tools to ground every claim in real data.

Tool priority:
- rag_search first — the local corpus is curated; try it before anything else.
- web_search when the corpus is silent on the topic (no relevant chunks).
- browser_navigate / browser_click / browser_screenshot only when you need stateful UI, JS-rendered content, or to show the user what a page looks like.

If rag_search returns nothing relevant, say "the corpus is silent on this" briefly, then fall back to web_search. Never invent facts.`;

export async function runLlmTools(messages: ChatMessage[], apiKey?: string) {
  const anthropic = getAnthropic(apiKey);
  const traces: string[] = [];
  const toolCalls: ObservedToolCall[] = [];
  let webSearchUsed = false;
  // Stateless: only the latest user message seeds the loop — no prior turns.
  // The within-turn tool loop still appends assistant/tool_result blocks below.
  const apiMessages: Anthropic.MessageParam[] = [
    { role: "user", content: messages[messages.length - 1]?.content ?? "" },
  ];

  for (let i = 0; i < MAX_ITERATIONS; i++) {
    const response = await anthropic.messages.create({
      model: MODEL,
      max_tokens: 2048,
      system: SYSTEM,
      tools: toolsForToolsMode as Anthropic.ToolUnion[],
      messages: apiMessages,
    });

    for (const block of response.content) {
      if ((block as { type: string }).type === "server_tool_use" && (block as { name?: string }).name === "web_search") {
        webSearchUsed = true;
      }
    }

    if (response.stop_reason !== "tool_use") {
      const text = response.content
        .filter((b): b is Anthropic.TextBlock => b.type === "text")
        .map((b) => b.text)
        .join("\n");
      return {
        content: text,
        traces,
        stickies: buildStickies({ mode: "tools", toolCalls, webSearchUsed }),
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

      let trace = formatTrace(block.name, block.input as Record<string, unknown>);
      let toolContent: Anthropic.ToolResultBlockParam["content"];

      if (result.imageBase64) {
        // Pass the PNG to the model as a proper image block and surface it in the trace.
        toolContent = [
          {
            type: "image",
            source: {
              type: "base64",
              media_type: "image/png",
              data: result.imageBase64,
            },
          },
          { type: "text", text: result.text },
        ];
        trace += `<br/><img src="data:image/png;base64,${result.imageBase64}" alt="screenshot" style="max-width:100%;margin-top:6px;border-radius:6px;border:1px solid #ececec" />`;
      } else {
        toolContent = result.text.slice(0, 6000);
      }

      traces.push(trace);
      toolResults.push({
        type: "tool_result",
        tool_use_id: block.id,
        content: toolContent,
      });
    }

    apiMessages.push({ role: "user", content: toolResults });
  }

  return {
    content: "(stopped after max tool iterations)",
    traces,
    stickies: buildStickies({ mode: "tools", toolCalls, webSearchUsed }),
  };
}
