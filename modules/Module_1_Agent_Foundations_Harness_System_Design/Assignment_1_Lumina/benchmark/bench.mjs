#!/usr/bin/env node
/**
 * LUMINA benchmark. PROVIDED — do not edit it, and do not loosen benchmark/sla.json to
 * pass. Zero dependencies: `node benchmark/bench.mjs` and nothing else installed.
 *
 *   node benchmark/bench.mjs                    # the full run, through the gateway
 *   node benchmark/bench.mjs --smoke            # five queries (Gate 2)
 *   node benchmark/bench.mjs --json out.json    # machine-readable, anywhere you like
 *   node benchmark/bench.mjs --target https://your-gateway.fly.dev
 *
 * It measures what the SLA declares and nothing it cannot measure honestly:
 *   latency        TTFT and full-answer percentiles, timed client-side, as a user feels them
 *   grounding      every [n] resolves to a source, and that source's snippet is really in
 *                  the page or chunk it claims — arithmetic, never a judge
 *   recall@5       the gold set against your Space
 *   cache          done.searchCached across a workload that is half repeats
 *   deep search    a plan before retrieval, sub-question attribution, and whether deep
 *                  actually reads more than quick or is just slower
 *   decoupling     search p95 while a 60-page PDF ingests
 *   cost           per gear, from done.costUsd, against the declared price table
 *
 * Writes reports/bench.json (everything) and reports/eval.json (the four metric names
 * quality/check.mjs reads). Exits 1 on any missed target, 2 if the target is unusable.
 */
import { readFileSync, writeFileSync, mkdirSync, readdirSync, existsSync } from 'node:fs';
import { dirname, join, resolve, basename, extname } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  ask,
  citationNumbers,
  costOf,
  HttpError,
  makeClient,
  makePdf,
  mean,
  percentile,
  pool,
  round,
  sleep,
  snippetIsGrounded
} from './lib.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, '..');

const argv = process.argv.slice(2);
const has = (f) => argv.includes(f);
const val = (f, d) => {
  const i = argv.indexOf(f);
  return i > -1 && argv[i + 1] ? argv[i + 1] : d;
};

const SMOKE = has('--smoke');
const sla = JSON.parse(readFileSync(join(HERE, 'sla.json'), 'utf8'));
const queries = JSON.parse(readFileSync(join(HERE, 'queries.json'), 'utf8'));
const target = val('--target', process.env.BENCH_TARGET ?? sla.target);
const userId = val('--user', sla.user_id ?? 'bench');
const client = makeClient({ target, userId });

const W = sla.workload ?? {};
const S = sla.sla ?? {};
const PRICES = sla.cost_model ?? {};

const say = (...a) => console.log(...a);
const hr = () => say('─'.repeat(74));

/** Everything the run learns, in one place, so the report is a dump rather than a story. */
const M = {
  answers: [],
  accept202Ms: [],
  deep: { runs: [], quickBaseline: new Map() },
  searchMsIdle: [],
  searchMsDuringIngest: [],
  errors: 0,
  requests: 0,
  grounding: { checked: 0, grounded: 0, unverifiable: 0, dangling: 0 },
  recall: { asked: 0, hit: 0 },
  contract: [],
  /**
   * The repeat workload alone. The cache hit rate is a property of THAT workload — not of
   * document questions that never search the web, and not of the deep phase's one-off
   * baselines. Anything else averaged in here is a number about something else.
   */
  webAnswers: [],
  notes: [],
  stats: null,
  health: null,
  /** Per-rubric-row evidence, so eval/build-report.mjs scores from measurements, not prose. */
  caps: {}
};

/** Record one checkable capability with the evidence that settled it. */
const cap = (name, ok, evidence) => {
  M.caps[name] = { ok: Boolean(ok), evidence: String(evidence) };
  return ok;
};

const fail = (msg) => {
  console.error(`\n✗ ${msg}`);
  process.exit(2);
};

// ---------------------------------------------------------------- phase 0: preflight

async function preflight() {
  hr();
  say(`target   ${target}`);
  say(`mode     ${SMOKE ? 'smoke (Gate 2)' : 'full'}`);

  // A degraded /health is information, not a transport failure, so read the body either way.
  let healthStatus = 0;
  try {
    const res = await client.raw('GET', '/health');
    healthStatus = res.status;
    M.health = await res.json().catch(() => ({}));
  } catch (err) {
    fail(`could not reach ${target}/health: ${err.message}\n  Is the gateway running? Is --target right?`);
  }

  if (!M.health?.model) {
    fail(
      `GET /health returned ${healthStatus} without the declared shape.\n` +
        '  It must name model, searchProvider, vectorStore and db (contract HealthResponse).'
    );
  }

  say(
    `health   ${M.health.model} · ${M.health.searchProvider} · ${M.health.vectorStore} · db ${M.health.db}` +
      (healthStatus === 200 ? '' : `  (HTTP ${healthStatus})`)
  );

  if (M.health.db !== 'ok') {
    fail(
      'health reports db is not ok, so nothing can persist and every number below would be\n' +
        '  meaningless. Fix MONGODB_URI first: `node scripts/create-indexes.mjs --status`.'
    );
  }
  if (M.health.ai && M.health.ai.status !== 'ok') {
    M.notes.push('the gateway reports the agent service down — expect every ask to fail');
  }
  hr();

  // Contract probes that need no LLM spend. These are cheap and catch the classic misses.
  const probe = async (label, fn, want) => {
    let got;
    try {
      const res = await fn();
      got = res.status;
    } catch (err) {
      got = err instanceof HttpError ? err.status : 0;
    }
    const ok = got === want;
    M.contract.push({ check: label, want, got, ok });
    say(`  ${ok ? '✓' : '✗'} ${label} → ${got} (want ${want})`);
    return ok;
  };

  say('contract probes');
  // 401 without X-User-Id: the one auth rule, on a route that is not /health.
  await probe('GET /memory without X-User-Id', () => client.raw('GET', '/memory', { headers: { 'x-user-id': '' } }), 401);
  await probe('GET /threads/thr_nope (unknown id)', () => client.raw('GET', '/threads/thr_nope'), 404);
  await probe('POST /threads/thr_x/ask with an empty body', () =>
    client.raw('POST', '/threads/thr_x/ask', { body: {} }), 400);

  // The grader's tooling pulls this with no header, so it must not be behind the user check.
  {
    let status = 0;
    try {
      status = (await client.raw('GET', '/evals/report.json', { headers: { 'x-user-id': '' } })).status;
    } catch (err) {
      status = err instanceof HttpError ? err.status : 0;
    }
    const ok = status !== 401;
    M.contract.push({ check: 'GET /evals/report.json without X-User-Id', want: 'not 401', got: status, ok });
    say(`  ${ok ? '✓' : '✗'} GET /evals/report.json without X-User-Id → ${status} (must not be 401)`);
  }

  cap(
    'contractProbes',
    M.contract.every((c) => c.ok),
    M.contract.map((c) => `${c.check}: ${c.got}`).join(' · ')
  );
  cap(
    'healthNames',
    Boolean(M.health.model && M.health.searchProvider && M.health.vectorStore && M.health.db),
    `/health names ${M.health.model} · ${M.health.searchProvider} · ${M.health.vectorStore} · db ${M.health.db}`
  );
  hr();
}

// ---------------------------------------------------------------- grounding

const stripHtml = (html) =>
  html
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&[a-z#0-9]+;/gi, ' ');

/** Full locator identity: two chunks of one document must not share a key. */
const locatorKey = (s) =>
  `${s.docId}:${s.locator?.page ?? ''}:${s.locator?.heading ?? ''}:${s.locator?.line ?? ''}`;

const pageCache = new Map();

async function fetchPageText(url) {
  if (pageCache.has(url)) return pageCache.get(url);
  let text = null;
  try {
    const res = await fetch(url, {
      redirect: 'follow',
      headers: { 'user-agent': 'lumina-bench/0.1 (+course benchmark)' },
      signal: AbortSignal.timeout(12000)
    });
    if (res.ok) text = stripHtml(await res.text());
  } catch {
    text = null;
  }
  pageCache.set(url, text);
  return text;
}

/**
 * Two questions per answer, and they are different questions:
 *   1. does every [n] in the text resolve to a source in this answer? (no network, hard rule)
 *   2. is that source's snippet actually in the page or chunk it points at?
 *
 * A publisher that 403s the bench makes (2) unverifiable, not false: those are excluded
 * from the ratio and reported separately, because failing an honest citation on a paywall
 * teaches nobody anything. (1) can never be unverifiable.
 */
async function scoreGrounding(answer, docText) {
  const bySource = new Map((answer.sources ?? []).map((s) => [s.n, s]));

  for (const n of citationNumbers(answer.text)) {
    M.grounding.checked++;
    const src = bySource.get(n);
    if (!src) {
      M.grounding.dangling++;
      continue; // counted, never grounded: this is the automatic-fail case
    }
    if (src.kind === 'doc') {
      // Key by document AND page: two PDFs both have a page 1, and keying on the page
      // alone made one document's chunk the haystack for the other's citation.
      const hay = docText?.get(locatorKey(src)) ?? docText?.get('*') ?? null;
      if (!hay) M.grounding.unverifiable++;
      else if (snippetIsGrounded(src.snippet, hay)) M.grounding.grounded++;
      continue;
    }
    const page = src.url ? await fetchPageText(src.url) : null;
    if (!page) M.grounding.unverifiable++;
    else if (snippetIsGrounded(src.snippet, page)) M.grounding.grounded++;
  }
}

// ---------------------------------------------------------------- phase 1: web workload

function buildWorkload() {
  if (SMOKE) return queries.smoke.slice(0, 5);
  const distinct = queries.web;
  const total = W.web_queries ?? 40;
  const repeats = Math.round(total * (W.repeat_fraction ?? 0.5));
  const fresh = total - repeats;
  const out = [];
  for (let i = 0; i < fresh; i++) out.push(distinct[i % distinct.length]);
  // Repeats are deliberate: a cache that never gets a second chance cannot be measured.
  for (let i = 0; i < repeats; i++) out.push(out[i % Math.max(1, fresh)]);
  return out;
}

async function runWebWorkload() {
  const work = buildWorkload();
  say(`web workload: ${work.length} queries, concurrency ${SMOKE ? 1 : (W.concurrency ?? 4)}`);

  const thread = await client.post('/threads', {}).catch((err) => fail(`POST /threads failed: ${err.message}`));
  const threadId = thread.threadId;

  const tasks = work.map((query) => async () => {
    M.requests++;
    const t0 = Date.now();
    const res = await ask(client, threadId, { query, mode: 'web', userId });
    M.searchMsIdle.push(Date.now() - t0);
    return res;
  });

  const results = await pool(tasks, SMOKE ? 1 : (W.concurrency ?? 4));
  const webAnswers = [];

  for (const r of results) {
    if (!r.ok) {
      M.errors++;
      const status = r.error instanceof HttpError ? r.error.status : 0;
      M.notes.push(`ask failed (${status || 'network'}): ${r.error.message}`);
      continue;
    }
    const a = r.value;
    if (a.error) M.errors++;
    M.answers.push(a);
    webAnswers.push(a);
    await scoreGrounding(a, null);
  }
  M.webAnswers = webAnswers;

  const done = M.answers.filter((a) => a.done);
  say(`  ${done.length}/${work.length} answered · ${M.errors} error(s)`);
  if (!done.length) fail('no answer completed — build the ask route before benchmarking it');
}

// ---------------------------------------------------------------- phase 2: RAG & recall@5

function goldCorpusFiles() {
  const dir = join(ROOT, 'eval', 'gold', 'corpus');
  if (!existsSync(dir)) return [];
  return readdirSync(dir)
    .filter((f) => ['.pdf', '.md', '.txt'].includes(extname(f).toLowerCase()))
    .map((f) => join(dir, f));
}

const MIME = { '.pdf': 'application/pdf', '.md': 'text/markdown', '.txt': 'text/plain' };

async function uploadAndWait(spaceId, path, { timeoutMs = 240000 } = {}) {
  const buf = readFileSync(path);
  const form = new FormData();
  form.append('file', new Blob([buf], { type: MIME[extname(path).toLowerCase()] }), basename(path));

  const t0 = Date.now();
  const res = await client.post(`/spaces/${spaceId}/documents`, form);
  const acceptMs = Date.now() - t0;
  M.accept202Ms.push(acceptMs);

  const deadline = Date.now() + timeoutMs;
  for (;;) {
    const { documents } = await client.get(`/spaces/${spaceId}/documents`);
    const row = documents.find((d) => d.docId === res.docId);
    if (row?.status === 'indexed') return { ...row, acceptMs };
    if (row?.status === 'failed') throw new Error(`indexing failed: ${row.error ?? 'no error string'}`);
    if (Date.now() > deadline) throw new Error(`still ${row?.status ?? 'missing'} after ${timeoutMs}ms`);
    await sleep(1200);
  }
}

async function runRag() {
  const goldPath = join(ROOT, 'eval', 'gold', 'rag_gold.jsonl');
  const files = goldCorpusFiles();
  if (!files.length || !existsSync(goldPath)) {
    M.notes.push('no gold corpus or gold set found — recall@5 skipped');
    return;
  }

  const space = await client.post('/spaces', { name: `bench-${Date.now()}` });
  say(`rag: space ${space.spaceId}, ${files.length} corpus file(s)`);

  const indexed = [];
  for (const f of files) {
    try {
      const row = await uploadAndWait(space.spaceId, f);
      indexed.push({ file: basename(f), ...row });
      say(`  ✓ ${basename(f)} → indexed (202 in ${row.acceptMs}ms${row.pages ? `, ${row.pages} pages` : ''})`);
    } catch (err) {
      M.notes.push(`${basename(f)}: ${err.message}`);
      say(`  ✗ ${basename(f)} — ${err.message}`);
    }
  }
  if (!indexed.length) {
    M.notes.push('nothing indexed — recall@5 cannot be measured');
    return;
  }

  const gold = readFileSync(goldPath, 'utf8')
    .split('\n')
    .filter((l) => l.trim())
    .map((l) => JSON.parse(l));

  const items = SMOKE ? gold.slice(0, 3) : gold.slice(0, W.doc_queries_from_gold ?? gold.length);
  say(`  recall@5 over ${items.length} gold question(s)`);

  const titleOf = (docId) => indexed.find((d) => d.docId === docId)?.title ?? '';

  for (const item of items) {
    M.requests++;
    let a;
    try {
      const thread = await client.post('/threads', {});
      a = await ask(client, thread.threadId, {
        query: item.question,
        mode: 'docs',
        spaceId: space.spaceId,
        userId
      });
    } catch (err) {
      M.errors++;
      M.notes.push(`gold ${item.id}: ${err.message}`);
      continue;
    }
    if (a.error) M.errors++;
    M.answers.push(a);

    // The `sources` event IS the retrieval surface: top-5 of it is what recall@5 means here.
    const top5 = (a.sources ?? []).filter((s) => s.kind === 'doc').slice(0, 5);
    M.recall.asked++;
    const hit = top5.some((s) => {
      // A learner's `title` may be the filename or the PDF's own title, so compare stems
      // loosely rather than failing a correct retrieval on punctuation.
      const stem = (v) => String(v ?? '').toLowerCase().replace(/\.(pdf|md|txt)$/, '').replace(/[^a-z0-9]/g, '');
      const want = stem(item.doc);
      const candidates = [stem(s.title), stem(titleOf(s.docId))].filter(Boolean);
      const docOk = !want || candidates.some((c) => c.includes(want) || want.includes(c));
      if (!docOk) return false;
      if (item.page) return s.locator?.page === item.page;
      if (item.anchor) return snippetIsGrounded(item.anchor, s.snippet, 6);
      return true;
    });
    if (hit) M.recall.hit++;

    // Grounding for doc citations is checked against the chunk text the answer returned.
    const docText = new Map([['*', top5.map((s) => s.snippet).join('\n')]]);
    for (const s of top5) docText.set(locatorKey(s), s.snippet);
    await scoreGrounding(a, docText);
  }
  say(`  recall@5 ${M.recall.hit}/${M.recall.asked}`);

  const accept = percentile(M.accept202Ms, 95);
  cap('accept202', accept !== null && accept <= (S.accept_202_p95_ms ?? 300), `202 accept p95 ${accept}ms`);
  cap(
    'indexedViaWorker',
    indexed.length > 0,
    `${indexed.length}/${files.length} corpus file(s) reached indexed after a 202`
  );

  const docSources = M.answers.flatMap((a) => (a.sources ?? []).filter((x) => x.kind === 'doc'));
  const withPage = docSources.filter((x) => x.locator?.page);
  cap(
    'pageLocator',
    withPage.length > 0,
    withPage.length
      ? `${withPage.length} document citation(s) carry a page locator, e.g. p. ${withPage[0].locator.page}`
      : 'no document citation carried a page locator'
  );

  // mode:auto has to reach for the documents on its own when the Space holds the answer.
  try {
    const autoThread = await client.post('/threads', {});
    const auto = await ask(client, autoThread.threadId, {
      query: gold[0].question,
      mode: 'auto',
      spaceId: space.spaceId,
      userId
    });
    M.requests++;
    M.answers.push(auto);
    const pickedDocs = (auto.sources ?? []).some((x) => x.kind === 'doc');
    const routerStep = (auto.trace ?? []).find((t) => t.tool === 'search_documents');
    cap(
      'routerPicksDocs',
      pickedDocs,
      pickedDocs
        ? `mode=auto retrieved from the Space${routerStep?.reason ? ` — "${routerStep.reason}"` : ''}`
        : 'mode=auto never touched the Space on a corpus question'
    );
  } catch (err) {
    cap('routerPicksDocs', false, `mode=auto failed: ${err.message}`);
  }

  return space.spaceId;
}

// ---------------------------------------------------------------- phase 3: ingest decoupling

async function runIngestDecoupling(spaceId) {
  if (SMOKE || !spaceId) return;
  const pages = W.ingest_during_search_pdf_pages ?? 60;
  say(`decoupling: ingesting a ${pages}-page PDF while searching`);

  const form = new FormData();
  form.append('file', new Blob([makePdf(pages)], { type: 'application/pdf' }), `bench-${pages}p.pdf`);

  const t0 = Date.now();
  const upload = await client.post(`/spaces/${spaceId}/documents`, form).catch((err) => {
    M.notes.push(`decoupling upload failed: ${err.message}`);
    return null;
  });
  if (!upload) return;
  M.accept202Ms.push(Date.now() - t0);

  // Hammer search while the worker chews on it. If the parse is on the request thread,
  // these get slow, and that is the whole point of the measurement.
  const thread = await client.post('/threads', {});
  const probes = queries.smoke.slice(0, 4).map((query) => async () => {
    const s = Date.now();
    await ask(client, thread.threadId, { query, mode: 'web', userId });
    M.searchMsDuringIngest.push(Date.now() - s);
  });
  await pool(probes, 2);

  const idle = percentile(M.searchMsIdle, 95);
  const busy = percentile(M.searchMsDuringIngest, 95);
  say(`  search p95 idle ${idle}ms · during ingest ${busy}ms`);
}

// ---------------------------------------------------------------- phase 4: deep search

/**
 * Deep search, judged the way a user would judge it: did it say what it was going to look
 * for, did it look in more places than the cheap gear, and did it stay inside its budget?
 *
 * Every check here is arithmetic on the stream. None of them asks whether the prose is
 * good — that is the manual row, and a person does it.
 */
async function runDeepSearch() {
  if (SMOKE) return;
  const count = W.deep_queries ?? 4;
  const questions = (queries.deep ?? []).slice(0, count);
  if (!questions.length) {
    M.notes.push('no deep queries in benchmark/queries.json — deep search unmeasured');
    return;
  }

  // A fresh user per run: the deep daily cap is per X-User-Id, and a bench that spends the
  // declared user's allowance fails its own second run of the day. The cap gets its own
  // probe below, with its own throwaway user.
  const deepUser = `${userId}-deep-${Date.now().toString(36)}`;
  const deepClient = makeClient({ target, userId: deepUser });

  say(`deep search: ${questions.length} multi-part question(s), each run quick then deep`);

  for (const query of questions) {
    // The same question at both depths, so "deeper" is a measurement and not a claim.
    try {
      const quickThread = await deepClient.post('/threads', {});
      const quick = await ask(deepClient, quickThread.threadId, { query, mode: 'web', depth: 'quick', userId: deepUser });
      M.requests++;
      if (quick.error) M.errors++;
      M.answers.push(quick);
      // NOT pushed into M.webAnswers: these baselines are one-off fresh queries, and the
      // cache hit rate is declared against the repeat workload. Counting them would let a
      // phase that has nothing to do with caching fail the caching SLA.
      await scoreGrounding(quick, null);
      M.deep.quickBaseline.set(query, distinctSources(quick));
    } catch (err) {
      M.errors++;
      M.notes.push(`deep baseline (quick) failed: ${err.message}`);
      continue;
    }

    try {
      const thread = await deepClient.post('/threads', {});
      const deep = await ask(deepClient, thread.threadId, { query, mode: 'web', depth: 'deep', userId: deepUser });
      M.requests++;
      if (deep.error) M.errors++;
      M.answers.push(deep);
      await scoreGrounding(deep, null);
      M.deep.runs.push({ query, run: deep });

      const subs = deep.plan?.subQuestions?.length ?? 0;
      const gain = M.deep.quickBaseline.get(query)
        ? distinctSources(deep) / M.deep.quickBaseline.get(query)
        : null;
      say(
        `  ${deep.done ? '✓' : '✗'} ${subs} sub-question(s) · plan in ${deep.planMs ?? '—'}ms · ` +
          `${distinctSources(deep)} sources (${gain ? `${gain.toFixed(1)}x quick` : 'no baseline'}) · ` +
          `${((deep.latencyMs ?? 0) / 1000).toFixed(1)}s · $${deep.done?.costUsd ?? '?'}`
      );
    } catch (err) {
      if (err instanceof HttpError && err.status === 429) {
        // The cap doing its job is not an error; it is the gate this bench also checks.
        M.notes.push(
          `deep search hit the daily cap after ${M.deep.runs.length} run(s) — raise DEEP_DAILY_CAP ` +
            `above workload.deep_queries (${count}) to measure them all`
        );
        say(`  · deep cap reached after ${M.deep.runs.length} run(s)`);
        break;
      }
      M.errors++;
      M.notes.push(`deep search failed: ${err.message}`);
      say(`  ✗ deep — ${err.message}`);
    }
  }

  scoreDeep();
  await probeDeepCap();
}

const distinctSources = (a) =>
  new Set((a.sources ?? []).map((s) => s.url ?? `${s.docId}:${s.locator?.page ?? s.locator?.heading ?? ''}`)).size;

function scoreDeep() {
  const runs = M.deep.runs.filter((r) => r.run.done);
  if (!runs.length) {
    cap('deepPlan', false, 'no deep search completed');
    cap('deepAttribution', false, 'no deep search completed');
    cap('deepReadsMore', false, 'no deep search completed');
    cap('deepBudget', false, 'no deep search completed');
    return;
  }

  const minSubs = S.min_deep_sub_questions ?? 3;
  const planned = runs.filter((r) => (r.run.plan?.subQuestions?.length ?? 0) >= minSubs);
  const ordered = runs.filter((r) => r.run.planBeforeRetrieval === true);
  cap(
    'deepPlan',
    planned.length === runs.length && ordered.length === runs.length,
    `${planned.length}/${runs.length} deep runs planned >= ${minSubs} sub-questions, ` +
      `${ordered.length}/${runs.length} streamed the plan before retrieving anything`
  );

  /**
   * Attribution: a merged source list nobody can trace back to a sub-question is a pile.
   *
   * Only the FAN-OUT is attributable. `plan_research` serves the whole question, and a
   * `recall_memory` before planning serves no sub-question at all — requiring an index on
   * those would fail a correct implementation, so this looks at retrieval steps only.
   */
  const RETRIEVAL = ['web_search', 'fetch_page', 'search_documents'];
  const attributed = runs.filter((r) => {
    const steps = (r.run.trace ?? []).filter((t) => RETRIEVAL.includes(t.tool));
    const sources = r.run.sources ?? [];
    return (
      steps.length > 0 &&
      steps.every((t) => Number.isInteger(t.subQuestion)) &&
      sources.length > 0 &&
      sources.every((x) => Number.isInteger(x.subQuestion))
    );
  });
  const missing = runs.length - attributed.length;
  cap(
    'deepAttribution',
    attributed.length === runs.length,
    attributed.length === runs.length
      ? `all ${runs.length} deep runs tag every retrieval step and every source with its subQuestion`
      : `${missing}/${runs.length} deep run(s) left subQuestion off a retrieval step or a source`
  );

  const ratios = runs
    .map((r) => {
      const base = M.deep.quickBaseline.get(r.query);
      return base ? distinctSources(r.run) / base : null;
    })
    .filter((v) => v !== null);
  const worst = ratios.length ? Math.min(...ratios) : null;
  const wantRatio = S.min_deep_source_ratio ?? 2;
  cap(
    'deepReadsMore',
    worst !== null && worst >= wantRatio,
    worst === null
      ? 'no quick baseline to compare against'
      : `worst deep/quick distinct-source ratio ${worst.toFixed(2)}x (need ${wantRatio}x)`
  );

  const costCap = S.max_cost_per_deep_answer_usd ?? 0.35;
  const overCost = runs.filter((r) => (r.run.done.costUsd ?? 0) > costCap);
  const callCap = 24;
  const overCalls = runs.filter((r) => (r.run.trace ?? []).length > callCap);
  cap(
    'deepBudget',
    overCost.length === 0 && overCalls.length === 0,
    `${overCost.length} deep run(s) over $${costCap}, ${overCalls.length} over ${callCap} tool calls`
  );

  // The escalation check: a quick search must never reach for the planner on its own.
  const quickRuns = M.answers.filter((a) => a.depth === 'quick');
  const escalated = quickRuns.filter((a) => (a.trace ?? []).some((t) => t.tool === 'plan_research'));
  cap(
    'quickNeverEscalates',
    escalated.length === 0,
    escalated.length
      ? `${escalated.length} quick run(s) called plan_research — depth must be opted into, not drifted into (R2)`
      : `${quickRuns.length} quick run(s), none called plan_research`
  );

  // The quick gear also has to stay in ITS envelope, which expectations.json cannot express.
  const quickDone = quickRuns.filter((a) => a.done);
  const quickOver = quickDone.filter(
    (a) => (a.done.costUsd ?? 0) > (S.max_cost_per_answer_usd ?? 0.05) || (a.trace ?? []).length > 8
  );
  cap(
    'quickBudget',
    quickOver.length === 0,
    `${quickOver.length}/${quickDone.length} quick run(s) exceeded $${S.max_cost_per_answer_usd ?? 0.05} or 8 tool calls`
  );
}

/**
 * The spend gate. Deep search is the expensive operation now, so it is the one that needs
 * a cap: a documented cap that is not enforced server-side is not a cap. Throwaway user,
 * so it cannot exhaust the real one.
 */
async function probeDeepCap() {
  const stats = M.stats ?? (await client.get('/stats').catch(() => ({})));
  const limit = Number(stats?.deepDailyCap ?? 5);
  const user = `${userId}-deepcap-${Date.now().toString(36)}`;
  const capClient = makeClient({ target, userId: user });

  try {
    const thread = await capClient.post('/threads', {});
    for (let i = 0; i < limit + 2; i++) {
      try {
        // A cheap question: the point is the counter, not the answer.
        await ask(capClient, thread.threadId, {
          query: `cap probe ${i}: what is reciprocal rank fusion?`,
          mode: 'web',
          depth: 'deep',
          userId: user
        });
      } catch (err) {
        if (err instanceof HttpError && err.status === 429) {
          // A 429 without resetsAt tells a client to stop and gives it no way to know when
          // to start again, so the contract asks for both and so does this.
          const resets = err.body?.resetsAt;
          cap(
            'deepCap429',
            Boolean(resets),
            `request ${i + 1} of a ${limit}/day deep cap returned 429` +
              (resets ? ` with resetsAt ${resets}` : ' but no resetsAt, which the contract requires')
          );
          return;
        }
        throw err;
      }
    }
    cap('deepCap429', false, `${limit + 2} deep searches all accepted — the daily cap is not enforced server-side`);
  } catch (err) {
    cap('deepCap429', false, `deep cap probe failed: ${err.message}`);
  }
}

// ---------------------------------------------------------------- phase 4b: memory

/**
 * The memory row is graded automatically, and it can be: every step here is arithmetic on
 * a response body or a trace, never a judgement about whether an answer "sounds British".
 *
 *   1. ask thread A to remember a preference   → a row appears in GET /memory
 *   2. ask thread B anything                   → the trace carries a recall_memory step
 *   3. DELETE the row                          → GET /memory no longer lists it
 */
async function runMemory() {
  const user = `${userId}-mem-${Date.now().toString(36)}`;
  const memClient = makeClient({ target, userId: user });
  const PREF = 'Always answer in British English and keep answers under 100 words.';

  try {
    const before = await memClient.get('/memory');
    const a = await ask(memClient, (await memClient.post('/threads', {})).threadId, {
      query: `Remember this preference for all future answers: ${PREF}`,
      mode: 'web',
      userId: user
    });
    M.requests++;
    if (a.error) M.errors++;

    const saveStep = (a.trace ?? []).some((t) => t.tool === 'save_memory' && t.ok);
    const after = await memClient.get('/memory');
    const added = (after.memories ?? []).filter(
      (m) => !(before.memories ?? []).some((b) => b.id === m.id)
    );

    cap(
      'memorySaved',
      added.length > 0,
      added.length
        ? `GET /memory lists ${added.length} new row after the save${saveStep ? ' and the trace shows save_memory' : ' (no save_memory step in the trace)'}`
        : 'no new row in GET /memory after asking it to remember a preference'
    );

    if (!added.length) {
      cap('memoryRecalled', false, 'nothing was saved, so recall could not be tested');
      cap('memoryDeleted', false, 'nothing was saved, so delete could not be tested');
      return;
    }

    // A different thread, same user: recall has to cross the thread boundary.
    const b = await ask(memClient, (await memClient.post('/threads', {})).threadId, {
      query: 'What is the capital of Portugal?',
      mode: 'web',
      userId: user
    });
    M.requests++;
    const recalled = (b.trace ?? []).filter((t) => t.tool === 'recall_memory');
    cap(
      'memoryRecalled',
      recalled.length > 0 && recalled.some((t) => t.ok),
      recalled.length
        ? `a new thread's trace carries ${recalled.length} recall_memory step(s)`
        : 'a new thread never called recall_memory — the preference cannot have crossed threads'
    );

    const target0 = added[0];
    await memClient.del(`/memory/${target0.id}`);
    const afterDelete = await memClient.get('/memory');
    const gone = !(afterDelete.memories ?? []).some((m) => m.id === target0.id);
    cap('memoryDeleted', gone, gone ? `DELETE /memory/${target0.id} removed the row` : 'the row survived its DELETE');
  } catch (err) {
    const status = err instanceof HttpError ? err.status : 0;
    cap('memorySaved', false, `${status || 'network'}: ${err.message}`);
    cap('memoryRecalled', false, 'memory phase did not complete');
    cap('memoryDeleted', false, 'memory phase did not complete');
    M.notes.push(`memory phase: ${err.message}`);
  }
}

// ---------------------------------------------------------------- phase 5: /stats

async function runStats() {
  try {
    M.stats = await client.get('/stats');
  } catch (err) {
    M.notes.push(`GET /stats: ${err.message}`);
    return;
  }
  const ours = M.answers.filter((a) => a.done).length;
  const reconciles = M.stats.answers >= ours;
  if (!reconciles) {
    M.notes.push(`/stats.answers=${M.stats.answers} is below the ${ours} answers this run produced — it does not reconcile`);
  }
  cap('statsReconciles', reconciles, `/stats.answers=${M.stats.answers} against ${ours} answers this run`);

  const echoed = M.answers.filter((a) => a.requestId).length;
  cap(
    'requestIdEchoed',
    echoed === M.answers.length && echoed > 0,
    `${echoed}/${M.answers.length} answers returned an X-Request-Id to correlate the two logs`
  );
}

// ---------------------------------------------------------------- scoring

function computeMetrics() {
  const done = M.answers.filter((a) => a.done);
  // The TTFT and answer SLAs are the quick gear's. Deep has its own, longer, targets, and
  // averaging the two would let a slow quick search hide behind a fast deep one (or vice versa).
  const quickDone = done.filter((a) => a.depth !== 'deep');
  const deepDone = done.filter((a) => a.depth === 'deep');
  const withCites = M.grounding.checked - M.grounding.unverifiable;

  const citationGrounding = withCites > 0 ? M.grounding.grounded / withCites : null;
  const recallAt5 = M.recall.asked ? M.recall.hit / M.recall.asked : null;

  // retrievalRate: the share of answers whose trace actually retrieved something. An
  // answer from the model's own memory is not a cited answer, however good it reads.
  const retrieved = done.filter((a) =>
    (a.trace ?? []).some((t) => t.tool === 'web_search' || t.tool === 'search_documents')
  ).length;
  const retrievalRate = done.length ? retrieved / done.length : null;
  const errorRate = M.requests ? M.errors / M.requests : null;

  const webDone = M.webAnswers.filter((a) => a.done);
  const cacheHits = webDone.filter((a) => a.done.searchCached).length;
  const searchCacheHitRatePct = webDone.length ? (cacheHits / webDone.length) * 100 : null;

  const costPerAnswer = mean(quickDone.map((a) => a.done.costUsd));
  const costPerDeepAnswer = mean(deepDone.map((a) => a.done.costUsd));
  const declaredCost = mean(
    done.map((a) =>
      costOf(
        { tokensIn: a.done.tokens?.in ?? 0, tokensOut: a.done.tokens?.out ?? 0, searches: 1 },
        PRICES
      )
    )
  );

  const idle = percentile(M.searchMsIdle, 95);
  const busy = percentile(M.searchMsDuringIngest, 95);

  return {
    answers: done.length,
    citationGrounding,
    recallAt5,
    retrievalRate,
    errorRate,
    searchCacheHitRatePct,
    latency: {
      ttftP50Ms: percentile(quickDone.map((a) => a.ttftMs), 50),
      ttftP95Ms: percentile(quickDone.map((a) => a.ttftMs), 95),
      answerP50Ms: percentile(quickDone.map((a) => a.latencyMs), 50),
      answerP95Ms: percentile(quickDone.map((a) => a.latencyMs), 95),
      accept202P95Ms: percentile(M.accept202Ms, 95)
    },
    ingestRatio: idle && busy ? busy / idle : null,
    deepPlanP95Ms: percentile(M.deep.runs.map((r) => r.run.planMs), 95),
    deepAnswerP95S: percentile(
      M.deep.runs.filter((r) => r.run.done).map((r) => r.run.latencyMs / 1000),
      95
    ),
    deepSubQuestionsMin: M.deep.runs.length
      ? Math.min(...M.deep.runs.map((r) => r.run.plan?.subQuestions?.length ?? 0))
      : null,
    deepSourceRatioMin: (() => {
      const ratios = M.deep.runs
        .map((r) => {
          const base = M.deep.quickBaseline.get(r.query);
          return base ? distinctSources(r.run) / base : null;
        })
        .filter((v) => v !== null);
      return ratios.length ? Math.min(...ratios) : null;
    })(),
    deepAnswers: M.deep.runs.filter((r) => r.run.done).length,
    cost: {
      meanCostPerAnswerUsd: costPerAnswer,
      meanCostPerDeepAnswerUsd: costPerDeepAnswer,
      declaredPriceTableUsd: declaredCost,
      /** Blended at the declared deep fraction: what the product actually costs to run. */
      projectedMonthlyUsd: costPerAnswer
        ? (costPerAnswer * (1 - (PRICES.monthly_deep_fraction ?? 0)) +
            (costPerDeepAnswer ?? costPerAnswer) * (PRICES.monthly_deep_fraction ?? 0)) *
          (PRICES.monthly_answer_volume ?? 0)
        : null,
      projectedMonthlyNoCacheUsd:
        costPerAnswer && searchCacheHitRatePct !== null
          ? (costPerAnswer + (PRICES.search_usd_per_call ?? 0) * (searchCacheHitRatePct / 100)) *
            (PRICES.monthly_answer_volume ?? 0)
          : null
    },
    orderingOk: done.every((a) => a.sourcesBeforeFirstToken !== false),
    danglingCitations: M.grounding.dangling
  };
}

function assertSla(m) {
  const rows = [];
  const row = (metric, comparator, targetValue, actual, unit = '', note) => {
    const pass =
      actual === null || actual === undefined
        ? false
        : comparator === '<='
          ? actual <= targetValue
          : actual >= targetValue;
    rows.push({ metric, target: targetValue, actual: actual ?? null, unit, comparator, pass, note });
  };

  row('ttft p95', '<=', S.ttft_p95_ms, m.latency.ttftP95Ms, 'ms');
  row('answer p95', '<=', S.answer_p95_ms, m.latency.answerP95Ms, 'ms');
  if (!SMOKE) {
    row('202 accept p95', '<=', S.accept_202_p95_ms, m.latency.accept202P95Ms, 'ms');
    row('search p95 during ingest / idle', '<=', S.search_p95_during_ingest_ratio_max, m.ingestRatio && round(m.ingestRatio), '×');
    row('recall@5', '>=', S.min_recall_at_5, m.recallAt5 && round(m.recallAt5), '');
    row('search cache hit rate', '>=', S.min_search_cache_hit_rate_pct, m.searchCacheHitRatePct && round(m.searchCacheHitRatePct, 1), '%');
    row('deep plan p95', '<=', S.deep_plan_p95_ms, m.deepPlanP95Ms && round(m.deepPlanP95Ms, 0), 'ms');
    row('deep answer p95', '<=', S.deep_answer_p95_s, m.deepAnswerP95S && round(m.deepAnswerP95S, 1), 's');
    row('deep sub-questions (min)', '>=', S.min_deep_sub_questions, m.deepSubQuestionsMin, '');
    row('deep/quick source ratio (min)', '>=', S.min_deep_source_ratio, m.deepSourceRatioMin && round(m.deepSourceRatioMin, 2), '×');
    row('cost per deep answer', '<=', S.max_cost_per_deep_answer_usd, m.cost.meanCostPerDeepAnswerUsd && round(m.cost.meanCostPerDeepAnswerUsd, 4), '$');
  }
  row('citation grounding', '>=', S.min_citation_grounding, m.citationGrounding && round(m.citationGrounding), '');
  row('error rate', '<=', S.max_error_rate_pct / 100, m.errorRate === null ? null : round(m.errorRate, 4), '');
  row('cost per answer (quick)', '<=', S.max_cost_per_answer_usd, m.cost.meanCostPerAnswerUsd && round(m.cost.meanCostPerAnswerUsd, 4), '$');

  // Two contract rules the SLA does not have a number for but the bench can still assert.
  rows.push({
    metric: 'sources before the first token',
    target: 1,
    actual: m.orderingOk ? 1 : 0,
    unit: '',
    comparator: '>=',
    pass: m.orderingOk,
    note: m.orderingOk ? undefined : 'at least one answer streamed a token before its sources event'
  });
  rows.push({
    metric: 'citations with no matching source',
    target: 0,
    actual: m.danglingCitations,
    unit: '',
    comparator: '<=',
    pass: m.danglingCitations === 0,
    note: m.danglingCitations ? 'an ungrounded citation is an automatic fail' : undefined
  });

  return rows;
}

// ---------------------------------------------------------------- main

await preflight();
await runWebWorkload();
const spaceId = await runRag();
await runIngestDecoupling(spaceId);
await runStats();
if (!SMOKE) await runDeepSearch();
if (!SMOKE) await runMemory();

const metrics = computeMetrics();

// The last few rubric rows are arithmetic on the metrics, so they are recorded here.
cap(
  'sourcesBeforeTokens',
  metrics.orderingOk,
  metrics.orderingOk ? 'every answer sent its sources event before its first token' : 'at least one answer streamed text before its sources'
);
cap(
  'groundingMet',
  metrics.citationGrounding !== null && metrics.citationGrounding >= (S.min_citation_grounding ?? 0.95),
  `citation grounding ${metrics.citationGrounding === null ? 'unmeasured' : round(metrics.citationGrounding)} over ${M.grounding.checked - M.grounding.unverifiable} verifiable citations, ${metrics.danglingCitations} dangling`
);
cap(
  'retrievalAlways',
  metrics.retrievalRate !== null && metrics.retrievalRate >= 1,
  `retrieval rate ${metrics.retrievalRate === null ? 'unmeasured' : round(metrics.retrievalRate)} — the share of answers whose run actually searched`
);
cap(
  'searchCacheHits',
  metrics.searchCacheHitRatePct !== null && metrics.searchCacheHitRatePct >= (S.min_search_cache_hit_rate_pct ?? 50),
  `search cache hit rate ${metrics.searchCacheHitRatePct === null ? 'unmeasured' : round(metrics.searchCacheHitRatePct, 1)}% on a workload that is ${Math.round((W.repeat_fraction ?? 0.5) * 100)}% repeats`
);

const slaRows = assertSla(metrics);
const passed = slaRows.every((r) => r.pass) && M.contract.every((c) => c.ok);

hr();
say('SLA');
for (const r of slaRows) {
  const actual = r.actual === null ? '—' : `${r.actual}${r.unit}`;
  say(
    `  ${r.pass ? '✓' : '✗'} ${r.metric.padEnd(34)} ${String(actual).padStart(10)}  (${r.comparator} ${r.target}${r.unit})${r.note ? `  ${r.note}` : ''}`
  );
}

hr();
say(
  `grounding: ${M.grounding.grounded}/${M.grounding.checked - M.grounding.unverifiable} verifiable citations` +
    ` · ${M.grounding.unverifiable} unverifiable (fetch blocked) · ${M.grounding.dangling} dangling`
);
if (metrics.cost.meanCostPerAnswerUsd) {
  say(
    `cost: $${round(metrics.cost.meanCostPerAnswerUsd, 4)}/quick` +
      (metrics.cost.meanCostPerDeepAnswerUsd
        ? ` · $${round(metrics.cost.meanCostPerDeepAnswerUsd, 4)}/deep`
        : '') +
      ` · $${round(metrics.cost.projectedMonthlyUsd, 0)}/month at ${PRICES.monthly_answer_volume} answers ` +
      `blended ${Math.round((PRICES.monthly_deep_fraction ?? 0) * 100)}% deep`
  );
}
if (metrics.deepAnswers) {
  say(
    `deep: ${metrics.deepAnswers} answer(s) · min ${metrics.deepSubQuestionsMin} sub-questions · ` +
      `${round(metrics.deepSourceRatioMin, 2)}x the sources of the same query run quick`
  );
}
if (M.notes.length) {
  say('\nnotes');
  for (const n of [...new Set(M.notes)].slice(0, 20)) say(`  · ${n}`);
}

const report = {
  ranAt: new Date().toISOString(),
  target,
  mode: SMOKE ? 'smoke' : 'full',
  pass: passed,
  health: M.health,
  contract: M.contract,
  sla: slaRows,
  ...metrics,
  grounding: M.grounding,
  recall: M.recall,
  caps: M.caps,
  stats: M.stats,
  notes: [...new Set(M.notes)]
};

mkdirSync(join(ROOT, 'reports'), { recursive: true });
writeFileSync(join(ROOT, 'reports', 'bench.json'), JSON.stringify(report, null, 2));

// reports/eval.json holds exactly the metric names quality/check.mjs looks for (E2).
writeFileSync(
  join(ROOT, 'reports', 'eval.json'),
  JSON.stringify(
    {
      ranAt: report.ranAt,
      target,
      citationGrounding: round(metrics.citationGrounding),
      recallAt5: round(metrics.recallAt5),
      retrievalRate: round(metrics.retrievalRate),
      errorRate: round(metrics.errorRate, 4)
    },
    null,
    2
  )
);

const jsonOut = val('--json', null);
if (jsonOut) writeFileSync(resolve(process.cwd(), jsonOut), JSON.stringify(report, null, 2));

hr();
say(`reports/bench.json + reports/eval.json written`);
say(passed ? '✓ bench passed' : '✗ bench failed: at least one declared target was missed');
process.exit(passed ? 0 : 1);
