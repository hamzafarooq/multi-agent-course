import { useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { TopNav } from "./components/TopNav";
import { About } from "./sections/About";
import { Scope } from "./sections/Scope";
import { Live } from "./sections/Live";
import { useStatus } from "./lib/status";
import { useReplay, REPLAY_TOTAL_MS } from "./lib/replay";
import type { ScopeSubmission } from "./lib/types";

type Section = "about" | "scope" | "live";
type DemoStage = "form" | "run" | "done";

export default function App() {
  const [demo, setDemo] = useState(() => window.location.hash === "#demo");
  const [stage, setStage] = useState<DemoStage>("form");
  const sample = useStatus(demo);
  const [section, setSection] = useState<Section>(() => (window.location.hash === "#demo" ? "scope" : "about"));
  const [userLocked, setUserLocked] = useState(() => window.location.hash === "#demo");

  const replay = useReplay(demo ? sample : null, demo && stage === "run", () => setStage("done"));
  const status = demo ? (stage === "form" ? { ...sample, phase: "waiting-for-scope" as const, docs: [], appUrl: null, credentials: null } : replay.status) : sample;

  const autoplay = useMemo<Partial<ScopeSubmission> | null>(
    () =>
    demo && stage === "form" && sample.config
      ? {
          projectName: sample.projectName ?? "",
          companyUrl: sample.config.companyUrl ?? "",
          repoUrl: sample.config.repoUrl ?? "",
          level: sample.config.level ?? "MVP",
          projectType: sample.config.projectType ?? "web-app",
          stack: sample.config.stack ?? "node-react",
          dataLayer: sample.config.dataLayer ?? "local",
          coreLoop: sample.config.coreLoop ?? "",
          excludes: (sample.config.excludes ?? []).join("\n"),
        }
      : null,
    [demo, stage, sample.config, sample.projectName]
  );

  const startDemo = () => {
    setDemo(true);
    setStage("form");
    replay.reset();
    window.location.hash = "demo";
    setUserLocked(true);
    setSection("scope");
  };
  const replayDemo = () => {
    setStage("form");
    replay.reset();
    setSection("scope");
  };
  const exitDemo = () => {
    setDemo(false);
    setStage("form");
    if (window.location.hash === "#demo") history.replaceState(null, "", window.location.pathname);
    setUserLocked(true);
    setSection("about");
  };
  const demoFormSubmitted = () => {
    setStage("run");
    replay.reset();
    setSection("live");
  };

  // Auto-advance to Live once the run has begun, unless the user has
  // navigated manually (e.g. back to About for a second explanation).
  useEffect(() => {
    if (userLocked) return;
    if (status.phase === "idle") return;
    // In a demo the stage machine drives navigation.
    if (status.demo) return;
    if (status.phase === "waiting-for-scope") {
      setSection("scope");
      return;
    }
    setSection("live");
  }, [status.phase, userLocked]);

  const handleNav = (next: Section) => {
    setUserLocked(true);
    setSection(next);
  };

  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [section]);

  return (
    <div className="min-h-screen">
      <TopNav section={section} onChange={handleNav} status={status} onRunDemo={demo ? undefined : startDemo} />
      {status.demo && (
        <div className="border-b border-border bg-surface-2">
          <div className="max-w-[1240px] mx-auto px-6 py-2 flex items-center gap-2 text-[13px] text-fg-muted">
            <span className="inline-flex h-1.5 w-1.5 rounded-full bg-warn" />
            <span>
              <strong className="font-medium text-fg">Sample run.</strong> A recorded
              {" "}<code className="font-mono text-[12px]">/sprint-zero</code> run against ghost.org, replayed in about a
              minute. The docs are the real ones; only the clock is compressed.
            </span>
            {demo && (
              <span className="ml-auto flex items-center gap-4">
                {stage === "run" && (
                  <span className="flex items-center gap-2">
                    <span className="h-1 w-28 rounded-full bg-border overflow-hidden">
                      <span className="block h-full bg-fg transition-[width] duration-200" style={{ width: `${Math.round(replay.progress * 100)}%` }} />
                    </span>
                    <span className="font-mono text-[11.5px] text-fg-subtle">{Math.max(0, Math.ceil((REPLAY_TOTAL_MS - replay.elapsed) / 1000))}s</span>
                    <button onClick={replay.skip} className="text-[13px] font-medium text-fg hover:underline underline-offset-2">Skip to end</button>
                  </span>
                )}
                {stage === "done" && (
                  <button onClick={replayDemo} className="text-[13px] font-medium text-fg hover:underline underline-offset-2">Replay</button>
                )}
                <button onClick={exitDemo} className="text-[13px] font-medium text-fg hover:underline underline-offset-2">Exit demo</button>
              </span>
            )}
          </div>
        </div>
      )}
      <main className="max-w-[1240px] mx-auto px-6 pb-24">
        <AnimatePresence mode="wait">
          <motion.div
            key={section}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.22, ease: [0.2, 0.8, 0.2, 1] }}
          >
            {section === "about" && <About onStart={() => handleNav("scope")} />}
            {section === "scope" && (
              <Scope
                key={demo ? `demo-${stage}` : "live"}
                onSubmitted={demo ? demoFormSubmitted : () => handleNav("live")}
                onBack={demo ? exitDemo : () => handleNav("about")}
                status={status}
                autoplay={autoplay}
              />
            )}
            {section === "live" && <Live status={status} demo={demo} />}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}
