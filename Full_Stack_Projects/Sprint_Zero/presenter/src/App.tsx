import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { TopNav } from "./components/TopNav";
import { About } from "./sections/About";
import { Scope } from "./sections/Scope";
import { Live } from "./sections/Live";
import { useStatus } from "./lib/status";

type Section = "about" | "scope" | "live";

export default function App() {
  const [demo, setDemo] = useState(() => window.location.hash === "#demo");
  const status = useStatus(demo);
  const [section, setSection] = useState<Section>(() => (window.location.hash === "#demo" ? "live" : "about"));
  const [userLocked, setUserLocked] = useState(() => window.location.hash === "#demo");

  const startDemo = () => {
    setDemo(true);
    window.location.hash = "demo";
    setUserLocked(true);
    setSection("live");
  };
  const exitDemo = () => {
    setDemo(false);
    if (window.location.hash === "#demo") history.replaceState(null, "", window.location.pathname);
    setUserLocked(true);
    setSection("about");
  };

  // Auto-advance to Live once the run has begun, unless the user has
  // navigated manually (e.g. back to About for a second explanation).
  useEffect(() => {
    if (userLocked) return;
    if (status.phase === "idle") return;
    // The sample run is already "done". Don't skip the audience past About.
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
              {" "}<code className="font-mono text-[12px]">/sprint-zero</code> run against ghost.org, saved from the real
              pipeline. Nothing here is live.
            </span>
            {demo && (
              <button onClick={exitDemo} className="ml-auto text-[13px] font-medium text-fg hover:underline underline-offset-2">
                Exit demo
              </button>
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
              <Scope onSubmitted={() => handleNav("live")} onBack={() => handleNav("about")} status={status} />
            )}
            {section === "live" && <Live status={status} demo={demo} />}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}
