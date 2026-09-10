import { motion, type Variants } from "motion/react";
import {
  ArrowRight,
  BookOpen,
  Cog,
  FileText,
  Layers,
  MousePointerClick,
  Rocket,
  ShieldCheck,
  Sparkles,
  Workflow,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const stagger: Variants = {
  animate: { transition: { staggerChildren: 0.06, delayChildren: 0.05 } },
};
const item: Variants = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.35, ease: [0.2, 0.8, 0.2, 1] as const } },
};

export function About({ onStart }: { onStart: () => void }) {
  return (
    <motion.div variants={stagger} initial="initial" animate="animate" className="pt-16 pb-8">
      {/* ------------------------------- hero ------------------------------- */}
      <motion.div variants={item} className="max-w-[840px]">
        <Badge className="mb-6">
          <Sparkles className="w-3 h-3" />
          Sprint Zero
        </Badge>
        <h1 className="text-[64px] leading-[1.02] font-semibold tracking-[-0.04em] text-fg">
          From a reference URL to a working product. One command.
        </h1>
        <p className="mt-6 text-[18px] leading-relaxed text-fg-muted max-w-[640px]">
          Sprint Zero is a Claude Code kit that gives a PM a full sub-agent product team on
          their laptop. Point it at a reference. Answer the scoping questions. Get back a full
          spec set and a running app.
        </p>
        <div className="mt-10 flex items-center gap-3">
          <Button size="lg" onClick={onStart}>
            Start a run
            <ArrowRight className="w-4 h-4" />
          </Button>
          <a
            href="#concept"
            className="text-[14px] text-fg-muted hover:text-fg transition-colors px-3 h-12 inline-flex items-center"
          >
            Read the flow first
          </a>
        </div>
      </motion.div>

      {/* ------------------------------ concept ------------------------------ */}
      <section id="concept" className="mt-28">
        <SectionHeading
          kicker="The flow"
          title="Four moving parts. One command drives all of them."
          description="Everything below runs inside a single /sprint-zero invocation. The PM stays in the loop the whole way through because the loop is now minutes long, not weeks."
        />
        <motion.div variants={stagger} className="mt-10 grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            {
              n: "01",
              title: "Reference URL",
              body: "You point Sprint Zero at a product similar to what you want to build. Optionally also a repo.",
              icon: BookOpen,
            },
            {
              n: "02",
              title: "A few scoping answers",
              body: "Build level, stack, where data lives, the one core loop that matters, and what to leave out.",
              icon: MousePointerClick,
            },
            {
              n: "03",
              title: "Specs, then code",
              body: "Six docs are written end-to-end. Then backend and frontend build in parallel to a shared contract.",
              icon: Layers,
            },
            {
              n: "04",
              title: "A running app",
              body: "QA drives a real browser through the auth dance and core loop. Servers boot. The URL lands in your terminal.",
              icon: Rocket,
            },
          ].map((c) => (
            <motion.div key={c.n} variants={item}>
              <Card className="p-5 h-full">
                <div className="flex items-start justify-between">
                  <c.icon className="w-5 h-5 text-fg" strokeWidth={1.5} />
                  <span className="text-[11px] font-mono text-fg-subtle tracking-wider">{c.n}</span>
                </div>
                <h3 className="mt-5 text-[15px] font-semibold tracking-tight text-fg">{c.title}</h3>
                <p className="mt-2 text-[13.5px] leading-relaxed text-fg-muted">{c.body}</p>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* --------------------------- scope levels ---------------------------- */}
      <section className="mt-28">
        <SectionHeading
          kicker="The scope lever"
          title="Pick one level. It calibrates every agent downstream."
          description="The scope level gets written into docs/scope.md and sets the polish bar for the whole run. Don't over-scope; MVP is the main demo path."
        />
        <div className="mt-10 grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            {
              key: "clickable",
              title: "Clickable",
              tagline: "Pitch-ready walkthrough",
              body: "Mock backend, fake data, no auth. Ideal for pitching and flow reviews where you just need the feel.",
              tone: "neutral" as const,
            },
            {
              key: "MVP",
              title: "MVP",
              tagline: "The idea actually works",
              body: "Real auth, real data, one core loop end-to-end. SQLite by default, Supabase if you ask. The demo path Sprint Zero is tuned for.",
              tone: "accent" as const,
              featured: true,
            },
            {
              key: "Prod",
              title: "Prod",
              tagline: "Ready for real users",
              body: "MVP plus error boundaries, loading states, input validation, and a browser error-path test per loop.",
              tone: "neutral" as const,
            },
          ].map((lvl) => (
            <Card
              key={lvl.key}
              className={
                "relative p-6 " +
                (lvl.featured ? "border-fg" : "")
              }
            >
              {lvl.featured && (
                <div className="absolute -top-2.5 left-6">
                  <Badge tone="accent">Default</Badge>
                </div>
              )}
              <div className="text-[12px] font-mono text-fg-subtle uppercase tracking-widest">
                {lvl.key}
              </div>
              <h3 className="mt-2 text-[22px] font-semibold tracking-tight text-fg">{lvl.title}</h3>
              <p className="mt-1 text-[13px] text-fg-muted font-medium">{lvl.tagline}</p>
              <p className="mt-4 text-[14px] leading-relaxed text-fg-muted">{lvl.body}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* ----------------------------- pipeline ------------------------------ */}
      <section className="mt-28">
        <SectionHeading
          kicker="The spec pipeline"
          title="Six documents, written in order. Each one feeds the next."
          description="Nothing is built until the spec set is complete. The API contract is law. Both engineers build to it in isolation."
        />
        <div className="mt-10">
          <PipelineTrack />
        </div>
      </section>

      {/* ------------------------------- team ------------------------------- */}
      <section className="mt-28">
        <SectionHeading
          kicker="The build team"
          title="Four sub-agents. You only talk to the main session."
          description="A briefing layer reads the specs and plans the build. Two engineers build in parallel. QA drives the browser."
        />
        <div className="mt-10 grid grid-cols-1 md:grid-cols-2 gap-4">
          <AgentCard
            icon={FileText}
            role="tech-lead"
            title="Reads the specs. Writes the build brief."
            body="Reads scope, PRD, contract, and decisions. Synthesises a build plan. Does not write code."
          />
          <AgentCard
            icon={Cog}
            role="backend-engineer"
            title="Builds the API against the contract."
            body="Owns server/. Wires the data layer, JWT middleware, schema, and a realistic seed script. Express, FastAPI, or Next.js route handlers, per the stack."
          />
          <AgentCard
            icon={Zap}
            role="frontend-engineer"
            title="Builds the React client."
            body="Owns client/. Session context, protected routes, login and signup, and a polished landing page. Talks to the backend auth API or Supabase Auth, per the data layer."
          />
          <AgentCard
            icon={ShieldCheck}
            role="qa-engineer"
            title="Drives the app in a real browser."
            body="Auth dance, contract check, core loop happy path. Prod scope adds error-path tests per loop."
          />
        </div>
      </section>

      {/* ----------------------------- contract ----------------------------- */}
      <section className="mt-28">
        <Card className="p-8 md:p-10 bg-fg text-bg border-fg">
          <div className="flex items-start gap-5">
            <Workflow className="w-8 h-8 shrink-0" strokeWidth={1.4} />
            <div>
              <h3 className="text-[22px] font-semibold tracking-tight">
                The API contract is law.
              </h3>
              <p className="mt-3 text-[15px] leading-relaxed text-white/70 max-w-[760px]">
                Endpoint paths, request shapes, response shapes, status codes, all defined in
                one file. Backend implements it. Frontend consumes it. QA validates against it.
                The engineers never speak to each other; they both build to the same contract.
              </p>
            </div>
          </div>
        </Card>
      </section>

      {/* ------------------------------ CTA ------------------------------ */}
      <section className="mt-28 text-center">
        <h3 className="text-[28px] font-semibold tracking-tight text-fg">
          Ready when you are.
        </h3>
        <p className="mt-3 text-[15px] text-fg-muted">
          Start a run and watch the pipeline play out live.
        </p>
        <div className="mt-7 inline-flex">
          <Button size="lg" onClick={onStart}>
            Start a run
            <ArrowRight className="w-4 h-4" />
          </Button>
        </div>
      </section>
    </motion.div>
  );
}

/* ------------------------------------------------------------------ */

function SectionHeading({
  kicker,
  title,
  description,
}: {
  kicker: string;
  title: string;
  description?: string;
}) {
  return (
    <div className="max-w-[720px]">
      <div className="text-[12px] font-mono text-fg-subtle uppercase tracking-widest">{kicker}</div>
      <h2 className="mt-3 text-[36px] leading-[1.1] font-semibold tracking-[-0.03em] text-fg">
        {title}
      </h2>
      {description && (
        <p className="mt-4 text-[15px] leading-relaxed text-fg-muted">{description}</p>
      )}
    </div>
  );
}

function AgentCard({
  icon: Icon,
  role,
  title,
  body,
}: {
  icon: React.ComponentType<{ className?: string; strokeWidth?: number }>;
  role: string;
  title: string;
  body: string;
}) {
  return (
    <Card className="p-6">
      <div className="flex items-start gap-4">
        <div className="h-10 w-10 rounded-md bg-surface-2 border border-border flex items-center justify-center shrink-0">
          <Icon className="w-4.5 h-4.5 text-fg" strokeWidth={1.5} />
        </div>
        <div className="min-w-0">
          <code className="text-[12px] font-mono text-fg-subtle">{role}</code>
          <h3 className="mt-1 text-[15px] font-semibold tracking-tight text-fg">{title}</h3>
          <p className="mt-2 text-[13.5px] leading-relaxed text-fg-muted">{body}</p>
        </div>
      </div>
    </Card>
  );
}

function PipelineTrack() {
  const steps = [
    { n: "1", title: "scope.md", sub: "Build level, core loop, excludes" },
    { n: "2", title: "reference-brief.md", sub: "What the reference does, how" },
    { n: "3", title: "prd.md", sub: "Goals, non-goals, stories" },
    { n: "4", title: "decisions.md", sub: "Scope cuts vs. reference" },
    { n: "5", title: "user-stories.md", sub: "Given / When / Then" },
    { n: "6", title: "api-contract.md", sub: "The shared interface" },
  ];

  return (
    <div className="relative">
      <div className="absolute left-0 right-0 top-5 h-px bg-border" />
      <div className="relative grid grid-cols-2 md:grid-cols-6 gap-4">
        {steps.map((s, i) => (
          <div key={s.n} className="relative">
            <div className="flex items-center justify-center">
              <div className="relative z-10 w-10 h-10 rounded-full bg-surface border border-border flex items-center justify-center">
                <span className="text-[13px] font-mono text-fg font-semibold">{s.n}</span>
              </div>
            </div>
            <div className="mt-4 text-center">
              <div className="font-mono text-[12.5px] text-fg">{s.title}</div>
              <div className="mt-1 text-[11.5px] text-fg-subtle leading-tight">{s.sub}</div>
            </div>
            {i < steps.length - 1 && (
              <ArrowRight
                className="hidden md:block absolute top-4 -right-3 w-3 h-3 text-border-strong"
                strokeWidth={2}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
