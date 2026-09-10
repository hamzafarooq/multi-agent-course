import { motion } from "motion/react";
import { Check, Loader2, ShieldCheck, X } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/cn";
import type { Status } from "@/lib/types";

export function QaPanel({ qa }: { qa: NonNullable<Status["qa"]> | undefined }) {
  const rows = [
    { key: "contractBackend", label: "Contract check: backend" },
    { key: "contractFrontend", label: "Contract check: frontend" },
    {
      key: "integration",
      label: qa?.integration
        ? `Integration tests (${qa.integration.passed}/${qa.integration.total})`
        : "Integration tests",
    },
    { key: "authDance", label: "Auth dance (signup, session, logout, login, 401)" },
    { key: "coreLoop", label: "Core loop happy path" },
  ] as const;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="h-full"
    >
      <Card className="h-full" elevated>
        <CardHeader>
          <div className="flex items-start gap-3">
            <div className="h-9 w-9 rounded-md bg-surface-2 border border-border flex items-center justify-center shrink-0">
              <ShieldCheck className="w-4 h-4 text-fg" strokeWidth={1.75} />
            </div>
            <div>
              <CardTitle>QA in a real browser</CardTitle>
              <CardDescription>
                Validates both engineers against the contract and drives the live app in a real
                browser.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <ul className="space-y-1">
            {rows.map((r) => {
              const value = qa ? (qa as Record<string, unknown>)[r.key] : undefined;
              const state = normalize(value);
              return (
                <li
                  key={r.key}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2.5 rounded-md",
                    "border border-transparent",
                    state === "running" && "bg-surface-2"
                  )}
                >
                  <StateIcon state={state} />
                  <span
                    className={cn(
                      "text-[13.5px]",
                      state === "idle" ? "text-fg-subtle" : "text-fg-muted"
                    )}
                  >
                    {r.label}
                  </span>
                </li>
              );
            })}
          </ul>
        </CardContent>
      </Card>
    </motion.div>
  );
}

type RowState = "pass" | "fail" | "running" | "n/a" | "idle";

function normalize(v: unknown): RowState {
  if (v === "pass" || v === "fail" || v === "n/a") return v;
  if (v === "pending") return "running";
  if (v && typeof v === "object" && "passed" in v && "total" in v) {
    const o = v as { passed: number; total: number };
    return o.total === 0 ? "idle" : o.passed === o.total ? "pass" : "fail";
  }
  return "idle";
}

function StateIcon({ state }: { state: RowState }) {
  if (state === "pass")
    return (
      <div className="w-5 h-5 rounded-full bg-success/15 border border-success/40 flex items-center justify-center shrink-0">
        <Check className="w-3 h-3 text-success" strokeWidth={2.5} />
      </div>
    );
  if (state === "fail")
    return (
      <div className="w-5 h-5 rounded-full bg-danger/15 border border-danger/40 flex items-center justify-center shrink-0">
        <X className="w-3 h-3 text-danger" strokeWidth={2.5} />
      </div>
    );
  if (state === "running")
    return (
      <div className="w-5 h-5 rounded-full bg-surface border border-fg flex items-center justify-center shrink-0">
        <Loader2 className="w-3 h-3 text-fg animate-spin" strokeWidth={2} />
      </div>
    );
  if (state === "n/a")
    return (
      <div className="w-5 h-5 rounded-full bg-surface-3 border border-border flex items-center justify-center shrink-0">
        <span className="text-[8px] text-fg-subtle font-mono">n/a</span>
      </div>
    );
  return (
    <div className="w-5 h-5 rounded-full border border-border bg-surface-2 shrink-0" />
  );
}
