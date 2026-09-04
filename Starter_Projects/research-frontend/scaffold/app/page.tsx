"use client";

import { useEffect, useState } from "react";
import { ChatPane, type ChatMessage } from "@/components/ChatPane";
import { MemoryPanel } from "@/components/MemoryPanel";

type Mode = "llm" | "tools" | "memory";

const TABS: { id: Mode; label: string; hint: string; banner: string; tone: "warn" | "ok" }[] = [
  {
    id: "llm",
    label: "LLM",
    hint: "no tools, no memory",
    banner:
      "⚠️ No tools, no memory. Answers come only from the LLM's training data (cutoff ~early 2025). No web access, no corpus retrieval, no source citations possible.",
    tone: "warn",
  },
  {
    id: "tools",
    label: "+ Tools",
    hint: "rag + web + browser",
    banner:
      "✓ Tools enabled: rag_search (5-doc corpus), web_search (Anthropic live search), browser_* (Playwright). The model chooses which tool to call.",
    tone: "ok",
  },
  {
    id: "memory",
    label: "+ Tools + Memory",
    hint: "memory + skill + remember_fact",
    banner:
      "✓ Tools + Memory: everything from the Tools tab, plus the system prompt loads memory/CLAUDE.md and skills/research/SKILL.md every turn. The remember_fact tool persists user context.",
    tone: "ok",
  },
];

export default function Home() {
  const [active, setActive] = useState<Mode>("llm");
  const [histories, setHistories] = useState<Record<Mode, ChatMessage[]>>({
    llm: [], tools: [], memory: [],
  });
  const [loading, setLoading] = useState(false);
  const [mem, setMem] = useState({ claudeMd: "", skillMd: "" });

  const activeTab = TABS.find((t) => t.id === active)!;

  async function refreshMemory() {
    try {
      const res = await fetch("/api/memory");
      if (res.ok) setMem(await res.json());
    } catch {}
  }

  useEffect(() => {
    if (active === "memory") refreshMemory();
  }, [active]);

  async function handleSend(text: string) {
    const next = [...histories[active], { role: "user", content: text } as ChatMessage];
    setHistories({ ...histories, [active]: next });
    setLoading(true);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: active, messages: next }),
      });
      const data = await res.json();
      const reply: ChatMessage = {
        role: "assistant",
        content: data.content ?? "(no reply)",
        traces: data.traces,
      };
      setHistories((h) => ({ ...h, [active]: [...next, reply] }));
      if (active === "memory") refreshMemory();
    } catch (err) {
      setHistories((h) => ({
        ...h,
        [active]: [...next, { role: "assistant", content: `Error: ${(err as Error).message}` }],
      }));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-screen-2xl p-8">
      <header className="mb-6 flex items-center gap-3">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-orange font-bold text-white">✻</div>
        <h1 className="text-base font-semibold">Competitor Research Agent — Agentic AI PM Course</h1>
      </header>

      <div className="rounded-2xl border border-line bg-white shadow-sm">
        <div className="flex border-b border-line px-5">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setActive(t.id)}
              className={
                "flex flex-col items-start border-b-2 px-4 py-2 text-left transition " +
                (active === t.id
                  ? "border-orange text-ink"
                  : "border-transparent text-ink-3 hover:text-ink-2")
              }
            >
              <span className={"text-sm " + (active === t.id ? "font-semibold" : "")}>{t.label}</span>
              <span className="text-[10px] text-ink-3">{t.hint}</span>
            </button>
          ))}
        </div>

        <div
          className={
            "px-6 py-3 text-xs leading-relaxed " +
            (activeTab.tone === "warn"
              ? "border-b border-orange-border bg-orange-soft text-ink-2"
              : "border-b border-line bg-[#fafafa] text-ink-2")
          }
        >
          {activeTab.banner}
        </div>

        <div
          className={
            "h-[600px] " +
            (active === "memory" ? "grid grid-cols-[1fr_280px]" : "flex")
          }
        >
          <div className="flex flex-1 flex-col p-6">
            <ChatPane
              messages={histories[active]}
              loading={loading}
              onSend={handleSend}
            />
          </div>
          {active === "memory" && <MemoryPanel claudeMd={mem.claudeMd} skillMd={mem.skillMd} />}
        </div>
      </div>
    </main>
  );
}
