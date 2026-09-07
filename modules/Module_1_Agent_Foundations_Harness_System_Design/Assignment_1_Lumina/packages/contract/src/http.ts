import { z } from 'zod';
import { AnswerId, DocId, MemoryId, SpaceId, ThreadId } from './ids.js';
import { Depth, DoneEvent, Source } from './sse.js';

/**
 * Every route in PRD 7, as request and response schemas. The gateway validates inbound
 * bodies with these; the agent service validates what it sends back; the UI compiles
 * against the inferred types. One definition, three consumers, no drift.
 *
 * `X-User-Id` is required on every route except GET /health.
 */

export const USER_HEADER = 'x-user-id';
export const REQUEST_HEADER = 'x-request-id';

/** 400 · 401 · 404 · 413 · 429 · 501 · 502 all use this body. */
export const ErrorBody = z.object({
  error: z.string().min(1),
  status: z.number().int().optional(),
  /** 429 from the image cap says when the cap resets. */
  resetsAt: z.string().datetime().optional(),
  requestId: z.string().optional()
});
export type ErrorBody = z.infer<typeof ErrorBody>;

// ---------------------------------------------------------------- threads

export const CreateThreadBody = z.object({ title: z.string().min(1).max(200).optional() });
export const CreateThreadResponse = z.object({ threadId: ThreadId });
export type CreateThreadResponse = z.infer<typeof CreateThreadResponse>;

export const ThreadMessage = z.object({
  role: z.enum(['user', 'assistant']),
  content: z.string(),
  sources: z.array(Source).optional(),
  answerId: AnswerId.optional(),
  done: DoneEvent.partial().optional(),
  createdAt: z.string().datetime().optional()
});
export type ThreadMessage = z.infer<typeof ThreadMessage>;

export const GetThreadResponse = z.object({
  threadId: ThreadId.optional(),
  title: z.string().optional(),
  messages: z.array(ThreadMessage)
});
export type GetThreadResponse = z.infer<typeof GetThreadResponse>;

export const ListThreadsResponse = z.object({
  threads: z.array(
    z.object({ threadId: ThreadId, title: z.string(), createdAt: z.string().datetime() })
  )
});
export type ListThreadsResponse = z.infer<typeof ListThreadsResponse>;

/** How the router picks retrieval: web, the Space's documents, or its own decision. */
export const AskMode = z.enum(['auto', 'web', 'docs']);
export type AskMode = z.infer<typeof AskMode>;

export const AskBody = z.object({
  query: z.string().min(1, 'query is required').max(2000),
  /** Where to look. */
  mode: AskMode.default('auto'),
  /**
   * How hard to look. Defaults to quick on purpose: deep costs several times as much, so
   * it is something a user opts into, never somewhere the server drifts.
   */
  depth: Depth.default('quick'),
  spaceId: SpaceId.optional()
});
export type AskBody = z.input<typeof AskBody>;

// ---------------------------------------------------------------- memory

export const Memory = z.object({
  id: MemoryId,
  text: z.string().min(1),
  sourceThread: ThreadId.optional(),
  createdAt: z.string().datetime()
});
export type Memory = z.infer<typeof Memory>;

export const ListMemoryResponse = z.object({ memories: z.array(Memory) });
export type ListMemoryResponse = z.infer<typeof ListMemoryResponse>;

// ---------------------------------------------------------------- spaces & documents

export const CreateSpaceBody = z.object({ name: z.string().min(1).max(120) });
export const CreateSpaceResponse = z.object({ spaceId: SpaceId, name: z.string() });
export type CreateSpaceResponse = z.infer<typeof CreateSpaceResponse>;

export const ListSpacesResponse = z.object({
  spaces: z.array(z.object({ spaceId: SpaceId, name: z.string(), createdAt: z.string().datetime() }))
});
export type ListSpacesResponse = z.infer<typeof ListSpacesResponse>;

/** pending → parsing → embedding → indexed, or failed. `indexed` only after the probe. */
export const DocStatus = z.enum(['pending', 'parsing', 'embedding', 'indexed', 'failed']);
export type DocStatus = z.infer<typeof DocStatus>;

export const UploadDocumentResponse = z.object({
  docId: DocId,
  status: z.literal('pending')
});
export type UploadDocumentResponse = z.infer<typeof UploadDocumentResponse>;

export const DocumentRow = z.object({
  docId: DocId,
  title: z.string(),
  status: DocStatus,
  pct: z.number().min(0).max(100),
  pages: z.number().int().positive().optional(),
  chunks: z.number().int().nonnegative().optional(),
  error: z.string().optional()
});
export type DocumentRow = z.infer<typeof DocumentRow>;

export const ListDocumentsResponse = z.object({ documents: z.array(DocumentRow) });
export type ListDocumentsResponse = z.infer<typeof ListDocumentsResponse>;

export const MAX_UPLOAD_BYTES = 25 * 1024 * 1024;
export const ACCEPTED_UPLOAD_TYPES = [
  'application/pdf',
  'text/markdown',
  'text/plain'
] as const;

// ---------------------------------------------------------------- health & stats

export const HealthResponse = z.object({
  status: z.enum(['ok', 'degraded']),
  model: z.string().min(1),
  searchProvider: z.enum(['tavily', 'serpapi']),
  vectorStore: z.enum(['atlas-vector-search', 'mongo-cosine-scan']),
  db: z.enum(['ok', 'down']),
  /** The gateway nests the agent service's own /health here. */
  ai: z.object({ status: z.enum(['ok', 'down']) }).passthrough().optional(),
  version: z.string().optional()
});
export type HealthResponse = z.infer<typeof HealthResponse>;

export const StatsResponse = z.object({
  requests: z.number().int().nonnegative(),
  answers: z.number().int().nonnegative(),
  searchCacheHitRatePct: z.number().min(0).max(100),
  ttftP95Ms: z.number().nonnegative(),
  costUsdToday: z.number().nonnegative(),
  /** Deep searches this user has spent today, and the cap that stops them. */
  deepToday: z.number().int().nonnegative(),
  deepDailyCap: z.number().int().nonnegative()
});
export type StatsResponse = z.infer<typeof StatsResponse>;

// ---------------------------------------------------------------- route table

/**
 * The routes the UI calls, in one place, so a skeleton can register all of them as 501
 * and the bench can walk them. `auth: false` means no X-User-Id required.
 */
export const ROUTES = [
  { method: 'GET', path: '/health', auth: false },
  { method: 'GET', path: '/stats', auth: true },
  { method: 'GET', path: '/evals/report.json', auth: false },
  { method: 'POST', path: '/threads', auth: true },
  { method: 'GET', path: '/threads', auth: true },
  { method: 'GET', path: '/threads/:threadId', auth: true },
  { method: 'POST', path: '/threads/:threadId/ask', auth: true },
  { method: 'GET', path: '/memory', auth: true },
  { method: 'DELETE', path: '/memory/:memoryId', auth: true },
  { method: 'POST', path: '/spaces', auth: true },
  { method: 'GET', path: '/spaces', auth: true },
  { method: 'POST', path: '/spaces/:spaceId/documents', auth: true },
  { method: 'GET', path: '/spaces/:spaceId/documents', auth: true }
] as const;
export type Route = (typeof ROUTES)[number];

