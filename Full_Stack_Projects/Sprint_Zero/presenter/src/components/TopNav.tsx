import { Logo } from "./Logo";
import { cn } from "@/lib/cn";
import type { Status } from "@/lib/types";
import { Dot } from "./ui/badge";

type Section = "about" | "scope" | "live";

interface TopNavProps {
  section: Section;
  onChange: (next: Section) => void;
  status: Status;
  onRunDemo?: () => void;
}

export function TopNav({ section, onChange, status, onRunDemo }: TopNavProps) {
  const runStarted = status.phase !== "idle" && status.phase !== "waiting-for-scope";
  const runFinished = status.phase === "done";
  const runFailed = status.phase === "failed";

  const links: { key: Section; label: string; disabled?: boolean }[] = [
    { key: "about", label: "About" },
    { key: "scope", label: "Start a run" },
    { key: "live", label: "Live", disabled: !runStarted },
  ];

  return (
    <header className="sticky top-0 z-20 bg-bg/85 backdrop-blur-md border-b border-border">
      <div className="max-w-[1240px] mx-auto px-6 h-14 flex items-center justify-between">
        <Logo />
        <nav className="flex items-center gap-0.5">
          {links.map((l) => {
            const active = section === l.key;
            return (
              <button
                key={l.key}
                onClick={() => !l.disabled && onChange(l.key)}
                disabled={l.disabled}
                className={cn(
                  "h-8 px-3 rounded-md text-[13px] font-medium tracking-tight",
                  "transition-colors duration-150",
                  active ? "text-fg bg-surface-3" : "text-fg-muted hover:text-fg hover:bg-surface-3",
                  l.disabled && "opacity-40 cursor-not-allowed hover:bg-transparent hover:text-fg-muted"
                )}
              >
                {l.label}
              </button>
            );
          })}
        </nav>
        <div className="flex items-center gap-3 text-[12px] text-fg-muted font-mono">
          {onRunDemo && (
            <button
              onClick={onRunDemo}
              className="h-8 px-3 rounded-md bg-fg text-bg font-sans text-[13px] font-medium tracking-tight hover:bg-fg-hover transition-colors"
            >
              Run demo
            </button>
          )}
          <Dot
            tone={
              runFailed ? "danger" : runFinished ? "success" : runStarted ? "accent" : "neutral"
            }
          />
          <span>
            {runFailed
              ? "failed"
              : runFinished
                ? "done"
                : runStarted
                  ? status.step || "running"
                  : "idle"}
          </span>
        </div>
      </div>
    </header>
  );
}
