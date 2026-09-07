import { z } from 'zod';
import { Terminated, ToolName } from './sse.js';

/**
 * `GET /evals/report.json` — the Product Evaluation, written by `/fde-lumina-eval` and
 * rendered by the provided UI at `/evals`. This page IS the submission (SUBMISSION.md).
 *
 * Never hand-edit a report, and never write a number into one that a run did not produce.
 */

/** The five system-design questions, answered before the build. Graded as the design section. */
export const DesignAnswers = z.object({
  components: z.string().min(1),
  responsibilities: z.string().min(1),
  communication: z.string().min(1),
  state: z.string().min(1),
  tradeoffs: z.string().min(1)
});
export type DesignAnswers = z.infer<typeof DesignAnswers>;

export const RubricRow = z.object({
  id: z.string(),
  label: z.string(),
  points: z.number(),
  awarded: z.number(),
  status: z.enum(['pass', 'partial', 'fail', 'manual']),
  evidence: z.string(),
  rules: z.array(z.string()).default([])
});
export type RubricRow = z.infer<typeof RubricRow>;

export const RubricReport = z.object({
  total: z.number(),
  awarded: z.number(),
  automated: z.array(RubricRow),
  manual: z.array(RubricRow),
  redLines: z.array(z.object({ check: z.string(), ok: z.boolean(), detail: z.string().optional() })).default([])
});
export type RubricReport = z.infer<typeof RubricReport>;

/** One SLA line: what was declared, what the run produced, and whether it held. */
export const SlaRow = z.object({
  metric: z.string(),
  target: z.number(),
  actual: z.number().nullable(),
  unit: z.string(),
  comparator: z.enum(['<=', '>=']),
  pass: z.boolean(),
  note: z.string().optional()
});
export type SlaRow = z.infer<typeof SlaRow>;

export const BenchReport = z.object({
  ranAt: z.string().datetime(),
  target: z.string(),
  pass: z.boolean(),
  sla: z.array(SlaRow),
  /** The four metric names quality/check.mjs looks for, also written to reports/eval.json. */
  citationGrounding: z.number().min(0).max(1).nullable(),
  recallAt5: z.number().min(0).max(1).nullable(),
  retrievalRate: z.number().min(0).max(1).nullable(),
  errorRate: z.number().min(0).max(1).nullable(),
  latency: z
    .object({
      ttftP50Ms: z.number().nullable(),
      ttftP95Ms: z.number().nullable(),
      answerP50Ms: z.number().nullable(),
      answerP95Ms: z.number().nullable(),
      accept202P95Ms: z.number().nullable()
    })
    .partial(),
  cost: z
    .object({
      meanCostPerAnswerUsd: z.number().nullable(),
      projectedMonthlyUsd: z.number().nullable(),
      projectedMonthlyNoCacheUsd: z.number().nullable()
    })
    .partial(),
  searchCacheHitRatePct: z.number().nullable().optional(),
  answers: z.number().int().nonnegative().optional()
});
export type BenchReport = z.infer<typeof BenchReport>;

export const QualityRuleResult = z.object({
  id: z.string(),
  title: z.string(),
  severity: z.string(),
  status: z.enum(['pass', 'fail', 'skip', 'manual', 'unimplemented']),
  detail: z.string().optional()
});
export type QualityRuleResult = z.infer<typeof QualityRuleResult>;

export const QualityReport = z.object({
  project: z.string(),
  checkedAt: z.string(),
  runs: z.number().int().nonnegative(),
  errors: z.number().int().nonnegative(),
  warnings: z.number().int().nonnegative(),
  results: z.array(QualityRuleResult)
});
export type QualityReport = z.infer<typeof QualityReport>;

/** One step of a trajectory a human actually read, end to end. */
export const TrajectoryStep = z.object({
  step: z.number().int().positive(),
  tool: ToolName,
  ok: z.boolean(),
  ms: z.number().nonnegative().optional(),
  input: z.record(z.unknown()).optional(),
  reason: z.string().optional(),
  error: z.string().optional(),
  subQuestion: z.number().int().positive().optional()
});
export type TrajectoryStep = z.infer<typeof TrajectoryStep>;

export const Trajectory = z.object({
  requestId: z.string().min(1),
  query: z.string().optional(),
  terminated: Terminated.optional(),
  depth: z.enum(['quick', 'deep']).optional(),
  steps: z.array(TrajectoryStep),
  /** What reading it taught you. P1 is not satisfied by pasting a log. */
  notes: z.string().min(1)
});
export type Trajectory = z.infer<typeof Trajectory>;

export const GateResult = z.object({
  gate: z.number().int().nonnegative(),
  name: z.enum(['STATIC', 'CONTRACT', 'RUN', 'TRAJECTORY', 'EVAL', 'HUMAN']),
  status: z.enum(['pass', 'fail', 'skip', 'manual']),
  detail: z.string().optional(),
  exitCode: z.number().int().optional()
});
export type GateResult = z.infer<typeof GateResult>;

export const EvalsReport = z.object({
  assignment: z.string(),
  student: z.string(),
  repo: z.string().optional(),
  video: z.string().optional(),
  deployedAt: z.string(),
  /** LLM, search provider, Atlas tier: how this run was actually configured. */
  runNotes: z.string().optional(),
  design: DesignAnswers,
  gates: z.array(GateResult).default([]),
  rubric: RubricReport,
  bench: BenchReport,
  quality: QualityReport,
  trajectories: z.object({ successful: Trajectory, failing: Trajectory })
});
export type EvalsReport = z.infer<typeof EvalsReport>;
