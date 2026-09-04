"use client";

import { useEffect, useState } from "react";
import { ChatPane, type ChatMessage } from "@/components/ChatPane";
import { MemoryPanel } from "@/components/MemoryPanel";
import { LessonPanel, type Mode } from "@/components/LessonPanel";

const TABS: { id: Mode; label: string; hint: string; banner: string; tone: "warn" | "ok"; lessonOpen: boolean }[] = [
  {
    id: "llm",
    label: "LLM",
    hint: "no memory, no tools",
    banner:
      "⚠️ Stateless. Only the current message reaches the model — no prior turns, no tools, no persisted memory. Ask it something from earlier and it won't know.",
    tone: "warn",
    lessonOpen: true,
  },
  {
    id: "short-term",
    label: "+ Short-term",
    hint: "in-context transcript",
    banner:
      "💬 Short-term memory: the entire conversation transcript is replayed every turn. It remembers within this session — but press 🔄 New session and it forgets everything. No tools, no persisted store.",
    tone: "ok",
    lessonOpen: true,
  },
  {
    id: "long-term",
    label: "+ Long-term",
    hint: "persistent CLAUDE.md",
    banner:
      "✅ Long-term memory: no transcript is replayed, but memory/CLAUDE.md is injected into the system prompt every request. remember_fact writes durable facts. Press 🔄 New session — it still knows you, from disk.",
    tone: "ok",
    lessonOpen: true,
  },
  {
    id: "tools",
    label: "+ Tools",
    hint: "rag + web + browser",
    banner:
      "✓ Tools enabled (stateless): rag_search, web_search, browser_*. Grounded answers — but no memory of who you are or earlier turns.",
    tone: "ok",
    lessonOpen: false,
  },
  {
    id: "memory",
    label: "+ Tools + Memory",
    hint: "memory + skill + remember_fact",
    banner:
      "✓ Tools + Memory: everything from the Tools tab, plus the system prompt loads memory/CLAUDE.md and skills/research/SKILL.md every turn. The remember_fact tool persists user context.",
    tone: "ok",
    lessonOpen: false,
  },
];

const EMPTY_HISTORIES: Record<Mode, ChatMessage[]> = {
  llm: [], "short-term": [], "long-term": [], tools: [], memory: [],
};

export default function Home() {
  const [active, setActive] = useState<Mode>("llm");
  const [histories, setHistories] = useState<Record<Mode, ChatMessage[]>>(EMPTY_HISTORIES);
  const [loading, setLoading] = useState(false);
  const [mem, setMem] = useState({ claudeMd: "", skillMd: "" });
  const [apiKey, setApiKey] = useState("");

  // Restore a previously entered key from this browser.
  useEffect(() => {
    const saved = localStorage.getItem("anthropic_api_key");
    if (saved) setApiKey(saved);
  }, []);

  function updateApiKey(value: string) {
    setApiKey(value);
    if (value.trim()) localStorage.setItem("anthropic_api_key", value.trim());
    else localStorage.removeItem("anthropic_api_key");
  }

  const activeTab = TABS.find((t) => t.id === active)!;
  const showPanel = active === "long-term" || active === "memory";

  async function refreshMemory() {
    try {
      const res = await fetch("/api/memory");
      if (res.ok) setMem(await res.json());
    } catch {}
  }

  useEffect(() => {
    if (showPanel) refreshMemory();
    // showPanel is derived from active; refreshMemory is stable in practice
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active]);

  function newSession() {
    setHistories((h) => ({ ...h, [active]: [] }));
  }

  async function handleSend(text: string) {
    const next = [...histories[active], { role: "user", content: text } as ChatMessage];
    setHistories({ ...histories, [active]: next });
    setLoading(true);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: active, messages: next, apiKey }),
      });
      const data = await res.json();
      const reply: ChatMessage = {
        role: "assistant",
        content: data.content ?? "(no reply)",
        traces: data.traces,
        stickies: data.stickies,
      };
      setHistories((h) => ({ ...h, [active]: [...next, reply] }));
      if (showPanel) refreshMemory();
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
        <div className="ml-auto flex items-center gap-2">
          <input
            type="password"
            value={apiKey}
            onChange={(e) => updateApiKey(e.target.value)}
            placeholder="Anthropic API key (sk-ant-…)"
            spellCheck={false}
            autoComplete="off"
            className="w-72 rounded-md border border-line bg-white px-3 py-1.5 text-xs text-ink placeholder:text-ink-3 focus:border-orange focus:outline-none"
          />
          <span className={"text-[10px] " + (apiKey.trim() ? "text-ink-3" : "text-orange")}>
            {apiKey.trim() ? "key set" : "uses server key"}
          </span>
        </div>
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

        <LessonPanel key={active} active={active} defaultOpen={activeTab.lessonOpen} />

        <div
          className={
            "flex items-center gap-3 px-6 py-3 text-xs leading-relaxed " +
            (activeTab.tone === "warn"
              ? "border-b border-orange-border bg-orange-soft text-ink-2"
              : "border-b border-line bg-[#fafafa] text-ink-2")
          }
        >
          <span className="flex-1">{activeTab.banner}</span>
          <button
            onClick={newSession}
            className="shrink-0 rounded-md border border-line bg-white px-2.5 py-1 text-[11px] font-medium text-ink-2 hover:text-ink"
          >
            🔄 New session
          </button>
        </div>

        <div className={"h-[600px] " + (showPanel ? "grid grid-cols-[1fr_280px]" : "flex")}>
          <div className="flex flex-1 flex-col p-6">
            <ChatPane messages={histories[active]} loading={loading} onSend={handleSend} />
          </div>
          {showPanel && (
            <MemoryPanel
              claudeMd={mem.claudeMd}
              skillMd={mem.skillMd}
              showSkill={active === "memory"}
            />
          )}
        </div>
      </div>
    </main>
  );
}
