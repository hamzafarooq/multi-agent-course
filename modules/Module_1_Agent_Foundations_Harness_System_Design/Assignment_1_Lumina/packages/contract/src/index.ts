/**
 * @lumina/contract — the LUMINA API contract.
 *
 * PROVIDED. DO NOT EDIT. The gateway validates inbound requests with these schemas, the
 * agent service validates the events it emits, and the React UI compiles against the
 * inferred types. One definition, three consumers: drift fails `npm run typecheck`
 * before it fails a learner.
 *
 * Read this package first. Every route, status code, SSE event, and MongoDB document in
 * the PRD is here, and it is the answer to "what exactly am I supposed to return?".
 */
export * from './ids.js';
export * from './sse.js';
export * from './http.js';
export * from './db.js';
export * from './report.js';
