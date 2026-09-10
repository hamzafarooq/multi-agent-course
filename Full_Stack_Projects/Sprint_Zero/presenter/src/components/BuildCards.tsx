import { motion } from "motion/react";
import { Check, Loader2, Server, Monitor } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/cn";
import type { BuildConfig, BuildState } from "@/lib/types";

interface BuildCardsProps {
  backend?: BuildState;
  frontend?: BuildState;
  config?: BuildConfig | null;
}

const BACKEND: Record<string, { title: string; steps: string[] }> = {
  "node-react": {
    title: "Express API",
    steps: ["data client + JWT middleware", "schema and idempotent seed", "routes per contract entity"],
  },
  nextjs: {
    title: "Next.js route handlers",
    steps: ["app scaffold + data client", "schema and idempotent seed", "app/api routes per contract entity"],
  },
  "python-react": {
    title: "FastAPI backend",
    steps: ["data client + JWT dependency", "schema and idempotent seed", "routers per contract entity"],
  },
};

const FRONTEND: Record<string, { title: string; steps: string[] }> = {
  "node-react": {
    title: "React + Vite client",
    steps: ["session context + protected routes", "login, signup, landing page", "product screens + api client"],
  },
  nextjs: {
    title: "Next.js pages",
    steps: ["session context + protected routes", "login, signup, landing page", "product screens, same-origin api"],
  },
  "python-react": {
    title: "React + Vite client",
    steps: ["session context + protected routes", "login, signup, landing page", "product screens + api client"],
  },
};

export function BuildCards({ backend = "idle", frontend = "idle", config }: BuildCardsProps) {
  const stack = config?.stack ?? "node-react";
  const hasFrontend = (config?.projectType ?? "web-app") === "web-app";
  const be = BACKEND[stack] ?? BACKEND["node-react"];
  const fe = FRONTEND[stack] ?? FRONTEND["node-react"];
  const authNote =
    config?.dataLayer === "supabase" ? " Auth via Supabase." : " Auth via the backend's own JWT.";
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="h-full flex flex-col gap-4"
    >
      <Card className="p-6">
        <div className="flex items-start justify-between gap-3">
          <div>
            <Badge tone="accent">Parallel build</Badge>
            <h3 className="mt-3 text-[22px] font-semibold tracking-tight text-fg">
              {hasFrontend ? "Both engineers are building to the contract." : "The backend engineer is building to the contract."}
            </h3>
            <p className="mt-2 text-[14px] leading-relaxed text-fg-muted max-w-[620px]">
              {hasFrontend ? "Backend and frontend never speak to each other. They both read " : "The engineer reads "}
              <code className="font-mono text-[12.5px] text-fg">docs/api-contract.md</code>
              {hasFrontend
                ? " and build in isolation. When they return, QA validates both against the same contract."
                : " and builds to it. When it returns, QA validates against the same contract."}
              {authNote}
            </p>
          </div>
        </div>
      </Card>

      <div className={cn("grid grid-cols-1 gap-4 flex-1", hasFrontend && "md:grid-cols-2")}>
        <BuildPanel icon={Server} label="backend-engineer" title={be.title} state={backend} steps={be.steps} />
        {hasFrontend && (
          <BuildPanel icon={Monitor} label="frontend-engineer" title={fe.title} state={frontend} steps={fe.steps} />
        )}
      </div>
    </motion.div>
  );
}

function BuildPanel({
  icon: Icon,
  label,
  title,
  state,
  steps,
}: {
  icon: React.ComponentType<{ className?: string; strokeWidth?: number }>;
  label: string;
  title: string;
  state: BuildState;
  steps: string[];
}) {
  const isRunning = state === "running";
  const isDone = state === "done";

  return (
    <Card
      className={cn(
        "h-full transition-colors duration-300",
        isRunning && "border-fg",
        isDone && "border-success/40"
      )}
    >
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <div
              className={cn(
                "h-10 w-10 rounded-md border flex items-center justify-center shrink-0 transition-colors",
                isRunning && "border-fg bg-fg",
                isDone && "border-success/30 bg-success/10",
                state === "idle" && "border-border bg-surface-2"
              )}
            >
              <Icon
                className={cn(
                  "w-4.5 h-4.5 transition-colors",
                  isRunning && "text-bg",
                  isDone && "text-success",
                  state === "idle" && "text-fg-subtle"
                )}
                strokeWidth={1.5}
              />
            </div>
            <div>
              <code className="text-[12px] font-mono text-fg-subtle">{label}</code>
              <CardTitle className="mt-0.5">{title}</CardTitle>
              <CardDescription>
                {isRunning
                  ? "Building…"
                  : isDone
                    ? "Complete. All endpoints match the contract."
                    : state === "failed"
                      ? "Reported a failure."
                      : "Waiting for the build brief."}
              </CardDescription>
            </div>
          </div>
          <StateIcon state={state} />
        </div>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2.5">
          {steps.map((s, i) => (
            <li key={i} className="flex items-center gap-2.5 text-[13px]">
              <div
                className={cn(
                  "w-1.5 h-1.5 rounded-full shrink-0",
                  isDone ? "bg-success" : isRunning ? "bg-fg animate-pulse" : "bg-fg-subtle/40"
                )}
              />
              <span className={isRunning || isDone ? "text-fg-muted" : "text-fg-subtle"}>{s}</span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}

function StateIcon({ state }: { state: BuildState }) {
  if (state === "running")
    return (
      <div className="h-7 w-7 rounded-full bg-surface border border-fg flex items-center justify-center">
        <Loader2 className="w-3.5 h-3.5 text-fg animate-spin" strokeWidth={2} />
      </div>
    );
  if (state === "done")
    return (
      <div className="h-7 w-7 rounded-full bg-success/15 border border-success/40 flex items-center justify-center">
        <Check className="w-3.5 h-3.5 text-success" strokeWidth={2.5} />
      </div>
    );
  if (state === "failed")
    return (
      <div className="h-7 w-7 rounded-full bg-danger/15 border border-danger/40 flex items-center justify-center">
        <span className="text-[10px] font-bold text-danger">!</span>
      </div>
    );
  return (
    <div className="h-7 w-7 rounded-full border border-border flex items-center justify-center">
      <span className="text-[10.5px] font-mono text-fg-subtle">idle</span>
    </div>
  );
}
