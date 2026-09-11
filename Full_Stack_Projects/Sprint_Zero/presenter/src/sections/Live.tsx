import { useEffect, useMemo, useState } from "react";
import { AnimatePresence } from "motion/react";
import { PhaseTimeline } from "@/components/PhaseTimeline";
import { DocPreview } from "@/components/DocPreview";
import { BuildCards } from "@/components/BuildCards";
import { DoneHero } from "@/components/DoneHero";
import { QaPanel } from "@/components/QaPanel";
import { FailureCard } from "@/components/FailureCard";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { PHASES, phaseState, type PhaseDef, type Status } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Activity, Loader2 } from "lucide-react";

interface LiveProps {
  status: Status;
  demo?: boolean;
}

export function Live({ status, demo }: LiveProps) {
  const failed = status.phase === "failed";
  const isDone = status.phase === "done";

  // Pick the right thing to show on the right pane.
  const autoPhase = useMemo<PhaseDef | null>(() => {
    if (status.phase === "done" || status.phase === "failed" || status.phase === "idle") return null;
    return PHASES.find((p) => p.key === status.phase) ?? null;
  }, [status.phase]);

  const [pinnedKey, setPinnedKey] = useState<PhaseDef["key"] | null>(null);

  // Clear the pin when the phase advances past it
  useEffect(() => {
    if (!pinnedKey) return;
    const phaseDef = PHASES.find((p) => p.key === pinnedKey);
    if (!phaseDef) return;
    const state = phaseState(phaseDef, status.phase);
    if (state === "running" || state === "done") return;
    setPinnedKey(null);
  }, [pinnedKey, status.phase]);

  const activeKey = pinnedKey ?? autoPhase?.key ?? null;
  const activePhase = activeKey ? PHASES.find((p) => p.key === activeKey) ?? null : null;

  // Pick whichever doc to display: the user's pinned one, or the latest one written.
  const docToShow = useMemo(() => {
    if (activePhase?.docFile && status.docs.includes(activePhase.docFile)) {
      return { file: activePhase.docFile, phase: activePhase };
    }
    // fallback: most recently completed doc
    const ordered = [...PHASES].reverse();
    for (const p of ordered) {
      if (p.docFile && status.docs.includes(p.docFile)) {
        return { file: p.docFile, phase: p };
      }
    }
    return null;
  }, [activePhase, status.docs]);

  // Bust the markdown cache when scope.md or any doc changes
  const cacheKey = status.timestamp ?? status.docs.join(",");

  return (
    <div className="pt-10 pb-8">
      <Header status={status} />

      <div className="mt-8 grid grid-cols-1 lg:grid-cols-[340px_1fr] gap-6">
        {/* ---------- left: timeline ---------- */}
        <Card className="p-4 h-fit lg:sticky lg:top-20">
          <div className="px-2 pt-1 pb-3 border-b border-border flex items-center justify-between">
            <div className="text-[11px] font-mono text-fg-subtle uppercase tracking-widest">
              Pipeline
            </div>
            {status.stepNumber && !failed && !isDone && (
              <div className="text-[11px] font-mono text-fg-muted">
                step {status.stepNumber}/10
              </div>
            )}
          </div>
          <div className="mt-3">
            <PhaseTimeline
              phase={status.phase}
              docs={status.docs}
              selectedKey={activeKey}
              onSelect={(p) => setPinnedKey((cur) => (cur === p.key ? null : p.key))}
              failed={failed}
            />
          </div>
        </Card>

        {/* ---------- right: context pane ---------- */}
        <div className="min-h-[600px]">
          <AnimatePresence mode="wait">
            {failed && status.failure ? (
              <FailureCard
                key="failure"
                state={status.failure.state}
                message={status.failure.message}
                recovery={status.failure.recovery}
              />
            ) : isDone && status.appUrl && !pinnedKey ? (
              <DoneHero
                key="done"
                appUrl={status.appUrl}
                credentials={status.credentials}
                projectName={status.projectName}
                demo={demo}
              />
            ) : activePhase?.key === "building" ? (
              <BuildCards
                key="build"
                backend={status.build?.backend}
                frontend={status.build?.frontend}
                config={status.config}
              />
            ) : activePhase?.key === "qa" ? (
              <QaPanel key="qa" qa={status.qa} />
            ) : activePhase?.key === "brief" && !docToShow ? (
              <BriefingPlaceholder key="brief" />
            ) : docToShow ? (
              <DocPreview
                key={docToShow.file}
                docFile={docToShow.file}
                title={docToShow.phase.title}
                subtitle={docToShow.phase.subtitle}
                cacheKey={cacheKey}
              />
            ) : (
              <WaitingPlaceholder key="wait" message={status.message} />
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */

function Header({ status }: { status: Status }) {
  const failed = status.phase === "failed";
  const done = status.phase === "done";
  const stepName = PHASES.find((p) => p.key === status.phase)?.title ?? status.step ?? "Idle";

  return (
    <header className="flex items-center justify-between">
      <div>
        <Badge
          tone={failed ? "danger" : done ? "success" : "accent"}
          className="mb-3"
        >
          <Activity className="w-3 h-3" />
          {failed ? "Run halted" : done ? "Run complete" : "Run in progress"}
        </Badge>
        <h1 className="text-[34px] font-semibold tracking-[-0.03em] text-fg">
          {failed
            ? "Sprint Zero stopped."
            : done
              ? "Sprint Zero finished."
              : stepName}
        </h1>
        {!failed && !done && status.message && (
          <p className="mt-2 text-[14.5px] text-fg-muted">{status.message}</p>
        )}
      </div>
      {!failed && !done && (
        <div className="flex items-center gap-2 text-[12px] text-fg-muted">
          <Loader2 className="w-3.5 h-3.5 animate-spin text-fg" />
          watching docs/, server/, client/
        </div>
      )}
    </header>
  );
}

function WaitingPlaceholder({ message }: { message?: string }) {
  return (
    <Card className="h-full p-8 flex flex-col justify-center min-h-[400px]">
      <div className="flex items-start gap-4">
        <Loader2 className="w-5 h-5 text-fg animate-spin mt-0.5" />
        <div>
          <h3 className="text-[16px] font-semibold tracking-tight text-fg">
            Nothing new yet
          </h3>
          <p className="mt-2 text-[14px] text-fg-muted leading-relaxed max-w-[480px]">
            {message ??
              "This pane updates the moment a doc lands in docs/ or the phase changes."}
          </p>
          <div className="mt-6 space-y-3">
            <div className="h-3.5 w-2/3 rounded shimmer" />
            <div className="h-3.5 w-5/6 rounded shimmer" />
            <div className="h-3.5 w-3/5 rounded shimmer" />
          </div>
        </div>
      </div>
    </Card>
  );
}

function BriefingPlaceholder() {
  return (
    <Card className="h-full p-8" elevated>
      <CardHeader className="px-0 pt-0">
        <CardTitle>Tech-lead build brief</CardTitle>
        <CardDescription>
          The tech lead is reading all six docs and deciding who builds what, on which ports.
          Its brief prints in the terminal, and the engineers do not start until it does.
        </CardDescription>
      </CardHeader>
      <CardContent className="px-0 pb-0 mt-2 space-y-3">
        <div className="h-4 w-3/4 rounded shimmer" />
        <div className="h-4 w-full rounded shimmer" />
        <div className="h-4 w-5/6 rounded shimmer" />
        <div className="h-4 w-2/3 rounded shimmer" />
      </CardContent>
    </Card>
  );
}
