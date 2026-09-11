import { useEffect, useState } from "react";
import { motion } from "motion/react";
import { ArrowRight, ArrowLeft, Check, Globe, Github, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input, Textarea, Label, FieldHint, Segmented } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/cn";
import { submitScope } from "@/lib/status";
import type { DataLayer, ProjectType, ScopeLevel, ScopeSubmission, StackProfile, Status } from "@/lib/types";

interface ScopeProps {
  onSubmitted: () => void;
  onBack: () => void;
  status: Status;
  /** Demo replay: open the form prefilled with these real values; Start begins the replay without writing to disk. */
  autoplay?: Partial<ScopeSubmission> | null;
}

const LEVEL_OPTIONS: {
  value: ScopeLevel;
  title: string;
  tagline: string;
  body: string;
  recommended?: boolean;
}[] = [
  {
    value: "clickable",
    title: "Clickable",
    tagline: "Pitch-ready walkthrough",
    body: "Fake data, no login, nothing persists. Fastest path to something you can click through.",
  },
  {
    value: "MVP",
    title: "MVP",
    tagline: "The core loop works for real",
    body: "Real signup and login, real rows in a database, one flow working end to end.",
    recommended: true,
  },
  {
    value: "Prod",
    title: "Prod",
    tagline: "Ready for a handful of real users",
    body: "MVP plus form validation, loading states, error boundaries, and a browser test that submits bad input.",
  },
];

const PROJECT_TYPES: { value: ProjectType; label: string; hint: string }[] = [
  { value: "web-app", label: "web-app", hint: "UI + API" },
  { value: "api-service", label: "api-service", hint: "API only" },
  { value: "cli-tool", label: "cli-tool", hint: "command line" },
];

const STACKS: { value: StackProfile; label: string; hint: string }[] = [
  { value: "node-react", label: "node-react", hint: "Express + Vite" },
  { value: "nextjs", label: "nextjs", hint: "one app" },
  { value: "python-react", label: "python-react", hint: "FastAPI + Vite" },
];

const DATA_LAYERS: { value: DataLayer; label: string; hint: string }[] = [
  { value: "local", label: "local", hint: "SQLite, no keys" },
  { value: "supabase", label: "supabase", hint: "needs a .env" },
];

export function Scope({ onSubmitted, onBack, status, autoplay }: ScopeProps) {
  const [projectName, setProjectName] = useState("");
  const [companyUrl, setCompanyUrl] = useState("");
  const [repoUrl, setRepoUrl] = useState("");
  const [level, setLevel] = useState<ScopeLevel>("MVP");
  const [projectType, setProjectType] = useState<ProjectType>("web-app");
  const [stack, setStack] = useState<StackProfile>("node-react");
  const [dataLayer, setDataLayer] = useState<DataLayer>("local");
  const [coreLoop, setCoreLoop] = useState("");
  const [excludes, setExcludes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Transition once the orchestrator has picked up scope.md.
  useEffect(() => {
    if (autoplay) return;
    if (status.phase !== "idle" && status.phase !== "waiting-for-scope") {
      const t = setTimeout(onSubmitted, 300);
      return () => clearTimeout(t);
    }
  }, [status.phase, onSubmitted, autoplay]);

  // Demo replay: open the form already filled with the real scope. The presenter presses Start.
  useEffect(() => {
    if (!autoplay) return;
    setProjectName(autoplay.projectName ?? "");
    setCompanyUrl(autoplay.companyUrl ?? "");
    setRepoUrl(autoplay.repoUrl ?? "");
    if (autoplay.level) setLevel(autoplay.level);
    if (autoplay.projectType) setProjectType(autoplay.projectType);
    if (autoplay.stack) setStack(autoplay.stack);
    if (autoplay.dataLayer) setDataLayer(autoplay.dataLayer);
    setCoreLoop(autoplay.coreLoop ?? "");
    setExcludes(autoplay.excludes ?? "");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoplay]);

  const canSubmit = companyUrl.trim() && coreLoop.trim() && !submitting;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    setSubmitting(true);
    setError(null);
    if (autoplay) {
      // A recording never writes docs/scope.md.
      setTimeout(onSubmitted, 600);
      return;
    }
    const result = await submitScope({
      projectName,
      companyUrl,
      repoUrl,
      level,
      projectType,
      stack,
      dataLayer,
      coreLoop,
      excludes,
    });
    if (!result.ok) {
      setSubmitting(false);
      setError(result.error ?? "Could not submit");
    }
    // On success: leave submitting=true. The phase watcher above will transition.
  }

  return (
    <div className="pt-16 pb-8">
      <div className="max-w-[820px] mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Badge className="mb-5">Scoping</Badge>
          <h1 className="text-[44px] leading-[1.1] font-semibold tracking-[-0.03em] text-fg">
            Tell Sprint Zero what you want to build.
          </h1>
          <p className="mt-4 text-[16px] leading-relaxed text-fg-muted max-w-[620px]">
            These are the same questions the terminal would ask. Your answers are written to{" "}
            <code className="font-mono text-[13px] text-fg">docs/scope.md</code>, and every agent
            in the run reads that file before it does anything else.
          </p>
        </motion.div>

        <motion.form
          onSubmit={handleSubmit}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.06, duration: 0.3 }}
          className="mt-12 space-y-10"
        >
          <section className="space-y-5">
            <SectionLabel num="01" title="Identify the run" />

            <Field>
              <Label htmlFor="projectName">Project name</Label>
              <Input
                id="projectName"
                placeholder="mini-twenty"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
              />
              <FieldHint>A short slug used in the delivery summary. Optional.</FieldHint>
            </Field>

            <Field>
              <Label htmlFor="companyUrl">Reference product URL</Label>
              <div className="relative">
                <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-fg-subtle pointer-events-none" />
                <Input
                  id="companyUrl"
                  placeholder="https://twenty.com"
                  value={companyUrl}
                  onChange={(e) => setCompanyUrl(e.target.value)}
                  required
                  className="pl-9"
                />
              </div>
              <FieldHint>
                The product Sprint Zero studies and then rebuilds at the level you pick below. Required.
              </FieldHint>
            </Field>

            <Field>
              <Label htmlFor="repoUrl">Repo URL</Label>
              <div className="relative">
                <Github className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-fg-subtle pointer-events-none" />
                <Input
                  id="repoUrl"
                  placeholder="https://github.com/twentyhq/twenty"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  className="pl-9"
                />
              </div>
              <FieldHint>
                Optional. With a repo, the researcher reads the README and folder structure
                alongside the marketing site, which makes the API contract far less guessy.
              </FieldHint>
            </Field>
          </section>

          <section className="space-y-5">
            <SectionLabel num="02" title="Pick a build level" />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {LEVEL_OPTIONS.map((opt) => {
                const selected = level === opt.value;
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setLevel(opt.value)}
                    className={cn(
                      "text-left p-5 rounded-lg border transition-colors duration-150",
                      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-fg/20",
                      selected
                        ? "border-fg bg-surface"
                        : "border-border bg-surface hover:border-border-strong"
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <div className="text-[11px] font-mono text-fg-subtle uppercase tracking-widest">
                        {opt.value}
                      </div>
                      {selected ? (
                        <span className="h-4 w-4 rounded-full bg-fg text-bg flex items-center justify-center">
                          <Check className="w-2.5 h-2.5" strokeWidth={3} />
                        </span>
                      ) : opt.recommended ? (
                        <Badge>Default</Badge>
                      ) : null}
                    </div>
                    <div className="mt-3 text-[17px] font-semibold tracking-tight text-fg">
                      {opt.title}
                    </div>
                    <div className="mt-0.5 text-[12.5px] text-fg-muted font-medium">{opt.tagline}</div>
                    <div className="mt-3 text-[13px] leading-relaxed text-fg-muted">{opt.body}</div>
                  </button>
                );
              })}
            </div>
          </section>

          <section className="space-y-5">
            <SectionLabel num="03" title="Choose the build configuration" />
            <Field>
              <Label>Project type</Label>
              <Segmented value={projectType} onChange={setProjectType} options={PROJECT_TYPES} ariaLabel="Project type" />
              <FieldHint>
                {projectType === "web-app"
                  ? "A UI plus an API. Both engineers are spawned and QA drives a real browser."
                  : projectType === "api-service"
                    ? "Backend only. No frontend, no browser tests. QA checks the API directly."
                    : "A command-line program. No server. QA runs the CLI and asserts on output."}
              </FieldHint>
            </Field>
            <Field>
              <Label>Stack profile</Label>
              <Segmented value={stack} onChange={setStack} options={STACKS} ariaLabel="Stack profile" />
              <FieldHint>
                {stack === "node-react"
                  ? "Express on 3001, React + Vite on 5173. The default and the best-trodden path."
                  : stack === "nextjs"
                    ? "One Next.js app on 3000 serving both pages and route handlers."
                    : "FastAPI on 8000, React + Vite on 5173. Python dependencies in a venv."}
              </FieldHint>
            </Field>
            <Field>
              <Label>Data layer</Label>
              <Segmented value={dataLayer} onChange={setDataLayer} options={DATA_LAYERS} ariaLabel="Data layer" />
              <FieldHint>
                {dataLayer === "local"
                  ? "SQLite file plus a self-issued JWT. Runs straight after clone with no account or keys."
                  : "Hosted Postgres and Supabase Auth. Needs a free Supabase project and four keys in a .env."}
              </FieldHint>
            </Field>
          </section>

          <section className="space-y-5">
            <SectionLabel num="04" title="Name the core loop" />
            <Field>
              <Label htmlFor="coreLoop">The one user flow that must work</Label>
              <Textarea
                id="coreLoop"
                placeholder="User creates a contact (name, email, company), creates a deal linked to that contact, and moves the deal across pipeline stages (Lead, Qualified, Proposal, Closed Won or Closed Lost)."
                value={coreLoop}
                onChange={(e) => setCoreLoop(e.target.value)}
                required
                className="min-h-[120px]"
              />
              <FieldHint>
                If only one thing works end to end, what is it? Name the screens and the records.
                The agents build exactly this and not much else.
              </FieldHint>
            </Field>
          </section>

          <section className="space-y-5">
            <SectionLabel num="05" title="Name what to leave out" />
            <Field>
              <Label htmlFor="excludes">Anything to exclude</Label>
              <Textarea
                id="excludes"
                placeholder={
                  "Companies as a separate entity (roll into contacts)\nCustom fields\nEmail integration\nSearch and saved views"
                }
                value={excludes}
                onChange={(e) => setExcludes(e.target.value)}
                className="min-h-[120px]"
              />
              <FieldHint>
                One per line. Anything listed here is a feature the agents will not attempt,
                which is how you stop an MVP from growing a settings page.
              </FieldHint>
            </Field>
          </section>

          <section className="pt-2">
            <Card className="p-4 flex items-center justify-between bg-surface-2">
              <div className="flex items-center gap-3">
                <Button type="button" variant="ghost" size="md" onClick={onBack}>
                  <ArrowLeft className="w-4 h-4" />
                  Back
                </Button>
                {error && (
                  <span className="text-[13px] text-danger">{error}</span>
                )}
              </div>
              <Button type="submit" size="lg" disabled={!canSubmit}>
                {submitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Waiting for Sprint Zero
                  </>
                ) : (
                  <>
                    Start the run
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </Button>
            </Card>
          </section>
        </motion.form>
      </div>
    </div>
  );
}

function SectionLabel({ num, title }: { num: string; title: string }) {
  return (
    <div className="flex items-baseline gap-3 pb-2 border-b border-border">
      <span className="font-mono text-[11px] text-fg-subtle tracking-widest">{num}</span>
      <h2 className="text-[17px] font-semibold tracking-tight text-fg">{title}</h2>
    </div>
  );
}

function Field({ children }: { children: React.ReactNode }) {
  return <div className="space-y-2">{children}</div>;
}
