import {
  REQUEST_HEADER,
  USER_HEADER,
  type AskBody,
  type DoneEvent,
  type PlanEvent,
  type Source,
  type StreamErrorEvent,
  type TraceEvent
} from '@lumina/contract';

/**
 * The gateway. The browser never talks to the agent service, and never holds a key.
 * Read defensively: `import.meta.env` is a Vite injection and is absent when this module
 * is imported outside a Vite build (a test, or a server render).
 */
const viteEnv = (import.meta as { env?: Record<string, string | undefined> }).env;
export const API = (viteEnv?.VITE_API_URL ?? '').replace(/\/$/, '');

const USER_KEY = 'lumina.userId';

/** X-User-Id is the whole auth story for this assignment: one header, required everywhere. */
export function userId(): string {
  let id = localStorage.getItem(USER_KEY);
  if (!id) {
    id = `u_${Math.random().toString(36).slice(2, 10)}`;
    localStorage.setItem(USER_KEY, id);
  }
  return id;
}

export function setUserId(id: string): void {
  localStorage.setItem(USER_KEY, id.trim() || 'dev');
}

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
    readonly requestId?: string
  ) {
    super(message);
  }
  /** 501 is not a bug; it is a route the backend has not built yet. */
  get notImplemented(): boolean {
    return this.status === 501;
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    ...init,
    headers: {
      [USER_HEADER]: userId(),
      ...(init.body && !(init.body instanceof FormData) ? { 'content-type': 'application/json' } : {}),
      ...(init.headers ?? {})
    }
  });

  const requestId = res.headers.get(REQUEST_HEADER) ?? undefined;
  if (res.status === 204) return undefined as T;

  const text = await res.text();
  const body = text ? safeJson(text) : null;

  if (!res.ok) throw new ApiError(res.status, errorMessage(body, res), requestId);
  return body as T;
}

/** Prefer the server's own `error` string; fall back to the status line. */
function errorMessage(body: unknown, res: Response): string {
  if (body && typeof body === 'object' && 'error' in body) {
    const value = (body as { error?: unknown }).error;
    if (typeof value === 'string' && value.trim()) return value;
  }
  return `${res.status} ${res.statusText}`;
}

function safeJson(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return { error: text.slice(0, 400) };
  }
}

export const api = {
  health: () => request<Record<string, unknown>>('/health'),
  stats: () => request<Record<string, number>>('/stats'),

  listThreads: () => request<{ threads: { threadId: string; title: string; createdAt: string }[] }>('/threads'),
  createThread: () => request<{ threadId: string }>('/threads', { method: 'POST', body: '{}' }),
  getThread: (id: string) => request<{ messages: unknown[] }>(`/threads/${id}`),

  listMemory: () => request<{ memories: { id: string; text: string; createdAt: string; sourceThread?: string }[] }>('/memory'),
  deleteMemory: (id: string) => request<void>(`/memory/${id}`, { method: 'DELETE' }),

  listSpaces: () => request<{ spaces: { spaceId: string; name: string; createdAt: string }[] }>('/spaces'),
  createSpace: (name: string) =>
    request<{ spaceId: string; name: string }>('/spaces', { method: 'POST', body: JSON.stringify({ name }) }),
  listDocuments: (spaceId: string) =>
    request<{ documents: { docId: string; title: string; status: string; pct: number; pages?: number; error?: string }[] }>(
      `/spaces/${spaceId}/documents`
    ),
  uploadDocument: (spaceId: string, file: File) => {
    const form = new FormData();
    form.append('file', file);
    return request<{ docId: string; status: string }>(`/spaces/${spaceId}/documents`, {
      method: 'POST',
      body: form
    });
  },

  evalsReport: () => request<unknown>('/evals/report.json')
};

// ---------------------------------------------------------------- the ask stream

export interface AskHandlers {
  /** Deep search only, and it arrives first: what the system decided to go and find out. */
  onPlan?: (p: PlanEvent) => void;
  onTrace?: (t: TraceEvent) => void;
  onSources?: (s: Source[]) => void;
  onToken?: (text: string) => void;
  onDone?: (d: DoneEvent) => void;
  onError?: (e: StreamErrorEvent) => void;
}

/**
 * POST the question and read the SSE stream. EventSource cannot POST, so this parses
 * frames by hand: they are separated by a blank line, and each carries `event:` and
 * `data:` lines.
 *
 * If every token shows up at once at the end, the stream is being buffered somewhere —
 * that is a server problem (compression on the ask route, or a proxy), not a UI one.
 */
export async function askStream(
  threadId: string,
  body: AskBody,
  handlers: AskHandlers,
  signal?: AbortSignal
): Promise<void> {
  const res = await fetch(`${API}/threads/${threadId}/ask`, {
    method: 'POST',
    headers: { [USER_HEADER]: userId(), 'content-type': 'application/json' },
    body: JSON.stringify(body),
    signal
  });

  if (!res.ok || !res.body) {
    const text = await res.text().catch(() => '');
    throw new ApiError(
      res.status,
      errorMessage(text ? safeJson(text) : null, res),
      res.headers.get(REQUEST_HEADER) ?? undefined
    );
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let split: number;
    while ((split = buffer.indexOf('\n\n')) !== -1) {
      const frame = buffer.slice(0, split);
      buffer = buffer.slice(split + 2);
      dispatch(frame, handlers);
    }
  }
  if (buffer.trim()) dispatch(buffer, handlers);
}

function dispatch(frame: string, h: AskHandlers): void {
  let event = 'message';
  const dataLines: string[] = [];

  for (const line of frame.split('\n')) {
    if (line.startsWith('event:')) event = line.slice(6).trim();
    else if (line.startsWith('data:')) dataLines.push(line.slice(5).trim());
    // `:` comment lines (keep-alives) are ignored, as the spec says they should be.
  }
  if (!dataLines.length) return;

  let data: unknown;
  try {
    data = JSON.parse(dataLines.join('\n'));
  } catch {
    return;
  }

  switch (event) {
    case 'plan':
      h.onPlan?.(data as PlanEvent);
      break;
    case 'trace':
      h.onTrace?.(data as TraceEvent);
      break;
    case 'sources':
      h.onSources?.(data as Source[]);
      break;
    case 'token':
      h.onToken?.((data as { text: string }).text ?? '');
      break;
    case 'done':
      h.onDone?.(data as DoneEvent);
      break;
    case 'error':
      h.onError?.(data as StreamErrorEvent);
      break;
  }
}
