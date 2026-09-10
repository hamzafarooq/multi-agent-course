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
          Give it a URL. Get back six spec docs and an app that runs.
        </h1>
        <p className="mt-6 text-[18px] leading-relaxed text-fg-muted max-w-[640px]">
          Sprint Zero is a Claude Code kit for developers, founders, and PMs. You hand it a product
          to study and tell it which one flow has to work. Four sub-agents write the specs, then build to them while
          you watch from this screen. On the default stack there are no accounts or keys to set
          up first.
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
          title="What happens between the URL and the running app."
          description="One /sprint-zero command drives all of it. You answer questions once, at the start. After that your job is to read what lands."
        />
        <motion.div variants={stagger} className="mt-10 grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            {
              n: "01",
              title: "A reference",
              body: "A product close to what you want. Twenty for a CRM, Linear for issue tracking. Add a GitHub repo if there is one, so the researcher can read the source too.",
              icon: BookOpen,
            },
            {
              n: "02",
              title: "Your answers",
              body: "Which level, which stack, where data lives, the one flow that has to work end to end, and what to leave out. The form on the next tab writes them to docs/scope.md.",
              icon: MousePointerClick,
            },
            {
              n: "03",
              title: "Six docs, then code",
              body: "Reference brief, PRD, decisions, user stories, API contract. Only once the contract exists do the two engineers start, each building to it without seeing the other's work.",
              icon: Layers,
            },
            {
              n: "04",
              title: "A running app",
              body: "QA signs up, logs out, logs back in, and corrupts its own token to check the 401. Then both servers start and the URL and a demo login land on this screen.",
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
          title="One setting decides how much gets built."
          description="The level goes into docs/scope.md and every agent reads it before starting. Clickable is for a pitch. MVP is what this kit is tuned for. Prod is MVP with the rough edges sanded down, and it takes longer."
        />
        <div className="mt-10 grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            {
              key: "clickable",
              title: "Clickable",
              tagline: "For pitching a flow",
              body: "Fake data, no login, no database. Every screen is clickable and nothing persists. Fastest to build, and enough for a stakeholder review.",
              tone: "neutral" as const,
            },
            {
              key: "MVP",
              title: "MVP",
              tagline: "The core loop works for real",
              body: "Real signup and login, real rows in a database (SQLite by default), and the one flow you named working end to end. Everything else stays thin on purpose.",
              tone: "accent" as const,
              featured: true,
            },
            {
              key: "Prod",
              title: "Prod",
              tagline: "Ready for a handful of real users",
              body: "MVP plus validation on forms, loading states, error boundaries, and a browser test that deliberately submits bad input to see what happens.",
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
          title="Six documents, written in order."
          description="Each one is read by the writer of the next. The last, the API contract, is the only file both engineers are allowed to build from."
        />
        <div className="mt-10">
          <PipelineTrack />
        </div>
      </section>

      {/* ------------------------------- team ------------------------------- */}
      <section className="mt-28">
        <SectionHeading
          kicker="The build team"
          title="Four sub-agents, one conversation."
          description="You only ever talk to the main Claude Code session. It briefs a tech lead, spawns two engineers at the same time, then hands what they built to QA."
        />
        <div className="mt-10 grid grid-cols-1 md:grid-cols-2 gap-4">
          <AgentCard
            icon={FileText}
            role="tech-lead"
            title="Reads the specs, plans the build, writes no code."
            body="Works out which engineers to spawn, on which ports, with which run commands, and whether any doc is too thin to build from. If one is, the run stops here instead of producing a broken app."
          />
          <AgentCard
            icon={Cog}
            role="backend-engineer"
            title="Owns server/."
            body="Schema, seed data with real-sounding names and companies, auth endpoints that issue a JWT, and one route per entity in the contract. Express, FastAPI, or Next.js route handlers, depending on the stack you picked."
          />
          <AgentCard
            icon={Zap}
            role="frontend-engineer"
            title="Owns client/."
            body="Login, signup, a session provider, protected routes, the product screens, and a landing page. Every form field gets a data-testid so QA can find it in the browser."
          />
          <AgentCard
            icon={ShieldCheck}
            role="qa-engineer"
            title="Owns the verdict."
            body="Checks both codebases against the contract, runs API tests, then drives a real browser through signup, logout, login, and an expired token. When something is off, it fixes the code to match the contract, never the other way round."
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
                Paths, request and response shapes, status codes, and which routes need a token,
                all in docs/api-contract.md. The backend implements it, the frontend calls it,
                and QA checks both against it. The engineers never see each other's code, which
                is the point: the contract is the only place they could disagree, and it is
                written down before either of them starts.
              </p>
            </div>
          </div>
        </Card>
      </section>

      {/* ------------------------------ CTA ------------------------------ */}
      <section className="mt-28 text-center">
        <h3 className="text-[28px] font-semibold tracking-tight text-fg">
          Now watch one happen.
        </h3>
        <p className="mt-3 text-[15px] text-fg-muted">
          Fill in the form, then sit on the Live tab. The scope doc lands the moment you
          submit. The rest follow as each agent finishes.
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
