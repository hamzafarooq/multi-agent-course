import { z } from 'zod';
import { AnswerId, DocId } from './ids.js';

/**
 * The events of a streamed answer, in the order the UI expects them:
 *
 *   quick:  trace* → sources → token* → done
 *   deep:   plan → trace* → sources → token* → done
 *
 * `sources` MUST arrive before the first `token` so the UI can render citation chips
 * while the text is still arriving (PRD 7). On a deep search `plan` comes first, so the
 * reader can see what the system decided to go and find out.
 *
 * `error` ends the stream at any point.
 */

/** Every tool the loop may call. */
export const AskTool = z.enum([
  'web_search',
  'fetch_page',
  'search_documents',
  'recall_memory',
  'save_memory',
  /**
   * Decomposes a question into sub-questions. DEEP SEARCH ONLY: a quick search that calls
   * this has silently escalated itself into a run that costs several times as much, which
   * is the spend failure this separation exists to prevent (rule R2's shape).
   */
  'plan_research'
]);
export type AskTool = z.infer<typeof AskTool>;

/** Tools a quick search may never call, whatever the model decides it wants. */
export const DEEP_ONLY_TOOLS = ['plan_research'] as const;

export const ToolName = AskTool;
export type ToolName = z.infer<typeof ToolName>;

/**
 * How hard to look. Perplexity's two gears, and the whole point of having both is that
 * the cheap one is the default: most questions do not need six sub-questions and twelve
 * pages, and answering them as if they did is how a product becomes uneconomic.
 */
export const Depth = z.enum(['quick', 'deep']);
export type Depth = z.infer<typeof Depth>;

/**
 * One step of the loop, emitted before the answer streams. `reason` is what makes the
 * trace a debugging surface rather than a progress bar: it is why this step happened.
 */
export const TraceEvent = z
  .object({
    step: z.number().int().positive(),
    tool: ToolName,
    input: z.record(z.unknown()),
    ok: z.boolean(),
    ms: z.number().nonnegative(),
    reason: z.string().optional(),
    error: z.string().optional(),
    /** On a deep search, which sub-question this step was serving. Absent on a quick one. */
    subQuestion: z.number().int().positive().optional()
  })
  .superRefine((ev, ctx) => {
    // Rule A1, enforced by the contract itself: a failure you cannot tell apart from an
    // empty result is the Live Translate bug waiting to happen.
    if (ev.ok === false && !ev.error?.trim()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['error'],
        message: 'a trace step with ok:false must carry a non-empty error string (A1)'
      });
    }
  });
export type TraceEvent = z.infer<typeof TraceEvent>;

/** One thing the planner decided to go and find out. */
export const SubQuestion = z.object({
  i: z.number().int().positive(),
  question: z.string().min(1),
  /** Why this sub-question, in the planner's words. This is what makes the plan readable. */
  reason: z.string().optional()
});
export type SubQuestion = z.infer<typeof SubQuestion>;

/**
 * Emitted once, at the start of a deep search, before any retrieval. A deep search that
 * streams no plan is a slow quick search: the decomposition IS the feature, and it has to
 * be visible or nobody can tell whether it was any good.
 */
export const PlanEvent = z.object({
  subQuestions: z.array(SubQuestion).min(2).max(8),
  reason: z.string().optional()
});
export type PlanEvent = z.infer<typeof PlanEvent>;

export const Locator = z
  .object({
    page: z.number().int().positive().optional(),
    heading: z.string().optional(),
    line: z.number().int().positive().optional()
  })
  .refine((l) => l.page !== undefined || l.heading !== undefined || l.line !== undefined, {
    message: 'a chunk locator needs page, heading, or line'
  });
export type Locator = z.infer<typeof Locator>;

/** One citable thing that was actually retrieved in this request. `n` is the `[n]` in the text. */
export const Source = z
  .object({
    n: z.number().int().positive(),
    kind: z.enum(['web', 'doc']),
    title: z.string().min(1),
    /** The passage the claim rests on. The grounding check looks for this in the fetched text. */
    snippet: z.string().min(1),
    url: z.string().url().optional(),
    docId: DocId.optional(),
    locator: Locator.optional(),
    /**
     * Which sub-question turned this up. Deep search merges several result sets into one
     * numbering, and without this a reader cannot tell why a source is in the list.
     */
    subQuestion: z.number().int().positive().optional()
  })
  .superRefine((s, ctx) => {
    if (s.kind === 'web' && !s.url) {
      ctx.addIssue({ code: z.ZodIssueCode.custom, path: ['url'], message: 'a web source needs a url' });
    }
    if (s.kind === 'doc' && !s.docId) {
      ctx.addIssue({ code: z.ZodIssueCode.custom, path: ['docId'], message: 'a doc source needs a docId' });
    }
  });
export type Source = z.infer<typeof Source>;

export const SourcesEvent = z.array(Source);
export type SourcesEvent = z.infer<typeof SourcesEvent>;

export const TokenEvent = z.object({ text: z.string() });
export type TokenEvent = z.infer<typeof TokenEvent>;

/**
 * Why the loop stopped, set explicitly at the call site. No SDK gives you this:
 *   done  finished on its own
 *   cap   hit the tool-call or wall-clock cap; the answer is an honest partial
 *   error a provider threw; the request is also a 502
 */
export const Terminated = z.enum(['done', 'cap', 'error']);
export type Terminated = z.infer<typeof Terminated>;

export const DoneEvent = z.object({
  answerId: AnswerId,
  latencyMs: z.number().nonnegative(),
  ttftMs: z.number().nonnegative(),
  model: z.string().min(1),
  tokens: z.object({ in: z.number().int().nonnegative(), out: z.number().int().nonnegative() }),
  costUsd: z.number().nonnegative(),
  /** true only when EVERY search in the request was a cache hit. */
  searchCached: z.boolean(),
  terminated: Terminated,
  /** Which gear actually ran. The client asked; the server reports what it did. */
  depth: Depth,
  /** How many sub-questions the plan held. Absent or 0 on a quick search. */
  subQuestions: z.number().int().nonnegative().optional()
});
export type DoneEvent = z.infer<typeof DoneEvent>;

export const StreamErrorEvent = z.object({
  status: z.number().int(),
  error: z.string().min(1)
});
export type StreamErrorEvent = z.infer<typeof StreamErrorEvent>;

export const SSE_EVENTS = ['plan', 'trace', 'sources', 'token', 'done', 'error'] as const;
export type SseEventName = (typeof SSE_EVENTS)[number];

/** Discriminated union of a parsed SSE frame, for the UI's reducer. */
export const AskStreamEvent = z.union([
  z.object({ event: z.literal('plan'), data: PlanEvent }),
  z.object({ event: z.literal('trace'), data: TraceEvent }),
  z.object({ event: z.literal('sources'), data: SourcesEvent }),
  z.object({ event: z.literal('token'), data: TokenEvent }),
  z.object({ event: z.literal('done'), data: DoneEvent }),
  z.object({ event: z.literal('error'), data: StreamErrorEvent })
]);
export type AskStreamEvent = z.infer<typeof AskStreamEvent>;

/**
 * Every `[n]` in an answer must have exactly one matching source. Extra or missing is a
 * grounding failure (PRD 7). Both the agent service and the bench use this.
 */
export function citationNumbers(text: string): number[] {
  const out = new Set<number>();
  for (const m of text.matchAll(/\[(\d{1,3})\]/g)) out.add(Number(m[1]));
  return [...out].sort((a, b) => a - b);
}

export function unresolvedCitations(text: string, sources: readonly Source[]): number[] {
  const have = new Set(sources.map((s) => s.n));
  return citationNumbers(text).filter((n) => !have.has(n));
}
