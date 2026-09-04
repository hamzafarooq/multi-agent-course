"use client";

import { useState } from "react";

export type Mode = "llm" | "short-term" | "long-term" | "tools" | "memory";

const ROWS: { mode: Mode; label: string }[] = [
  { mode: "llm", label: "LLM" },
  { mode: "short-term", label: "+ Short-term" },
  { mode: "long-term", label: "+ Long-term" },
  { mode: "tools", label: "+ Tools" },
  { mode: "memory", label: "+ Tools + Memory" },
];

const BEHAVIOR: Record<Mode, [string, string, string, string]> = {
  llm:          ["current message only", "none", "❌", "❌"],
  "short-term": ["full transcript replayed in messages[]", "volatile session state", "❌", "❌"],
  "long-term":  ["current message + facts in system prompt (no transcript)", "memory/CLAUDE.md", "✅", "❌"],
  tools:        ["current message + tool results", "none", "❌", "✅"],
  memory:       ["facts + SKILL in system prompt + tool results", "CLAUDE.md + SKILL.md", "✅", "✅"],
};

const CAPS: Record<Mode, [string, string, string, string, string, string, string]> = {
  //          history  CLAUDE.md  rag    web    browser  SKILL  remember_fact
  llm:          ["—", "—", "—", "—", "—", "—", "—"],
  "short-term": ["✅", "—", "—", "—", "—", "—", "—"],
  "long-term":  ["—", "✅", "—", "—", "—", "—", "✅"],
  tools:        ["—", "—", "✅", "✅", "✅", "—", "—"],
  memory:       ["—", "✅", "✅", "✅", "✅", "✅", "✅"],
};

const BEHAVIOR_COLS = ["Layer", "What's sent to the model", "Memory store", "Survives 🔄 new session", "Grounded / can cite"];
const CAPS_COLS = ["Layer", "msg history", "CLAUDE.md", "rag_search", "web_search", "browser_*", "SKILL.md", "remember_fact"];

export function LessonPanel({ active, defaultOpen }: { active: Mode; defaultOpen: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  const [view, setView] = useState<"behavior" | "capabilities">("behavior");

  const cols = view === "behavior" ? BEHAVIOR_COLS : CAPS_COLS;

  return (
    <div className="border-b border-line bg-[#fafafa] px-6 py-3">
      <div className="flex items-center gap-3">
        <button
          onClick={() => setOpen((o) => !o)}
          className="text-xs font-semibold text-ink-2 hover:text-ink"
        >
          {open ? "▾" : "▸"} Lesson — short-term vs long-term memory
        </button>
        {open && (
          <div className="ml-auto flex gap-1 text-[11px]">
            {(["behavior", "capabilities"] as const).map((v) => (
              <button
                key={v}
                onClick={() => setView(v)}
                className={
                  "rounded-md border px-2 py-0.5 capitalize " +
                  (view === v
                    ? "border-orange bg-orange-soft text-ink"
                    : "border-line text-ink-3 hover:text-ink-2")
                }
              >
                {v}
              </button>
            ))}
          </div>
        )}
      </div>

      {open && (
        <div className="mt-2 overflow-x-auto">
          <table className="w-full border-collapse text-[11px] leading-snug">
            <thead>
              <tr className="bg-white">
                {cols.map((c) => (
                  <th key={c} className="border border-line px-2 py-1 text-left font-semibold text-ink-2">
                    {c}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {ROWS.map(({ mode, label }) => {
                const cells = view === "behavior" ? BEHAVIOR[mode] : CAPS[mode];
                const isActive = mode === active;
                return (
                  <tr
                    key={mode}
                    className={isActive ? "bg-orange-soft font-semibold" : "bg-white"}
                  >
                    <td className="border border-line px-2 py-1">{label}</td>
                    {cells.map((cell, i) => (
                      <td key={i} className="border border-line px-2 py-1 text-ink-2">
                        {cell}
                      </td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
