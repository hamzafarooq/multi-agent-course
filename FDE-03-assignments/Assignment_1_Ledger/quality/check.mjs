#!/usr/bin/env node
// Quality checker for the 2026-03 cohort.
// Zero dependencies. Node 18+.
//
//   node quality/check.mjs projects/argus
//
// rules.json holds the case law (metadata, precedent, params).
// This file holds the executables. A rule id with no CHECKS entry is reported as
// unimplemented rather than silently passing.

import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync } from 'node:fs';
import { join, resolve, dirname, basename } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));

// ---------------------------------------------------------------- helpers

const readJson = (p) => JSON.parse(readFileSync(p, 'utf8'));
const isNum = (v) => typeof v === 'number' && Number.isFinite(v);
const pass = (detail = '') => ({ status: 'pass', detail });
const fail = (detail) => ({ status: 'fail', detail });
const skip = (detail) => ({ status: 'skip', detail });
const manual = (detail) => ({ status: 'manual', detail });

// Every run-dependent check folds over all runs and fails on the first bad one.
const overRuns = (ctx, fn) => {
  if (!ctx.runs.length) return skip('no run logs found');
  const bad = [];
  for (const run of ctx.runs) {
    const r = fn(run, ctx);
    if (r) bad.push(`${run._id}: ${r}`);
  }
  return bad.length ? fail(bad.join('; ')) : pass(`${ctx.runs.length} run(s)`);
};

const toolNames = (run) => (run.toolCalls || []).map((t) => t.name);

// ---------------------------------------------------------------- checks

const CHECKS = {
  C1: (ctx) => {
    const { exp } = ctx;
    const problems = [];
    for (const [k, v] of Object.entries(exp.budget || {})) {
      if (!isNum(v) || v <= 0) problems.push(`budget.${k} must be a positive number, got ${JSON.stringify(v)}`);
    }
    for (const [k, v] of Object.entries(exp.eval || {})) {
      if (!k.startsWith('min') && !k.startsWith('max')) continue;
      if (!isNum(v)) { problems.push(`eval.${k} must be a number, got ${JSON.stringify(v)}`); continue; }
      if (v < 0 || v > 1) problems.push(`eval.${k}=${v} is outside 0..1 and can never be satisfied`);
    }
    const gold = exp.eval?.goldSetPath;
    if (gold && !existsSync(join(ctx.root, gold))) problems.push(`eval.goldSetPath missing: ${gold}`);
    const t = exp.trajectory || {};
    for (const a of t.mustCallTools || []) {
      if ((t.mustNotCallTools || []).includes(a)) problems.push(`tool "${a}" is both required and forbidden`);
    }
    return problems.length ? fail(problems.join('; ')) : pass('contract coherent');
  },

  A1: (ctx) => overRuns(ctx, (run) => {
    const bad = (run.toolCalls || []).filter((t) => t.ok === false && !String(t.error || '').trim());
    return bad.length ? `${bad.length} failed call(s) with no error string` : null;
  }),

  A2: (ctx) => overRuns(ctx, (run) => {
    if (ctx.exp.trajectory?.mustTerminate === false) return null;
    return run.terminated === 'done' ? null : `terminated=${JSON.stringify(run.terminated)}`;
  }),

  A3: (ctx, rule) => {
    const cap = ctx.exp.trajectory?.maxConsecutiveSameTool ?? rule.params?.maxConsecutiveSameTool ?? 3;
    return overRuns(ctx, (run) => {
      let streak = 0, prev = null, worst = 0, who = null;
      for (const n of toolNames(run)) {
        streak = n === prev ? streak + 1 : 1;
        prev = n;
        if (streak > worst) { worst = streak; who = n; }
      }
      return worst > cap ? `"${who}" called ${worst}x consecutively (cap ${cap})` : null;
    });
  },

  R1: (ctx) => {
    const required = ctx.exp.trajectory?.mustCallTools || [];
    if (!required.length) return skip('none declared');
    return overRuns(ctx, (run) => {
      const called = new Set(toolNames(run));
      const missing = required.filter((t) => !called.has(t));
      return missing.length ? `never called ${missing.join(', ')}` : null;
    });
  },

  R2: (ctx) => {
    const forbidden = ctx.exp.trajectory?.mustNotCallTools || [];
    if (!forbidden.length) return skip('none declared');
    return overRuns(ctx, (run) => {
      const called = new Set(toolNames(run));
      const hit = forbidden.filter((t) => called.has(t));
      return hit.length ? `called forbidden ${hit.join(', ')}` : null;
    });
  },

  E1: (ctx, rule) => {
    const gold = ctx.exp.eval?.goldSetPath;
    if (!gold) return skip('no goldSetPath declared');
    const p = join(ctx.root, gold);
    if (!existsSync(p)) return fail(`missing: ${gold}`);
    const n = readFileSync(p, 'utf8').split('\n').filter((l) => l.trim()).length;
    const min = rule.params?.minGoldItems ?? 30;
    return n < min ? fail(`${n} items, need ${min}`) : pass(`${n} items`);
  },

  E2: (ctx) => {
    const decl = ctx.exp.eval || {};
    const thresholds = Object.entries(decl).filter(([k]) => k.startsWith('min') || k.startsWith('max'));
    if (!thresholds.length) return skip('no thresholds declared');
    if (!ctx.evalReport) return skip('no eval report — run the eval first');
    const problems = [];
    for (const [k, want] of thresholds) {
      const metric = k.replace(/^(min|max)/, '');
      const key = metric.charAt(0).toLowerCase() + metric.slice(1);
      const got = ctx.evalReport[key];
      if (!isNum(got)) { problems.push(`${key} absent from eval report`); continue; }
      if (k.startsWith('min') && got < want) problems.push(`${key}=${got} < ${want}`);
      if (k.startsWith('max') && got > want) problems.push(`${key}=${got} > ${want}`);
    }
    return problems.length ? fail(problems.join('; ')) : pass(`${thresholds.length} threshold(s) met`);
  },

  E3: () => manual('confirm no error-severity rule derives its verdict from a model'),

  B1: (ctx) => {
    const cap = ctx.exp.budget?.maxTokensPerRun;
    if (!isNum(cap)) return skip('not declared');
    return overRuns(ctx, (r) => (isNum(r.tokens) && r.tokens > cap ? `${r.tokens} tokens > ${cap}` : null));
  },

  B2: (ctx) => {
    const cap = ctx.exp.budget?.maxWallClockSec;
    if (!isNum(cap)) return skip('not declared');
    return overRuns(ctx, (r) => (isNum(r.wallClockSec) && r.wallClockSec > cap ? `${r.wallClockSec}s > ${cap}s` : null));
  },

  B3: (ctx) => {
    const cap = ctx.exp.budget?.maxCostUsd;
    if (!isNum(cap)) return skip('not declared');
    return overRuns(ctx, (r) => (isNum(r.costUsd) && r.costUsd > cap ? `$${r.costUsd} > $${cap}` : null));
  },

  P1: () => manual('name the successful and failing trajectories you read end to end'),

  P2: (ctx) => {
    const todo = ctx.rules
      .filter((r) => (r.precedent || []).some((p) => String(p).trim().startsWith('TODO')))
      .map((r) => r.id);
    return todo.length ? fail(`${todo.length} rule(s) still lack a real precedent: ${todo.join(', ')}`) : pass('all rules cite a precedent');
  },
};

// ---------------------------------------------------------------- main

const projectArg = process.argv[2];
if (!projectArg) {
  console.error('usage: node quality/check.mjs <project-dir>');
  process.exit(2);
}
const root = resolve(projectArg);
const name = basename(root);

const expPath = join(root, 'expectations.json');
if (!existsSync(expPath)) {
  console.log(`quality: ${name} has no expectations.json — skipped`);
  process.exit(0);
}
const exp = readJson(expPath);
if (!exp.quality || Object.values(exp.quality).every((v) => !v)) {
  console.log(`quality: ${name} has not opted in — skipped`);
  process.exit(0);
}

const runsDir = join(root, 'runs');
const runs = existsSync(runsDir)
  ? readdirSync(runsDir)
      .filter((f) => f.endsWith('.json'))
      .map((f) => ({ ...readJson(join(runsDir, f)), _id: f.replace(/\.json$/, '') }))
  : [];

const evalPath = join(root, 'reports', 'eval.json');
const evalReport = existsSync(evalPath) ? readJson(evalPath) : null;

const { rules } = readJson(join(HERE, 'rules.json'));
const ctx = { root, exp, runs, evalReport, rules };

const GLYPH = { pass: '✓', fail: '✗', skip: '–', manual: '☐', unimplemented: '?' };
const results = [];
let errors = 0, warnings = 0;

for (const rule of rules) {
  const fn = CHECKS[rule.id];
  let r;
  if (!fn) r = { status: 'unimplemented', detail: 'no executable for this rule id' };
  else {
    try { r = fn(ctx, rule); }
    catch (e) { r = fail(`checker threw: ${e.message}`); }
  }

  if (r.status === 'fail') {
    if (rule.severity === 'error') errors++;
    else if (rule.severity === 'warn') warnings++;
  }
  if (r.status === 'unimplemented') warnings++;

  results.push({ id: rule.id, title: rule.title, severity: rule.severity, ...r });
  const line = `${rule.id} ${GLYPH[r.status]}  ${rule.title}`;
  console.log(r.detail ? `${line}\n      ${r.detail}` : line);
}

mkdirSync(join(root, 'reports'), { recursive: true });
writeFileSync(
  join(root, 'reports', 'quality.json'),
  JSON.stringify({ project: name, checkedAt: new Date().toISOString(), runs: runs.length, errors, warnings, results }, null, 2)
);

const exitCode = errors ? 2 : warnings ? 1 : 0;
console.log(`\n${name}: ${errors} error(s), ${warnings} warning(s) — exit ${exitCode}`);
console.log(`report: ${join(root, 'reports', 'quality.json')}`);
process.exit(exitCode);
