import type { Response } from 'express';

/**
 * Express buffers Server-Sent Events by default, and so do most proxies. Get these four
 * headers and the flush right or your tokens all arrive at once at the end, which reads
 * as "the model is slow" and fails the TTFT SLA for a reason no profiler will show you.
 *
 * Also: do NOT put `compression()` in front of the ask route.
 */
export function sseHeaders(res: Response): void {
  res.setHeader('Content-Type', 'text/event-stream; charset=utf-8');
  res.setHeader('Cache-Control', 'no-cache, no-transform');
  res.setHeader('Connection', 'keep-alive');
  // nginx / Fly's proxy will otherwise hold the stream until it has a bufferful.
  res.setHeader('X-Accel-Buffering', 'no');
  res.flushHeaders();
}

/** Write one SSE frame and flush it. The blank line terminates the frame; without it the client waits. */
export function sseSend(res: Response, event: string, data: unknown): void {
  res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`);
  // @ts-expect-error `flush` exists when a compression middleware is present; harmless otherwise.
  if (typeof res.flush === 'function') res.flush();
}
