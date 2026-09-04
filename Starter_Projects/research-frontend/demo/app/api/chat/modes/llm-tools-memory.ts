import { getAnthropic, MODEL } from "@/lib/anthropic";
import { toolsForMemoryMode } from "@/lib/tools";
import { executeToolUse, formatTrace } from "@/lib/tool-loop";
import { readMemory, readSkill } from "@/lib/memory";
import { buildStickies, type ObservedToolCall } from "@/lib/stickies";
import type Anthropic from "@anthropic-ai/sdk";
import type { ChatMessage } from "@/components/ChatPane";

const MAX_ITERATIONS = 6;

export async function runLlmToolsMemory(messages: ChatMessage[], apiKey?: string) {
  const anthropic = getAnthropic(apiKey);
  const [claudeMd, skillMd] = await Promise.all([readMemory(), readSkill()]);

  // Detect "first turn of a new thread": the user has sent exactly one message
  // and the persistent memory has no Known facts yet. In that case, the model's
  // job is to ask the scope question — nothing else.
  const isFirstTurn = messages.filter((m) => m.role === "user").length === 1;
  const hasKnownFacts = /^##\s*Known facts\s*\n[\s\S]*?^\s*-\s+/m.test(claudeMd);
  const newThread = isFirstTurn && !hasKnownFacts;

  const operatingRules = newThread
    ? [
        `You are the assistant in the Memory tab. This is the FIRST TURN of a new research thread (Known facts is empty).`,
        ``,
        `MANDATORY behavior for this turn:`,
        `1. Do NOT call any tools — no rag_search, no web_search, no browser_*, no remember_fact.`,
        `2. Your entire response is a short scope-clarifying question (2-3 sub-questions about segment, target customer, and any constraint).`,
        `3. The user's message may already name a product — that is a starting point, not a full scope. Confirm before researching.`,
        `4. Follow SKILL Step 1 verbatim.`,
      ].join("\n")
    : [
        `You are the assistant in the Memory tab. Scope has been established (Known facts already has at least one bullet, or this is a follow-up turn).`,
        ``,
        `Operating rules:`,
        `1. ALWAYS read <user_context> below FIRST.`,
        `2. The instant the user reveals NEW durable info (segment refinement, strategic angle, constraint, decision), call \`remember_fact\` once.`,
        `3. Now proceed with research per the SKILL procedure: rag_search first (if relevant), web_search if the corpus is silent, browser_* only for stateful pages.`,
      ].join("\n");

  const system = [
    operatingRules,
    ``,
    `--- SKILL ---`,
    skillMd.trim(),
    ``,
    `--- USER CONTEXT (persistent memory) ---`,
    `<user_context>`,
    claudeMd.trim(),
    `</user_context>`,
  ].join("\n");

  const traces: string[] = [];
  const toolCalls: ObservedToolCall[] = [];
  let webSearchUsed = false;
  const apiMessages: Anthropic.MessageParam[] = messages.map((m) => ({
    role: m.role,
    content: m.content,
  }));

  for (let i = 0; i < MAX_ITERATIONS; i++) {
    const response = await anthropic.messages.create({
      model: MODEL,
      max_tokens: 2048,
      system,
      tools: toolsForMemoryMode as Anthropic.ToolUnion[],
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
        stickies: buildStickies({ mode: "memory", toolCalls, webSearchUsed }),
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
    stickies: buildStickies({ mode: "memory", toolCalls, webSearchUsed }),
  };
}
