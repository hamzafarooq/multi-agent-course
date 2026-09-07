# Streaming, Buffering, and the Latency Budget

*LUMINA gold corpus, document 4 of 4. FDE Agent Engineering Bootcamp. CC BY 4.0.*

## Why streaming changes the product

A generated answer takes seconds. Delivered at the end, those seconds are dead air and the
user assumes the page is broken. Delivered as tokens arrive, the same seconds are a machine
visibly working. Nothing about the total time changed; the perceived latency did, and
perceived latency is what a user has an opinion about.

The number that captures this is **time to first token (TTFT)**: from the request leaving
the browser to the first visible character. Total latency decides whether the answer was
worth waiting for. TTFT decides whether anyone waits.

## Server-Sent Events

Server-Sent Events (SSE) is a one-way stream from server to client over ordinary HTTP,
with a text format that is deliberately trivial. A message is a set of lines terminated by
a **blank line**:

    event: token
    data: {"text":"Atlas"}

    event: done
    data: {"latencyMs":6410}

Rules worth memorizing, because every one of them is a bug someone has shipped:

- The frame terminator is a blank line — `\n\n`. Without it the client holds the frame,
  waiting for more, and the stream appears to hang.
- The response content type is `text/event-stream`.
- A line beginning with `:` is a comment, useful as a keep-alive through an idle proxy.
- Multiple `data:` lines in one frame are concatenated with newlines by the client.
- Field names are case sensitive and take no space before the colon, though one space
  after it is conventional and stripped.

SSE goes one direction. It reconnects on its own, carries an id for resumption, and needs
no library on either side. It is the right choice for a streamed answer and the wrong
choice for a conversation both sides talk in — that is what WebSockets are for, at the cost
of a protocol upgrade, a stateful connection, and load-balancer configuration.

One asymmetry to plan for: the browser's `EventSource` API can only issue `GET` requests.
A streamed answer to a `POST` — which is what sending a question is — has to be read with
`fetch` and a manual parse of the response body, which is a dozen lines and no more.

## Buffering is the default, and it is invisible

The failure that costs teams the most time: every token arrives at once, at the end. The
stream is correct, the client is correct, and something between them is holding bytes until
it has enough to be efficient.

The candidates, in the order they are usually guilty:

1. **A compression middleware.** Gzip works on blocks. A middleware compressing the
   response will buffer until it has a block worth compressing, which for small SSE frames
   is the whole response. Compression must be disabled on a streaming route.
2. **The framework's own buffering.** A response that is never explicitly flushed may sit
   in a userspace buffer. After writing a frame, flush it.
3. **A reverse proxy.** nginx and most managed proxies buffer upstream responses by
   default. The header that disables it for nginx-family proxies is
   `X-Accel-Buffering: no`.
4. **Missing cache directives.** `Cache-Control: no-cache, no-transform` tells
   intermediaries not to hold or rewrite the body. `no-transform` is the half that stops a
   proxy from "helpfully" recompressing it.

The reason this is expensive to diagnose is that no error is raised anywhere. The only
symptom is a TTFT equal to the total latency, which reads as "the model is slow". Measuring
TTFT through the same path a user takes — not against the service directly — is what turns
it back into a visible, fixable failure.

## Ordering: metadata before text

If an answer's citations arrive after its text, the interface has to either delay rendering
or render markers it cannot resolve yet, and both look broken. So a streamed answer sends
its sources **before** the first token of text. The client can then render a citation chip
the instant the marker appears.

This is a contract rule, not an optimization, and it is worth testing explicitly: assert
that the sources frame precedes the first token frame in the stream, on every answer.

## Percentiles, not averages

Latency distributions have long right tails, so the mean describes a user who does not
exist. Report percentiles.

- **p50** — the median. Half of requests are faster.
- **p95** — the slow end that people complain about. One request in twenty is worse.
- **p99** — the tail that decides whether a system is trusted at scale.

An average of 800 ms with a p95 of 9 seconds is a system that feels fast in a demo and
unreliable in use. The p95 is the number to put in a service-level agreement, and it must
be declared before the run: a threshold chosen after seeing the results is a description,
not a target.

Nearest-rank is the honest way to compute one on a small sample. With twenty measurements,
p95 is the nineteenth slowest — no interpolation, no smoothing.

## A latency budget

A budget assigns the target to its parts, so a miss has an address. For a retrieval-augmented
answer, the recurring shape:

| Stage | Typical share of TTFT |
|---|---|
| Request validation and routing | a few milliseconds |
| Query planning (one model call) | 200 to 800 ms |
| Retrieval (search, or vector query) | 100 to 500 ms |
| Reading fetched pages | 200 ms to several seconds, and the usual culprit |
| First token of synthesis | 200 to 600 ms |

The step that blows a TTFT budget is almost always the third-party fetch, because it is the
only one whose latency belongs to someone else. Fetching pages in parallel, capping how
many, and capping how long each may take are the three levers. A cache is the fourth, and
the strongest: a repeated query that costs nothing is the only work that is free.

## Decoupling slow work

Some work does not fit in a request at all. Parsing a 60-page PDF, embedding its chunks,
rendering a slide deck, generating an image — all of these take longer than anyone will hold
a connection open for.

The pattern is to accept the work and return immediately: validate the input, write a job
row, respond **202 Accepted** with an id the client can poll. The response should land in
well under a second; a useful gate is a p95 under 300 ms, because the point of the 202 is
that no real work happened before it.

Then the work runs elsewhere — a worker process, a thread pool, a queue consumer — and the
status flips only after it succeeds. Two rules keep this honest. First, a status must never
claim more than has happened: a document is not "indexed" because a write returned. Second,
the worker must not share a thread with the request path. In a single-threaded runtime, a
worker parsing a large file on the main thread stalls every stream in flight, and the
symptom — search latency degrading only during uploads — looks like a database problem.

The measurement that catches it: search p95 while an ingest is running, over search p95
when the system is idle. A correctly decoupled system holds that ratio near 1. A blocking
one shows it immediately, and no amount of profiling the database will explain why.
