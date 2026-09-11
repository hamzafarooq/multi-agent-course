import { useEffect, useRef, useState } from "react";
import type { Status } from "./types";

/**
 * Replays a finished run as a timed sequence so a room can watch the pipeline
 * advance in about a minute. Every doc shown is the real one from the sample;
 * only the clock is synthetic.
 */

type Step = {
  phase: Status["phase"];
  step: string;
  stepNumber: number;
  message: string;
  ms: number;
  docsAfter: string[];
  build?: (t: number) => Status["build"];
  qa?: (t: number) => Status["qa"];
};

const D = ["scope.md", "reference-brief.md", "prd.md", "decisions.md", "user-stories.md", "api-contract.md"];

export const REPLAY_STEPS: Step[] = [
  { phase: "research", step: "reference-brief", stepNumber: 2, message: "Researching the reference product.", ms: 6000, docsAfter: D.slice(0, 2) },
  { phase: "prd", step: "prd", stepNumber: 3, message: "Drafting the PRD.", ms: 5000, docsAfter: D.slice(0, 3) },
  { phase: "decisions", step: "decisions", stepNumber: 4, message: "Logging scope cuts and tradeoffs.", ms: 4000, docsAfter: D.slice(0, 4) },
  { phase: "stories", step: "user-stories", stepNumber: 5, message: "Expanding stories with acceptance criteria.", ms: 4000, docsAfter: D.slice(0, 5) },
  { phase: "contract", step: "api-contract", stepNumber: 6, message: "Writing the API contract.", ms: 5000, docsAfter: D },
  { phase: "brief", step: "tech-lead-brief", stepNumber: 7, message: "Tech-lead is reading the spec set.", ms: 4000, docsAfter: D },
  {
    phase: "building", step: "parallel-build", stepNumber: 8, message: "Backend and frontend building in parallel.", ms: 9000, docsAfter: D,
    build: (t) => ({ backend: t > 0.65 ? "done" : "running", frontend: t > 0.95 ? "done" : "running" }),
  },
  {
    phase: "qa", step: "qa", stepNumber: 9, message: "QA: contract checks, auth dance, core loop, Ask me in both modes.", ms: 9000, docsAfter: D,
    build: () => ({ backend: "done", frontend: "done" }),
    qa: (t) => ({
      contractBackend: t > 0.15 ? "pass" : "pending",
      contractFrontend: t > 0.32 ? "pass" : "pending",
      integration: t > 0.55 ? { passed: 97, total: 97 } : { passed: 0, total: 0 },
      authDance: t > 0.75 ? "pass" : "pending",
      coreLoop: t > 0.92 ? "pass" : "pending",
    }),
  },
  { phase: "launch", step: "launch", stepNumber: 10, message: "Installing, seeding, and starting the servers.", ms: 3000, docsAfter: D,
    build: () => ({ backend: "done", frontend: "done" }),
    qa: () => ({ contractBackend: "pass", contractFrontend: "pass", integration: { passed: 97, total: 97 }, authDance: "pass", coreLoop: "pass" }),
  },
];

export const REPLAY_TOTAL_MS = REPLAY_STEPS.reduce((a, s) => a + s.ms, 0);

export function useReplay(sample: Status | null, active: boolean, onDone: () => void) {
  const [elapsed, setElapsed] = useState(0);
  const [finished, setFinished] = useState(false);
  const raf = useRef<number | null>(null);
  const start = useRef<number>(0);
  const doneRef = useRef(onDone);
  doneRef.current = onDone;

  const reset = () => {
    setElapsed(0);
    setFinished(false);
    start.current = performance.now();
  };

  useEffect(() => {
    if (!active || finished) return;
    start.current = performance.now() - elapsed;
    const tick = (now: number) => {
      const e = now - start.current;
      if (e >= REPLAY_TOTAL_MS) {
        setElapsed(REPLAY_TOTAL_MS);
        setFinished(true);
        doneRef.current();
        return;
      }
      setElapsed(e);
      raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => {
      if (raf.current) cancelAnimationFrame(raf.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active, finished]);

  const skip = () => {
    if (raf.current) cancelAnimationFrame(raf.current);
    setElapsed(REPLAY_TOTAL_MS);
    setFinished(true);
    doneRef.current();
  };

  let status: Status;
  if (!sample) {
    status = { phase: "idle", docs: [], demo: true };
  } else if (finished) {
    status = { ...sample, demo: true };
  } else {
    let acc = 0;
    let cur = REPLAY_STEPS[0];
    let t = 0;
    for (const s of REPLAY_STEPS) {
      if (elapsed < acc + s.ms) {
        cur = s;
        t = (elapsed - acc) / s.ms;
        break;
      }
      acc += s.ms;
    }
    const idx = REPLAY_STEPS.indexOf(cur);
    const docs = idx === 0 ? ["scope.md"] : REPLAY_STEPS[idx - 1].docsAfter;
    status = {
      phase: cur.phase,
      step: cur.step,
      stepNumber: cur.stepNumber,
      message: cur.message,
      docs,
      build: cur.build ? cur.build(t) : { backend: "idle", frontend: "idle" },
      qa: cur.qa ? cur.qa(t) : undefined,
      projectName: sample.projectName,
      config: sample.config,
      appUrl: null,
      credentials: null,
      demo: true,
      timestamp: String(Math.floor(elapsed / 250)),
    };
  }

  return { status, elapsed, finished, skip, reset, progress: Math.min(1, elapsed / REPLAY_TOTAL_MS) };
}
