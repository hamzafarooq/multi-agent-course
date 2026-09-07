/**
 * Shared helpers for the benchmark. ZERO DEPENDENCIES on purpose: the gates must run with
 * `node` and nothing installed, on a laptop or in CI, against localhost or a deploy.
 */
import { createHash } from 'node:crypto';

// ---------------------------------------------------------------- stats

export const percentile = (values, p) => {
  const xs = values.filter((v) => Number.isFinite(v)).sort((a, b) => a - b);
  if (!xs.length) return null;
  // Nearest-rank: with 20 samples p95 is the 19th, which is what a reader expects.
  const rank = Math.ceil((p / 100) * xs.length);
  return xs[Math.min(xs.length - 1, Math.max(0, rank - 1))];
};

export const mean = (values) => {
  const xs = values.filter(Number.isFinite);
  return xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null;
};

export const round = (n, dp = 3) => (n === null || n === undefined ? null : Number(n.toFixed(dp)));

// ---------------------------------------------------------------- http

export class HttpError extends Error {
  constructor(status, body, requestId) {
    super(`${status}: ${typeof body === 'string' ? body.slice(0, 200) : JSON.stringify(body).slice(0, 200)}`);
    this.status = status;
    this.body = body;
    this.requestId = requestId;
  }
}

export function makeClient({ target, userId, timeoutMs = 120000 }) {
  const base = target.replace(/\/$/, '');

  const call = async (method, path, { body, headers = {}, raw = false, user = userId } = {}) => {
    const isForm = body instanceof FormData;
    const res = await fetch(`${base}${path}`, {
      method,
      headers: {
        'x-user-id': user,
        ...(body && !isForm ? { 'content-type': 'application/json' } : {}),
        ...headers
      },
      body: body === undefined ? undefined : isForm ? body : JSON.stringify(body),
      signal: AbortSignal.timeout(timeoutMs)
    });

    if (raw) return res;
    const text = await res.text();
    let parsed = null;
    try {
      parsed = text ? JSON.parse(text) : null;
    } catch {
      parsed = text;
    }
    if (!res.ok) throw new HttpError(res.status, parsed ?? text, res.headers.get('x-request-id'));
    return parsed;
  };

  return {
    base,
    get: (p, o) => call('GET', p, o),
    post: (p, body, o) => call('POST', p, { ...o, body }),
    del: (p, o) => call('DELETE', p, o),
    raw: (method, p, o) => call(method, p, { ...o, raw: true })
  };
}

/**
 * POST an ask and read the SSE stream, measuring TTFT server-side-blind: the clock starts
 * before the request and stops at the first `token` frame, which is exactly what a user
 * feels. Returns everything the SLA needs plus the raw events for the grounding check.
 */
export async function ask(client, threadId, body, { timeoutMs = 300000 } = {}) {
  const started = Date.now();
  const res = await fetch(`${client.base}/threads/${threadId}/ask`, {
    method: 'POST',
    headers: { 'x-user-id': body.userId ?? 'bench', 'content-type': 'application/json' },
    body: JSON.stringify({
      query: body.query,
      mode: body.mode ?? 'auto',
      depth: body.depth ?? 'quick',
      ...(body.spaceId ? { spaceId: body.spaceId } : {})
    }),
    signal: AbortSignal.timeout(timeoutMs)
  });

  const requestId = res.headers.get('x-request-id');
  if (!res.ok || !res.body) {
    const text = await res.text().catch(() => '');
    let body = text;
    try {
      body = text ? JSON.parse(text) : text;
    } catch {
      // not JSON; the raw text is the most useful thing we have
    }
    throw new HttpError(res.status, body, requestId);
  }

  const out = {
    requestId,
    threadId,
    depth: body.depth ?? 'quick',
    trace: [],
    sources: [],
    text: '',
    done: null,
    error: null,
    plan: null,
    /** Time to the plan event: a deep search's real first paint. */
    planMs: null,
    /** A plan that lands after retrieval has started is a rationalisation, not a plan. */
    planBeforeRetrieval: null,
    ttftMs: null,
    latencyMs: null,
    sourcesBeforeFirstToken: null,
    order: []
  };

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let sawSources = false;
  let sawRetrieval = false;

  const handle = (frame) => {
    let event = 'message';
    const data = [];
    for (const line of frame.split('\n')) {
      if (line.startsWith('event:')) event = line.slice(6).trim();
      else if (line.startsWith('data:')) data.push(line.slice(5).trim());
    }
    if (!data.length) return;
    let parsed;
    try {
      parsed = JSON.parse(data.join('\n'));
    } catch {
      return;
    }
    out.order.push(event);

    if (event === 'plan') {
      out.plan = parsed;
      out.planMs = Date.now() - started;
      out.planBeforeRetrieval = !sawRetrieval;
    } else if (event === 'trace') {
      out.trace.push(parsed);
      if (parsed.tool === 'web_search' || parsed.tool === 'search_documents' || parsed.tool === 'fetch_page') {
        sawRetrieval = true;
      }
    } else if (event === 'sources') {
      out.sources = parsed;
      sawSources = true;
    } else if (event === 'token') {
      if (out.ttftMs === null) {
        out.ttftMs = Date.now() - started;
        // The contract's one ordering rule: chips must be renderable as text arrives.
        out.sourcesBeforeFirstToken = sawSources;
      }
      out.text += parsed.text ?? '';
    } else if (event === 'done') out.done = parsed;
    else if (event === 'error') out.error = parsed;
  };

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let i;
    while ((i = buffer.indexOf('\n\n')) !== -1) {
      handle(buffer.slice(0, i));
      buffer = buffer.slice(i + 2);
    }
  }
  if (buffer.trim()) handle(buffer);

  out.latencyMs = Date.now() - started;
  return out;
}

// ---------------------------------------------------------------- grounding

/**
 * Normalize before comparing, then require a run of consecutive tokens rather than exact
 * snippet equality: quotes, whitespace and ellipses differ between what a page serves and
 * what a model quotes, and failing an honest citation on a curly apostrophe teaches nobody
 * anything. 12 tokens is the declared window (PRD 16).
 */
export const normalize = (s) =>
  String(s ?? '')
    .toLowerCase()
    .replace(/[‘’“”]/g, "'")
    .replace(/[^a-z0-9']+/g, ' ')
    .trim();

export function snippetIsGrounded(snippet, haystack, minTokens = 12) {
  const need = normalize(snippet).split(' ').filter(Boolean);
  const hay = normalize(haystack);
  if (!need.length || !hay) return false;
  if (need.length <= minTokens) return hay.includes(need.join(' '));
  for (let i = 0; i + minTokens <= need.length; i++) {
    if (hay.includes(need.slice(i, i + minTokens).join(' '))) return true;
  }
  return false;
}

export const citationNumbers = (text) => {
  const out = new Set();
  for (const m of String(text).matchAll(/\[(\d{1,3})\]/g)) out.add(Number(m[1]));
  return [...out].sort((a, b) => a - b);
};

// ---------------------------------------------------------------- cost

/** Cost from the declared price table, so a learner's numbers are reproducible. */
export function costOf({ tokensIn = 0, tokensOut = 0, searches = 0, embedTokens = 0, images = 0 }, prices) {
  return (
    (tokensIn / 1e6) * (prices.input_usd_per_mtok ?? 0) +
    (tokensOut / 1e6) * (prices.output_usd_per_mtok ?? 0) +
    (embedTokens / 1e6) * (prices.embedding_usd_per_mtok ?? 0) +
    searches * (prices.search_usd_per_call ?? 0) +
    images * (prices.image_usd_each ?? 0)
  );
}

// ---------------------------------------------------------------- misc

export const sha256 = (s) => createHash('sha256').update(s).digest('hex');

export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/** Run `tasks` with at most `limit` in flight. Keeps concurrency honest without a dep. */
export async function pool(tasks, limit) {
  const results = new Array(tasks.length);
  let next = 0;
  const workers = Array.from({ length: Math.min(limit, tasks.length) }, async () => {
    for (;;) {
      const i = next++;
      if (i >= tasks.length) return;
      try {
        results[i] = { ok: true, value: await tasks[i]() };
      } catch (err) {
        results[i] = { ok: false, error: err };
      }
    }
  });
  await Promise.all(workers);
  return results;
}

/**
 * A valid multi-page PDF, generated at runtime, so the ingest-decoupling check has a real
 * upload with an exact page count and the repo carries no binary fixture.
 */
export function makePdf(pages, title = 'LUMINA bench corpus') {
  const objects = [];
  const add = (body) => objects.push(body) && objects.length;

  const fontId = add('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>');
  const pageIds = [];
  const contentIds = [];

  for (let p = 1; p <= pages; p++) {
    const text =
      `BT /F1 16 Tf 64 720 Td (${title} — page ${p} of ${pages}) Tj ET\n` +
      `BT /F1 11 Tf 64 690 Td (Synthetic page for the ingest decoupling check. ` +
      `Page ${p} marker: bench-page-${p}.) Tj ET`;
    contentIds.push(add(`<< /Length ${text.length} >>\nstream\n${text}\nendstream`));
    pageIds.push(0); // placeholder, filled below
  }

  const pagesId = objects.length + pages + 1;
  for (let p = 0; p < pages; p++) {
    pageIds[p] = add(
      `<< /Type /Page /Parent ${pagesId} 0 R /MediaBox [0 0 612 792] ` +
        `/Resources << /Font << /F1 ${fontId} 0 R >> >> /Contents ${contentIds[p]} 0 R >>`
    );
  }
  const kids = pageIds.map((id) => `${id} 0 R`).join(' ');
  add(`<< /Type /Pages /Kids [${kids}] /Count ${pages} >>`);
  const catalogId = add(`<< /Type /Catalog /Pages ${pagesId} 0 R >>`);

  let pdf = '%PDF-1.4\n';
  const offsets = [];
  objects.forEach((body, i) => {
    offsets[i] = pdf.length;
    pdf += `${i + 1} 0 obj\n${body}\nendobj\n`;
  });
  const xref = pdf.length;
  pdf += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
  for (const off of offsets) pdf += `${String(off).padStart(10, '0')} 00000 n \n`;
  pdf += `trailer\n<< /Size ${objects.length + 1} /Root ${catalogId} 0 R >>\nstartxref\n${xref}\n%%EOF\n`;

  return Buffer.from(pdf, 'latin1');
}
