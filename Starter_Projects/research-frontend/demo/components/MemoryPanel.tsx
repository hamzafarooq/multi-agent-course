"use client";

type Props = {
  claudeMd: string;
  skillMd: string;
  showSkill?: boolean;
};

export function MemoryPanel({ claudeMd, skillMd, showSkill = true }: Props) {
  return (
    <aside className="space-y-4 border-l border-line bg-[#fafafa] p-4 text-xs">
      <section>
        <h4 className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-ink-2">
          📁 memory/CLAUDE.md
        </h4>
        <pre className="max-h-64 overflow-y-auto whitespace-pre-wrap break-words rounded-md border border-line bg-white p-2 font-mono text-[10px] leading-relaxed text-ink-2">
          {claudeMd || "(empty — no facts yet)"}
        </pre>
      </section>
      {showSkill && (
        <section>
          <h4 className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-ink-2">
            📋 skills/research/SKILL.md
          </h4>
          <pre className="max-h-64 overflow-y-auto whitespace-pre-wrap break-words rounded-md border border-line bg-white p-2 font-mono text-[10px] leading-relaxed text-ink-2">
            {skillMd || "(empty)"}
          </pre>
        </section>
      )}
    </aside>
  );
}
