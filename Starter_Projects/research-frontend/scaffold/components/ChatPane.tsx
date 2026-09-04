"use client";

import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export type ChatMessage =
  | { role: "user"; content: string }
  | { role: "assistant"; content: string; traces?: string[] };

type Props = {
  messages: ChatMessage[];
  loading: boolean;
  onSend: (text: string) => void;
};

export function ChatPane({ messages, loading, onSend }: Props) {
  const [draft, setDraft] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  function autoResize() {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  }

  useEffect(autoResize, [draft]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  function submit(e?: FormEvent | KeyboardEvent) {
    e?.preventDefault();
    const text = draft.trim();
    if (!text || loading) return;
    onSend(text);
    setDraft("");
    setTimeout(autoResize, 0);
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      submit(e);
    }
  }

  return (
    <div className="flex h-full min-h-0 flex-1 flex-col">
      <div
        ref={scrollRef}
        className="flex-1 space-y-3 overflow-y-auto px-1"
      >
        {messages.map((m, i) =>
          m.role === "user" ? (
            <div
              key={i}
              className="ml-auto max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-md border border-orange-border bg-orange-soft px-4 py-2.5 text-sm leading-relaxed"
            >
              {m.content}
            </div>
          ) : (
            <div key={i} className="mr-auto max-w-[85%] space-y-2">
              {m.traces?.map((t, j) => (
                <div
                  key={j}
                  className="rounded-lg border border-dashed border-orange-border bg-[#fffaf4] px-3 py-2 font-mono text-xs leading-relaxed text-ink-2"
                  dangerouslySetInnerHTML={{ __html: t }}
                />
              ))}
              <div className="prose prose-sm max-w-none rounded-2xl rounded-bl-md border border-line bg-white px-4 py-2.5 text-sm leading-relaxed [&_h1]:mb-2 [&_h1]:mt-3 [&_h1]:text-base [&_h1]:font-semibold [&_h2]:mb-2 [&_h2]:mt-3 [&_h2]:text-sm [&_h2]:font-semibold [&_h3]:mb-1.5 [&_h3]:mt-2.5 [&_h3]:text-sm [&_h3]:font-semibold [&_p]:my-1.5 [&_ul]:my-1.5 [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:my-1.5 [&_ol]:list-decimal [&_ol]:pl-5 [&_li]:my-0.5 [&_code]:rounded [&_code]:bg-orange-soft [&_code]:px-1 [&_code]:py-0.5 [&_code]:text-[12px] [&_table]:my-2 [&_table]:w-full [&_table]:border-collapse [&_th]:border [&_th]:border-line [&_th]:bg-[#fafafa] [&_th]:px-2 [&_th]:py-1 [&_th]:text-left [&_td]:border [&_td]:border-line [&_td]:px-2 [&_td]:py-1 [&_strong]:font-semibold">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.content}</ReactMarkdown>
              </div>
            </div>
          ),
        )}
        {loading && (
          <div className="mr-auto inline-flex items-center gap-1 rounded-2xl rounded-bl-md border border-line bg-white px-3 py-2 text-sm text-ink-3">
            <span className="animate-pulse">●</span>
            <span className="animate-pulse [animation-delay:0.2s]">●</span>
            <span className="animate-pulse [animation-delay:0.4s]">●</span>
          </div>
        )}
      </div>

      <form
        onSubmit={submit}
        className="mt-4 flex items-end gap-2 border-t border-line pt-3"
      >
        <textarea
          ref={textareaRef}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Ask anything…  (Enter to send, Shift+Enter for newline)"
          rows={1}
          className="flex-1 resize-none rounded-xl border border-line px-3 py-2 text-sm leading-relaxed focus:border-orange focus:outline-none"
          style={{ overflow: "hidden" }}
        />
        <button
          type="submit"
          disabled={loading || !draft.trim()}
          className="rounded-xl bg-ink px-5 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}
