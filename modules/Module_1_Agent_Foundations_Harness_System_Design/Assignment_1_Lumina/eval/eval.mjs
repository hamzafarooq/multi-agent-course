#!/usr/bin/env node
/**
 * The six gates, in order, each one blocking. PROVIDED — do not edit.
 *
 *   node eval/eval.mjs                                  # local, against sla.json's target
 *   node eval/eval.mjs --deploy-url https://gw.fly.dev   # what the grader runs
 *   node eval/eval.mjs --skip-static                    # while you are still mid-build
 *
 *   0 STATIC      lint + typecheck clean; no .env, runs/ or reports/ staged in git
 *   1 CONTRACT    quality/check.mjs → C1: the expectations file is internally coherent
 *   2 RUN         bench --smoke: five queries inside budget, terminated "done"
 *   3 TRAJECTORY  quality/check.mjs over runs/ → A1, A2, A3, R2
 *   4 EVAL        full bench → reports/eval.json → E1, E2 + the SLA percentiles
 *   5 HUMAN       P1: you read one successful and one failing trajectory, every step
 *
 * Gate 5 cannot be automated and is not meant to be. It is the one that catches what
 * every other gate structurally cannot.
 *
 * Exit codes follow the kit: 0 pass, 1 warnings only, 2 at least one error.
 */
import { spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, '..');

const argv = process.argv.slice(2);
const has = (f) => argv.includes(f);
const val = (f, d) => {
  const i = argv.indexOf(f);
  return i > -1 && argv[i + 1] ? argv[i + 1] : d;
};

const deployUrl = val('--deploy-url', null);
const gates = [];
let errors = 0;
let warnings = 0;

const run = (cmd, args, opts = {}) =>
  spawnSync(cmd, args, { cwd: ROOT, encoding: 'utf8', stdio: 'pipe', ...opts });

const record = (gate, name, status, detail, exitCode) => {
  gates.push({ gate, name, status, detail, exitCode });
  const glyph = { pass: '✓', fail: '✗', skip: '–', manual: '☐' }[status];
  console.log(`\ngate ${gate} ${name} ${glyph} ${status.toUpperCase()}`);
  if (detail) console.log(`  ${detail.split('\n').join('\n  ')}`);
  if (status === 'fail') errors++;
};

const tail = (s, n = 12) =>
  String(s ?? '')
    .trim()
    .split('\n')
    .slice(-n)
    .join('\n');

// ---------------------------------------------------------------- gate 0: STATIC

if (has('--skip-static')) {
  record(0, 'STATIC', 'skip', 'skipped by --skip-static');
} else {
  // A missing script is not a failing script: the gates grade the contract, not the stack.
  // If you built outside the Node workspace, run your own linter and type checker and say
  // so in your run notes — but a project without these npm scripts still passes gate 0 on
  // the thing that matters, which is that no secret is staged.
  const scripts = (() => {
    try {
      return JSON.parse(readFileSync(join(ROOT, 'package.json'), 'utf8')).scripts ?? {};
    } catch {
      return {};
    }
  })();
  const lint = scripts.lint ? run('npm', ['run', '--silent', 'lint']) : { status: 0, skipped: true };
  const types = scripts.typecheck
    ? run('npm', ['run', '--silent', 'typecheck'])
    : { status: 0, skipped: true };
  const git = run('git', ['status', '--porcelain']);
  const dirty = (git.stdout ?? '')
    .split('\n')
    .filter((l) => /\s(\.env|runs\/|reports\/)/.test(l) || /^\?\?\s+(\.env$|runs\/|reports\/)/.test(l));

  const problems = [];
  if (lint.status !== 0) problems.push(`lint failed:\n${tail(lint.stdout || lint.stderr)}`);
  if (types.status !== 0) problems.push(`typecheck failed:\n${tail(types.stdout || types.stderr)}`);
  if (dirty.length) problems.push(`git has secrets or artifacts staged:\n${dirty.join('\n')}`);

  const skipped = [lint.skipped && 'lint', types.skipped && 'typecheck'].filter(Boolean);
  record(
    0,
    'STATIC',
    problems.length ? 'fail' : 'pass',
    problems.join('\n') ||
      (skipped.length
        ? `git clean; no npm ${skipped.join('/')} script — run your own and note it`
        : 'lint, typecheck and git clean')
  );
  if (problems.length) finish();
}

// ---------------------------------------------------------------- gate 1: CONTRACT

{
  const check = run('node', ['quality/check.mjs', '.']);
  const out = check.stdout ?? '';
  const c1 = /^C1 ✓/m.test(out);
  record(
    1,
    'CONTRACT',
    c1 ? 'pass' : 'fail',
    c1 ? 'C1: expectations.json is coherent' : `C1 did not pass:\n${tail(out)}`,
    check.status
  );
  if (!c1) finish();
}

// ---------------------------------------------------------------- gate 2: RUN

{
  const args = ['benchmark/bench.mjs', '--smoke'];
  if (deployUrl) args.push('--target', deployUrl);
  const smoke = run('node', args, { stdio: 'inherit' });
  record(
    2,
    'RUN',
    smoke.status === 0 ? 'pass' : 'fail',
    smoke.status === 0 ? 'five queries completed inside budget' : 'the smoke run missed a target — see above',
    smoke.status
  );
  if (smoke.status !== 0) finish();
}

// ---------------------------------------------------------------- gate 3: TRAJECTORY

{
  const runsDir = join(ROOT, 'runs');
  const count = existsSync(runsDir) ? readdirSync(runsDir).filter((f) => f.endsWith('.json')).length : 0;

  if (!count) {
    record(
      3,
      'TRAJECTORY',
      'fail',
      'runs/ is empty. Every answer must write runs/<requestId>.json (PRD 13).\n' +
        'Deployed? `node scripts/export-runs.mjs` pulls them out of Mongo.'
    );
    finish();
  }

  const check = run('node', ['quality/check.mjs', '.']);
  const out = check.stdout ?? '';
  console.log(out.trim());
  const failedErrors = ['A1', 'A2', 'R2'].filter((id) => new RegExp(`^${id} ✗`, 'm').test(out));
  const a3 = /^A3 ✗/m.test(out);
  if (a3) warnings++;

  record(
    3,
    'TRAJECTORY',
    failedErrors.length ? 'fail' : 'pass',
    failedErrors.length
      ? `error-severity rules failed over ${count} run(s): ${failedErrors.join(', ')}`
      : `${count} run log(s), no error-severity trajectory failure${a3 ? ' (A3 warns)' : ''}`,
    check.status
  );
  if (failedErrors.length) finish();
}

// ---------------------------------------------------------------- gate 4: EVAL

{
  const args = ['benchmark/bench.mjs'];
  if (deployUrl) args.push('--target', deployUrl);
  const full = run('node', args, { stdio: 'inherit' });

  const check = run('node', ['quality/check.mjs', '.']);
  const out = check.stdout ?? '';
  const e1 = /^E1 ✓/m.test(out);
  const e2 = /^E2 ✓/m.test(out);
  const detail = [
    full.status === 0 ? 'SLA: every declared target met' : 'SLA: at least one target missed',
    `E1 gold set: ${e1 ? 'pass' : 'FAIL'}`,
    `E2 thresholds: ${e2 ? 'pass' : 'FAIL'}`
  ].join(' · ');

  const ok = full.status === 0 && e1 && e2;
  record(4, 'EVAL', ok ? 'pass' : 'fail', detail, full.status);
  if (!ok) finish();
}

// ---------------------------------------------------------------- gate 5: HUMAN

record(
  5,
  'HUMAN',
  'manual',
  'P1: name the one successful and one failing trajectory you read end to end, every step,\n' +
    'and what each taught you. They go on /evals. If you cannot produce a failing one, kill\n' +
    'the search provider key and run again — you do not understand the failure surface yet.'
);

finish();

// ---------------------------------------------------------------- report

function finish() {
  mkdirSync(join(ROOT, 'reports'), { recursive: true });

  const read = (p) => {
    try {
      return JSON.parse(readFileSync(join(ROOT, p), 'utf8'));
    } catch {
      return null;
    }
  };

  const out = {
    ranAt: new Date().toISOString(),
    target: deployUrl ?? JSON.parse(readFileSync(join(ROOT, 'benchmark', 'sla.json'), 'utf8')).target,
    gates,
    errors,
    warnings,
    bench: read('reports/bench.json'),
    quality: read('reports/quality.json'),
    rubric: JSON.parse(readFileSync(join(HERE, 'rubric.json'), 'utf8'))
  };
  writeFileSync(join(ROOT, 'reports', 'gates.json'), JSON.stringify(out, null, 2));

  const code = errors ? 2 : warnings ? 1 : 0;
  console.log(`\n${'─'.repeat(74)}`);
  console.log(`gates: ${errors} error(s), ${warnings} warning(s) — exit ${code}`);
  console.log('reports/gates.json written');
  if (code === 0) {
    console.log(
      '\nGate 5 is still yours. Then `/fde-lumina-eval --deploy-url …` turns these results\n' +
        'into the report.json your /evals page renders.'
    );
  }
  process.exit(code);
}
