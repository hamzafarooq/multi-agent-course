export type PhaseKey =
  | "idle"
  | "waiting-for-scope"
  | "scoping"
  | "research"
  | "prd"
  | "decisions"
  | "stories"
  | "contract"
  | "brief"
  | "building"
  | "qa"
  | "launch"
  | "done"
  | "failed";

export type BuildState = "idle" | "running" | "done" | "failed";

export interface Credentials {
  email: string;
  password: string;
}

export type ProjectType = "web-app" | "api-service" | "cli-tool";
export type StackProfile = "node-react" | "nextjs" | "python-react";
export type DataLayer = "local" | "supabase";

/** Parsed from docs/scope.md by the presenter server. Null until scope.md exists. */
export interface BuildConfig {
  projectType: ProjectType | null;
  stack: StackProfile | null;
  dataLayer: DataLayer | null;
  level: ScopeLevel | null;
  companyUrl?: string | null;
  repoUrl?: string | null;
  coreLoop?: string | null;
  excludes?: string[] | null;
}

export interface Status {
  phase: PhaseKey;
  step?: string;
  stepNumber?: number;
  message?: string;
  timestamp?: string;
  docs: string[];
  build?: { backend: BuildState; frontend: BuildState };
  qa?: {
    contractBackend?: "pass" | "fail" | "pending";
    contractFrontend?: "pass" | "fail" | "pending";
    integration?: { passed: number; total: number } | null;
    authDance?: "pass" | "fail" | "n/a" | "pending";
    coreLoop?: "pass" | "fail" | "pending";
  };
  appUrl?: string | null;
  credentials?: Credentials | null;
  projectName?: string | null;
  /** True when this is the committed sample run, not a live one. */
  demo?: boolean;
  config?: BuildConfig | null;
  failure?: {
    state: string;
    message: string;
    recovery: string;
  } | null;
}

export type ScopeLevel = "clickable" | "MVP" | "Prod";

export interface ScopeSubmission {
  projectName: string;
  companyUrl: string;
  repoUrl: string;
  level: ScopeLevel;
  projectType: ProjectType;
  stack: StackProfile;
  dataLayer: DataLayer;
  coreLoop: string;
  excludes: string;
}

/* ------------------------------------------------------------------ */
/* Phase definitions — the 10-step timeline                           */
/* ------------------------------------------------------------------ */

export interface PhaseDef {
  key: Exclude<PhaseKey, "idle" | "waiting-for-scope" | "failed" | "done">;
  number: number;
  title: string;
  subtitle: string;
  docFile?: string;
}

export const PHASES: PhaseDef[] = [
  {
    key: "scoping",
    number: 1,
    title: "Scoping",
    subtitle: "Level, core loop, excludes",
    docFile: "scope.md",
  },
  {
    key: "research",
    number: 2,
    title: "Reference research",
    subtitle: "What the reference product does",
    docFile: "reference-brief.md",
  },
  {
    key: "prd",
    number: 3,
    title: "PRD",
    subtitle: "What we're building, for whom",
    docFile: "prd.md",
  },
  {
    key: "decisions",
    number: 4,
    title: "Decisions",
    subtitle: "Scope cuts vs. the reference",
    docFile: "decisions.md",
  },
  {
    key: "stories",
    number: 5,
    title: "User stories",
    subtitle: "Acceptance criteria Playwright can drive",
    docFile: "user-stories.md",
  },
  {
    key: "contract",
    number: 6,
    title: "API contract",
    subtitle: "The one source of truth both engineers build to",
    docFile: "api-contract.md",
  },
  {
    key: "brief",
    number: 7,
    title: "Tech-lead brief",
    subtitle: "Synthesises the spec set into a build plan",
  },
  {
    key: "building",
    number: 8,
    title: "Parallel build",
    subtitle: "Backend and frontend in parallel",
  },
  {
    key: "qa",
    number: 9,
    title: "QA",
    subtitle: "Contract checks, auth dance, core loop",
  },
  {
    key: "launch",
    number: 10,
    title: "Launch",
    subtitle: "Seed, start servers, hand off the URL",
  },
];

const PHASE_ORDER: PhaseKey[] = [
  "scoping",
  "research",
  "prd",
  "decisions",
  "stories",
  "contract",
  "brief",
  "building",
  "qa",
  "launch",
  "done",
];

export function phaseState(
  row: PhaseDef,
  current: PhaseKey
): "idle" | "running" | "done" | "failed" {
  if (current === "failed") {
    // past phases are done, everything else idle
    return "idle";
  }
  const rowIndex = PHASE_ORDER.indexOf(row.key);
  const currentIndex = PHASE_ORDER.indexOf(current);
  if (rowIndex < currentIndex) return "done";
  if (rowIndex === currentIndex) return "running";
  return "idle";
}
