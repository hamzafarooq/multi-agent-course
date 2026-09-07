#!/usr/bin/env node
/**
 * Assemble the Product Evaluation your /evals page renders. PROVIDED — do not edit.
 *
 *   node eval/build-report.mjs --student "Priya Nair" \
 *     --video https://youtu.be/xxxxxxxxxxx \
 *     --design DESIGN.md \
 *     --successful req_7f3a --failing req_9c1b \
 *     --notes "claude-sonnet-5 · tavily · Atlas M0" \
 *     --out reports/report.json
 *
 * Every number comes out of reports/bench.json, reports/quality.json and runs/*.json.
 * Nothing is retyped, nothing is inferred, and no model gets to characterise a result:
 * that is the point. If a file is missing, the row says so rather than guessing.
 *
 * The shape is `EvalsReport` in packages/contract. Serve the output at
 * GET /evals/report.json and the provided UI renders it at /evals.
 */
import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, '..');

const argv = process.argv.slice(2);
const val = (f, d = null) => {
  const i = argv.indexOf(`--${f}`);
  return i > -1 && argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[i + 1] : d;
};

const readJson = (rel) => {
  const p = join(ROOT, rel);
  if (!existsSync(p)) return null;
  try {
    return JSON.parse(readFileSync(p, 'utf8'));
  } catch (err) {
    console.error(`${rel} is not valid JSON: ${err.message}`);
    process.exit(2);
  }
};

const bench = readJson('reports/bench.json');
const quality = readJson('reports/quality.json');
const rubric = readJson('eval/rubric.json');

if (!bench) {
  console.error('reports/bench.json is missing. Run `node benchmark/bench.mjs` first.');
  process.exit(2);
}
if (!quality) {
  console.error('reports/quality.json is missing. Run `node quality/check.mjs .` first.');
  process.exit(2);
}

// A smoke run skips RAG, artifacts and memory, so those rows would score zero and the page
// would understate a working product. Refuse rather than publish a misleading score.
if (bench.mode === 'smoke' && !argv.includes('--allow-smoke')) {
  console.error(
    'reports/bench.json came from a --smoke run, which skips RAG, artifacts and memory.\n' +
      'Run the full bench first:  node benchmark/bench.mjs [--target <url>]\n' +
      '(--allow-smoke overrides, but the score it produces is not submittable.)'
  );
  process.exit(2);
}

const caps = bench.caps ?? {};
/** Evidence is read by a human: 0.867, not 0.8666666666666667. */
const num = (v, dp = 3) => (typeof v === 'number' && Number.isFinite(v) ? Number(v.toFixed(dp)) : v);
const ok = (name) => caps[name]?.ok === true;
const why = (name) => caps[name]?.evidence ?? 'not measured in this run';

// ---------------------------------------------------------------- the design section

/**
 * The five questions. Parsed out of DESIGN.md by heading, because the learner wrote them
 * before the build and should not have to retype them into a flag.
 */
function readDesign(path) {
  const wanted = {
    components: /components?/i,
    responsibilities: /responsibilit/i,
    communication: /communicat/i,
    state: /state/i,
    tradeoffs: /trade[- ]?offs?/i
  };
  const out = {};

  if (path && existsSync(resolve(ROOT, path))) {
    const md = readFileSync(resolve(ROOT, path), 'utf8');
    const sections = [...md.matchAll(/^#{1,4}\s+(.+)$/gm)].map((m, i, all) => ({
      heading: m[1].trim(),
      body: md
        .slice(m.index + m[0].length, all[i + 1] ? all[i + 1].index : undefined)
        .trim()
    }));
    for (const [key, re] of Object.entries(wanted)) {
      const hit = sections.find((s) => re.test(s.heading) && s.body);
      if (hit) out[key] = hit.body;
    }
  }

  const missing = Object.keys(wanted).filter((k) => !out[k]);
  for (const k of missing) {
    out[k] = `MISSING — add a "${k}" section to DESIGN.md and re-run. The design section is graded, and a stranger has to be able to read it.`;
  }
  if (missing.length) {
    console.error(`! design: ${missing.length} of 5 questions unanswered (${missing.join(', ')})`);
  }
  return out;
}

// ---------------------------------------------------------------- trajectories

/**
 * A run log becomes a trajectory: the ordered steps, exactly as they happened.
 *
 * Two folders, and the split matters. `runs/` is the graded workload, and rule A2 fails
 * any run in it that did not terminate as "done". `runs/failing/` is where you keep the
 * run you broke on purpose for rule P1 — a subfolder, so the trajectory rules do not read
 * it and P1 does not end up contradicting A2. Both are searched here.
 */
function readTrajectory(requestId, label) {
  const dirs = [join(ROOT, 'runs'), join(ROOT, 'runs', 'failing')];
  const files = dirs.flatMap((dir) =>
    existsSync(dir)
      ? readdirSync(dir)
          .filter((f) => f.endsWith('.json'))
          .map((f) => ({ dir, name: f }))
      : []
  );

  const hit =
    files.find((f) => f.name === `${requestId}.json`) ??
    files.find((f) => f.name.includes(String(requestId ?? '')));

  if (!requestId || !hit) {
    return {
      requestId: requestId ?? `MISSING-${label}`,
      steps: [],
      notes:
        `MISSING — pass --${label} <requestId> naming a run log in runs/ (or runs/failing/). ` +
        'Rule P1 is the human gate: you read one successful and one failing trajectory, ' +
        'every step, and say what each taught you. It cannot be automated and cannot be skipped.'
    };
  }

  const run = JSON.parse(readFileSync(join(hit.dir, hit.name), 'utf8'));
  return {
    requestId: hit.name.replace(/\.json$/, ''),
    query: run.query,
    terminated: run.terminated,
    steps: (run.toolCalls ?? []).map((t, i) => ({
      step: i + 1,
      tool: t.name,
      ok: t.ok !== false,
      ms: t.ms,
      error: t.error
    })),
    notes:
      val(`${label}-notes`) ??
      'TODO — what did reading this run end to end teach you? Replace this line; a grader reads it.'
  };
}

// ---------------------------------------------------------------- rubric scoring

/**
 * Automated rows are scored from the measurements. A row is all-or-nothing unless it has
 * parts, in which case it scores proportionally and says which part failed — a partial
 * with a reason is more useful to a learner than a zero.
 */
const SCORERS = {
  ui_lights_up_contract: () => [
    ['contract probes (401/404/400)', ok('contractProbes'), why('contractProbes')],
    ['sources before the first token', ok('sourcesBeforeTokens'), why('sourcesBeforeTokens')],
    ['/health names model, provider, store', ok('healthNames'), why('healthNames')]
  ],
  search_cited_answers: () => [
    ['citation grounding >= 0.95', ok('groundingMet'), why('groundingMet')],
    ['retrieval rate = 1.0', ok('retrievalAlways'), why('retrievalAlways')],
    ['search cache hits on repeats', ok('searchCacheHits'), why('searchCacheHits')]
  ],
  memory: () => [
    ['save_memory lands in GET /memory', ok('memorySaved'), why('memorySaved')],
    ['recall crosses into a new thread', ok('memoryRecalled'), why('memoryRecalled')],
    ['DELETE removes it', ok('memoryDeleted'), why('memoryDeleted')]
  ],
  rag_documents: () => [
    ['202 accept p95 < 300ms', ok('accept202'), why('accept202')],
    ['reaches indexed via the worker', ok('indexedViaWorker'), why('indexedViaWorker')],
    ['citation carries a page locator', ok('pageLocator'), why('pageLocator')],
    ['mode=auto picks documents', ok('routerPicksDocs'), why('routerPicksDocs')],
    [
      `recall@5 >= ${bench.sla?.find((r) => r.metric === 'recall@5')?.target ?? 0.7}`,
      bench.sla?.find((r) => r.metric === 'recall@5')?.pass === true,
      `recall@5 ${num(bench.recallAt5) ?? 'unmeasured'} over ${bench.recall?.asked ?? 0} gold questions`
    ]
  ],
  deep_search: () => [
    ['plan streamed before any retrieval', ok('deepPlan'), why('deepPlan')],
    ['every step and source tagged with its sub-question', ok('deepAttribution'), why('deepAttribution')],
    ['deep reads more than quick', ok('deepReadsMore'), why('deepReadsMore')],
    ['deep stays inside its budget', ok('deepBudget'), why('deepBudget')],
    ['quick never escalates to plan_research (R2)', ok('quickNeverEscalates'), why('quickNeverEscalates')],
    ['deep cap+1 returns 429 with resetsAt', ok('deepCap429'), why('deepCap429')]
  ],
  performance_sla: () => [
    ['bench.mjs exits 0', bench.pass === true, `${(bench.sla ?? []).filter((r) => !r.pass).length} SLA target(s) missed`],
    ['the quick gear stayed in its own envelope', ok('quickBudget'), why('quickBudget')],
    [
      'no error-severity quality failure',
      (quality.errors ?? 1) === 0,
      `quality: ${quality.errors} error(s), ${quality.warnings} warning(s) over ${quality.runs} run log(s)`
    ]
  ],
  observability: () => [
    ['one X-Request-Id correlates both logs', ok('requestIdEchoed'), why('requestIdEchoed')],
    ['/stats reconciles with the run', ok('statsReconciles'), why('statsReconciles')],
    [
      'every failed tool call carries an error (A1)',
      quality.results?.find((r) => r.id === 'A1')?.status === 'pass',
      `A1: ${quality.results?.find((r) => r.id === 'A1')?.detail ?? 'no run logs'}`
    ]
  ]
};

const automated = (rubric.automated ?? []).map((row) => {
  const parts = SCORERS[row.id] ? SCORERS[row.id]() : null;
  if (!parts) {
    return {
      id: row.id,
      label: row.label,
      points: row.points,
      awarded: 0,
      status: 'fail',
      evidence: 'no scorer for this rubric id — the rubric and the eval have drifted',
      rules: row.rules ?? []
    };
  }
  const passed = parts.filter(([, good]) => good).length;
  const awarded = Math.round((passed / parts.length) * row.points);
  const failedParts = parts.filter(([, good]) => !good);

  return {
    id: row.id,
    label: row.label,
    points: row.points,
    awarded,
    status: passed === parts.length ? 'pass' : passed === 0 ? 'fail' : 'partial',
    evidence: (failedParts.length ? failedParts : parts)
      .map(([name, good, evidence]) => `${good ? '✓' : '✗'} ${name}: ${evidence}`)
      .join(' · '),
    rules: row.rules ?? []
  };
});

// Manual rows are a grader's to award. Reporting them as 0 would understate the score;
// reporting them as earned would fabricate it. They are marked manual and left open.
const manual = (rubric.manual ?? []).map((row) => ({
  id: row.id,
  label: row.label,
  points: row.points,
  awarded: 0,
  status: 'manual',
  evidence: row.check,
  rules: row.rules ?? []
}));

const redLines = [
  {
    check: 'no fabricated citation in the bench sample (E2)',
    ok: (bench.danglingCitations ?? 0) === 0,
    detail: `${bench.danglingCitations ?? 0} citation(s) resolved to nothing retrieved in that request`
  },
  {
    check: 'no run that hit a cap reported as terminated=done (A2)',
    ok: quality.results?.find((r) => r.id === 'A2')?.status !== 'fail',
    detail: quality.results?.find((r) => r.id === 'A2')?.detail ?? 'not evaluated'
  },
  {
    check: 'plan_research never called from a quick search: depth is opted into, never drifted into (R2)',
    ok: caps.quickNeverEscalates?.ok === true,
    detail: why('quickNeverEscalates')
  },
  {
    check: 'no 2xx answer served on a provider exception (A1)',
    ok: quality.results?.find((r) => r.id === 'A1')?.status === 'pass',
    detail: quality.results?.find((r) => r.id === 'A1')?.detail ?? 'no run logs to read'
  }
];

// ---------------------------------------------------------------- assemble

const slaRow = (metric) => bench.sla?.find((r) => r.metric === metric);

const report = {
  assignment: rubric.assignment ?? 'Assignment 1: LUMINA',
  student: val('student') ?? 'UNNAMED — pass --student "Your Name"',
  repo: val('repo') ?? undefined,
  video: val('video') ?? undefined,
  deployedAt: new Date().toISOString(),
  runNotes: val('notes') ?? undefined,
  design: readDesign(val('design', 'DESIGN.md')),
  gates: (readJson('reports/gates.json')?.gates ?? []).map((g) => ({
    gate: g.gate,
    name: g.name,
    status: g.status,
    detail: g.detail,
    exitCode: g.exitCode
  })),
  rubric: {
    total: rubric.total_points ?? 100,
    awarded: automated.reduce((sum, r) => sum + r.awarded, 0),
    automated,
    manual,
    redLines
  },
  bench: {
    ranAt: bench.ranAt,
    target: bench.target,
    pass: bench.pass,
    sla: bench.sla ?? [],
    citationGrounding: bench.citationGrounding ?? null,
    recallAt5: bench.recallAt5 ?? null,
    retrievalRate: bench.retrievalRate ?? null,
    errorRate: bench.errorRate ?? null,
    latency: bench.latency ?? {},
    cost: bench.cost ?? {},
    searchCacheHitRatePct: bench.searchCacheHitRatePct ?? null,
    answers: bench.answers ?? 0
  },
  quality,
  trajectories: {
    successful: readTrajectory(val('successful'), 'successful'),
    failing: readTrajectory(val('failing'), 'failing')
  }
};

const outPath = resolve(ROOT, val('out', 'reports/report.json'));
mkdirSync(dirname(outPath), { recursive: true });
writeFileSync(outPath, JSON.stringify(report, null, 2));

// ---------------------------------------------------------------- summary

const pad = (s, n) => String(s).padEnd(n);
console.log(`\n${report.assignment} · ${report.student}`);
console.log('─'.repeat(74));
for (const r of automated) {
  const glyph = { pass: '✓', partial: '◐', fail: '✗' }[r.status];
  console.log(`${glyph} ${pad(r.label, 34)} ${String(r.awarded).padStart(3)}/${r.points}`);
}
for (const r of manual) console.log(`☐ ${pad(r.label, 34)}   –/${r.points}  (grader)`);
console.log('─'.repeat(74));
console.log(
  `automated ${report.rubric.awarded}/${automated.reduce((s, r) => s + r.points, 0)} · ` +
    `manual ${manual.reduce((s, r) => s + r.points, 0)} left to a grader · total possible ${report.rubric.total}`
);

const brokenRedLines = redLines.filter((r) => !r.ok);
if (brokenRedLines.length) {
  console.log(`\n✗ ${brokenRedLines.length} RED LINE(S) CROSSED — these are automatic fails:`);
  for (const r of brokenRedLines) console.log(`  · ${r.check}: ${r.detail}`);
}

const ttft = slaRow('ttft p95');
if (ttft) {
  console.log(
    `\nttft p95 ${ttft.actual}ms (target ${ttft.target}ms) · ` +
      `grounding ${num(report.bench.citationGrounding) ?? '—'} · recall@5 ${num(report.bench.recallAt5) ?? '—'}`
  );
}

console.log(`\nwrote ${outPath}`);
console.log('Serve it at GET /evals/report.json, redeploy, and open /evals on your Vercel URL.');
process.exit(brokenRedLines.length ? 1 : 0);
