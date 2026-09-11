import { motion } from "motion/react";
import { Check, AlertCircle } from "lucide-react";
import { cn } from "@/lib/cn";
import { PHASES, phaseState, type PhaseDef, type PhaseKey } from "@/lib/types";

interface PhaseTimelineProps {
  phase: PhaseKey;
  docs: string[];
  selectedKey: PhaseDef["key"] | null;
  onSelect: (p: PhaseDef) => void;
  failed?: boolean;
}

export function PhaseTimeline({
  phase,
  docs,
  selectedKey,
  onSelect,
  failed,
}: PhaseTimelineProps) {
  return (
    <ol className="relative space-y-1">
      {/* vertical rail */}
      <div className="absolute left-[15px] top-2 bottom-2 w-px bg-border" aria-hidden />
      {PHASES.map((p) => {
        const state = phaseState(p, phase);
        const hasDoc = p.docFile ? docs.includes(p.docFile) : false;
        const selectable = (state === "done" && !!p.docFile) || (state === "running" && hasDoc);
        const selected = selectedKey === p.key;
        const currentFailure = failed && state === "running";

        return (
          <li key={p.key}>
            <button
              onClick={() => selectable && onSelect(p)}
              disabled={!selectable}
              className={cn(
                "group w-full flex items-start gap-4 pl-0 pr-3 py-2.5 rounded-md",
                "transition-colors duration-150 text-left",
                selected
                  ? "bg-surface-3 border border-border"
                  : "border border-transparent hover:bg-surface-2",
                !selectable && "cursor-default hover:bg-transparent"
              )}
            >
              <PhaseDot state={state} number={p.number} failed={currentFailure} />
              <div className="min-w-0 flex-1 pt-0.5">
                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      "text-[14px] font-semibold tracking-tight",
                      state === "idle" ? "text-fg-subtle" : "text-fg"
                    )}
                  >
                    {p.title}
                  </span>
                  {state === "running" && !failed && <RunningPill />}
                  {currentFailure && (
                    <span className="text-[10.5px] font-medium text-danger tracking-wide uppercase">
                      failed
                    </span>
                  )}
                  {hasDoc && state === "done" && (
                    <span className="ml-auto text-[11px] text-fg-subtle group-hover:text-fg-muted transition-colors">
                      {selected ? "close" : "view doc"}
                    </span>
                  )}
                </div>
                <div
                  className={cn(
                    "mt-0.5 text-[12.5px] leading-snug",
                    state === "idle" ? "text-fg-subtle/70" : "text-fg-muted"
                  )}
                >
                  {p.subtitle}
                </div>
              </div>
            </button>
          </li>
        );
      })}
    </ol>
  );
}

function PhaseDot({
  state,
  number,
  failed,
}: {
  state: "idle" | "running" | "done" | "failed";
  number: number;
  failed?: boolean;
}) {
  return (
    <div className="relative z-10 shrink-0">
      <div
        className={cn(
          "w-8 h-8 rounded-full flex items-center justify-center",
          "border transition-colors duration-200",
          state === "done" &&
            !failed &&
            "bg-fg border-fg text-bg",
          state === "running" && !failed && "bg-surface border-fg text-fg animate-pulse-ring",
          state === "idle" && "bg-surface border-border text-fg-subtle",
          failed && "bg-surface border-danger text-danger"
        )}
      >
        {state === "done" && !failed ? (
          <Check className="w-4 h-4" strokeWidth={2.5} />
        ) : failed ? (
          <AlertCircle className="w-4 h-4" strokeWidth={2} />
        ) : (
          <span className="text-[12px] font-mono font-semibold">{number}</span>
        )}
      </div>
    </div>
  );
}

function RunningPill() {
  return (
    <motion.span
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-fg border border-fg"
    >
      <span className="w-1 h-1 rounded-full bg-bg animate-pulse" />
      <span className="text-[10.5px] font-medium text-bg tracking-wide uppercase">
        running
      </span>
    </motion.span>
  );
}
