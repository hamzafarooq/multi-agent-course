import { z } from 'zod';
import { AnswerId, DocId, SpaceId, ThreadId, UserId } from './ids.js';
import { DocStatus } from './http.js';
import { Depth, DoneEvent, Locator, Source, SubQuestion, Terminated, ToolName } from './sse.js';

/**
 * One database, `lumina` (PRD 8). These are the documents, not an ODM. Mongoose is
 * allowed but not required: zod is the contract, the ODM is an implementation detail.
 * Every document carries `userId` (from X-User-Id) and `createdAt`.
 */

const iso = z.union([z.string().datetime(), z.date()]);

export const ThreadDoc = z.object({
  _id: ThreadId,
  userId: UserId,
  title: z.string(),
  createdAt: iso
});
export type ThreadDoc = z.infer<typeof ThreadDoc>;

export const MessageDoc = z.object({
  _id: z.string(),
  threadId: ThreadId,
  userId: UserId,
  role: z.enum(['user', 'assistant']),
  content: z.string(),
  answerId: AnswerId.optional(),
  sources: z.array(Source).default([]),
  done: DoneEvent.optional(),
  /** The plan a deep search ran, stored so the answer stays explainable after the stream. */
  subQuestions: z.array(SubQuestion).optional(),
  createdAt: iso
});
export type MessageDoc = z.infer<typeof MessageDoc>;

export const EMBEDDING_DIMS = 1536;

export const MemoryDoc = z.object({
  _id: z.string(),
  userId: UserId,
  text: z.string().min(1),
  embedding: z.array(z.number()).length(EMBEDDING_DIMS),
  sourceThread: ThreadId.optional(),
  createdAt: iso
});
export type MemoryDoc = z.infer<typeof MemoryDoc>;

export const SpaceDoc = z.object({
  _id: SpaceId,
  userId: UserId,
  name: z.string(),
  createdAt: iso
});
export type SpaceDoc = z.infer<typeof SpaceDoc>;

export const DocumentDoc = z.object({
  _id: DocId,
  spaceId: SpaceId,
  userId: UserId,
  title: z.string(),
  mimeType: z.string(),
  bytes: z.number().int().nonnegative(),
  status: DocStatus,
  pct: z.number().min(0).max(100),
  pages: z.number().int().positive().optional(),
  chunks: z.number().int().nonnegative().optional(),
  error: z.string().optional(),
  /** GridFS id of the raw upload. */
  fileId: z.string(),
  createdAt: iso
});
export type DocumentDoc = z.infer<typeof DocumentDoc>;

export const ChunkDoc = z.object({
  _id: z.string(),
  docId: DocId,
  spaceId: SpaceId,
  userId: UserId,
  /** The chunk's own text. This is what a citation's snippet must be found in. */
  text: z.string().min(1),
  locator: Locator,
  ord: z.number().int().nonnegative(),
  embedding: z.array(z.number()).length(EMBEDDING_DIMS),
  createdAt: iso.optional()
});
export type ChunkDoc = z.infer<typeof ChunkDoc>;

export const SearchCacheDoc = z.object({
  /** sha256 of (normalized query + provider). */
  _id: z.string(),
  provider: z.enum(['tavily', 'serpapi']),
  query: z.string(),
  results: z.array(z.record(z.unknown())),
  /** The TTL index on this field is what expires the row; do not delete rows by hand. */
  expiresAt: iso,
  createdAt: iso
});
export type SearchCacheDoc = z.infer<typeof SearchCacheDoc>;

export const JobKind = z.enum(['index_document']);
export type JobKind = z.infer<typeof JobKind>;

export const JobStatus = z.enum(['pending', 'running', 'done', 'failed']);
export type JobStatus = z.infer<typeof JobStatus>;

export const JobDoc = z.object({
  _id: z.string(),
  kind: JobKind,
  status: JobStatus,
  payload: z.record(z.unknown()),
  userId: UserId,
  /** Stale `claimedAt` on a `running` row is how the sweeper finds a crashed job. */
  claimedAt: iso.optional(),
  workerId: z.string().optional(),
  attempts: z.number().int().nonnegative().default(0),
  error: z.string().optional(),
  createdAt: iso
});
export type JobDoc = z.infer<typeof JobDoc>;

export const RequestDoc = z.object({
  requestId: z.string(),
  userId: UserId,
  route: z.string(),
  status: z.number().int(),
  ms: z.number().nonnegative(),
  tokensIn: z.number().int().nonnegative().optional(),
  tokensOut: z.number().int().nonnegative().optional(),
  costUsd: z.number().nonnegative().optional(),
  toolCalls: z.number().int().nonnegative().optional(),
  terminated: Terminated.optional(),
  depth: Depth.optional(),
  createdAt: iso
});
export type RequestDoc = z.infer<typeof RequestDoc>;

/**
 * The run log. Exactly the shape `quality/check.mjs` reads out of `runs/<requestId>.json`
 * (PRD 13) — `tokens` is a single total, not the `{in,out}` split the done event carries.
 * Written once per answer. Ten lines of adapter; it is what the gates read.
 */
export const RunLog = z.object({
  tokens: z.number().int().nonnegative(),
  wallClockSec: z.number().nonnegative(),
  costUsd: z.number().nonnegative(),
  terminated: Terminated,
  /**
   * Which gear ran. The gates read one global budget out of expectations.json, so this is
   * how a reader (and the bench) tells a legitimately expensive deep run apart from a
   * quick run that has quietly run away with the budget.
   */
  depth: Depth.optional(),
  toolCalls: z.array(
    z
      .object({
        name: ToolName,
        ok: z.boolean(),
        error: z.string().optional(),
        ms: z.number().nonnegative().optional()
      })
      .superRefine((t, ctx) => {
        if (t.ok === false && !t.error?.trim()) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            path: ['error'],
            message: 'a failed tool call must carry a non-empty error string (A1)'
          });
        }
      })
  )
});
export type RunLog = z.infer<typeof RunLog>;

/** Same shape as the file, plus what makes it queryable when it lives in Mongo. */
export const RunDoc = RunLog.extend({
  requestId: z.string(),
  userId: UserId.optional(),
  threadId: ThreadId.optional(),
  answerId: AnswerId.optional(),
  query: z.string().optional(),
  createdAt: iso
});
export type RunDoc = z.infer<typeof RunDoc>;

export const COLLECTIONS = {
  threads: 'threads',
  messages: 'messages',
  memories: 'memories',
  spaces: 'spaces',
  documents: 'documents',
  chunks: 'chunks',
  searchCache: 'searchCache',
  jobs: 'jobs',
  requests: 'requests',
  runs: 'runs'
} as const;

export const GRIDFS_BUCKETS = { uploads: 'uploads' } as const;

/** Index names `scripts/create-indexes.mjs` creates. `/health` reports which backend is live. */
export const SEARCH_INDEXES = {
  memoriesVector: 'memories_vector',
  chunksVector: 'chunks_vector',
  chunksText: 'chunks_text'
} as const;
