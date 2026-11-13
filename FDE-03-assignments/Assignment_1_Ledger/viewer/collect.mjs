#!/usr/bin/env node
// Build the deployable site: viewer/dist/. Vercel runs this (vercel.json buildCommand); run it
// yourself with `node viewer/collect.mjs` and open viewer/dist with any static server.
// Zero dependencies. Node 18+.
//
// What it publishes, from YOUR run (nothing here is hand-written):
//   /data/outputs/**        everything in outputs/ (the pack, the register, rules, analytics, history)
//   /data/harness/**        your harness: CLAUDE.md, claude/settings.json, the six agents, the three skills (.claude/ is published as claude/),
//                           scripts/checks/check_trace.py (the grader re-runs the checks with it)
//   /data/eval/skill-runs/  the saved fresh-session runs of /extract-rules
//   /data/runs/             the exported agent run logs (eval/export_runs.py)
//   /data/DESIGN.md, /data/trajectories.md
//   /evals/report.json      reports/report.json from eval/build_report.py
//   /data/manifest.json     every published file with its sha256
//
// Supplier names are pseudonymised. This is a real council's data; the site lists payments flagged
// as risk INDICATORS, and a public page should not put a supplier's name next to "split purchases".
// Every supplier name found in outputs/analytics-full/ and outputs/samples/ is replaced, everywhere,
// by a token: SUP-<10 letters> for the name as published by the council, SUPN-<10 letters> for a
// normalised name. The letters are the first 10 hex digits of sha256(name), each mapped 0-f -> a-p.
// The grader recomputes the tokens from the council's workbooks to check every sampled payment.
// Do not bypass this: publishing supplier names is a red line.

import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync, statSync, rmSync, copyFileSync } from 'node:fs';
import { join, dirname, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');
const DIST = join(HERE, 'dist');
const posix = (p) => p.split(sep).join('/');

// ---------------------------------------------------------------- helpers
const walk = (dir) => {
  if (!existsSync(dir)) return [];
  return readdirSync(dir).flatMap((n) => {
    const p = join(dir, n);
    return statSync(p).isDirectory() ? walk(p) : [p];
  });
};

function parseCsv(text) {
  const rows = [];
  let row = [], cell = '', q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) {
      if (c === '"' && text[i + 1] === '"') { cell += '"'; i++; }
      else if (c === '"') q = false;
      else cell += c;
    } else if (c === '"') q = true;
    else if (c === ',') { row.push(cell); cell = ''; }
    else if (c === '\n' || c === '\r') {
      if (c === '\r' && text[i + 1] === '\n') i++;
      row.push(cell); rows.push(row); row = []; cell = '';
    } else cell += c;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  return rows.filter((r) => r.length > 1 || r[0]);
}

const token = (name, prefix) =>
  prefix + [...createHash('sha256').update(name.trim(), 'utf8').digest('hex').slice(0, 10)]
    .map((h) => String.fromCharCode(97 + parseInt(h, 16))).join('');

const RAW_COLS = new Set(['Supplier name', 'supplier_name', 'supplier', 'candidate_notice_supplier']);
const NORM_COLS = new Set(['supplier_norm']);
const SKIP_NAMES = /^(redacted|n\/a|none|unknown|)$/i;

// ---------------------------------------------------------------- the supplier map
function supplierMap() {
  const map = new Map(); // name -> token
  const files = [...walk(join(ROOT, 'outputs/analytics-full')), ...walk(join(ROOT, 'outputs/samples'))].filter((f) => f.endsWith('.csv'));
  for (const f of files) {
    const rows = parseCsv(readFileSync(f, 'utf8'));
    if (!rows.length) continue;
    const head = rows[0];
    head.forEach((col, i) => {
      const isRaw = RAW_COLS.has(col), isNorm = NORM_COLS.has(col);
      if (!isRaw && !isNorm) return;
      for (const r of rows.slice(1)) {
        const v = (r[i] || '').trim();
        if (v.length < 3 || SKIP_NAMES.test(v) || map.has(v)) continue;
        if (/^SUPN?-[a-p]{10}$/.test(v)) continue;
        map.set(v, token(v, isRaw ? 'SUP-' : 'SUPN-'));
      }
    });
  }
  // a name seen as both raw and normalised keeps its raw token: the grader restores SUP- tokens only
  for (const f of files) {
    const rows = parseCsv(readFileSync(f, 'utf8'));
    if (!rows.length) continue;
    rows[0].forEach((col, i) => {
      if (!RAW_COLS.has(col)) return;
      for (const r of rows.slice(1)) { const v = (r[i] || '').trim(); if (map.has(v)) map.set(v, token(v, 'SUP-')); }
    });
  }
  return map;
}

function replacer(map) {
  if (!map.size) return (s) => s;
  const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const names = [...map.keys()].sort((a, b) => b.length - a.length);
  const chunks = []; // one huge alternation is slow to compile; chunk it, longest names first
  for (let i = 0; i < names.length; i += 400) chunks.push(new RegExp(`(?<![A-Za-z0-9])(?:${names.slice(i, i + 400).map(esc).join('|')})(?![A-Za-z0-9])`, 'g'));
  return (text) => chunks.reduce((t, re) => t.replace(re, (m) => map.get(m) ?? m), text);
}

// ---------------------------------------------------------------- publish
function main() {
  rmSync(DIST, { recursive: true, force: true });
  mkdirSync(DIST, { recursive: true });
  for (const f of ['index.html', 'evals.html', 'app.js', 'evals.js', 'styles.css']) copyFileSync(join(HERE, f), join(DIST, f));
  mkdirSync(join(DIST, 'vendor'), { recursive: true });
  for (const f of readdirSync(join(HERE, 'vendor'))) copyFileSync(join(HERE, 'vendor', f), join(DIST, 'vendor', f));

  const map = supplierMap();
  const scrub = replacer(map);
  const published = [];
  const put = (src, dest) => {
    if (!existsSync(src)) return;
    const out = join(DIST, dest);
    mkdirSync(dirname(out), { recursive: true });
    const text = scrub(readFileSync(src, 'utf8'));
    writeFileSync(out, text);
    published.push({ path: posix(dest), bytes: Buffer.byteLength(text), sha256: createHash('sha256').update(text).digest('hex') });
  };

  for (const f of walk(join(ROOT, 'outputs'))) {
    const rel = posix(relative(join(ROOT, 'outputs'), f));
    if (rel === '.gitkeep' || !/\.(json|md|csv)$/.test(rel)) continue;
    put(f, `data/outputs/${rel}`);
  }
  const harness = ['CLAUDE.md', 'DESIGN.md', 'trajectories.md', 'live-test.md', 'design-interview.md', '.claude/settings.json', 'scripts/checks/check_trace.py',
    ...['spend-analyst', 'findings-analyst', 'risk-assessor', 'planner', 'challenger', 'qa-reviewer'].map((a) => `.claude/agents/${a}.md`),
    ...['extract-rules', 'risk-assessment', 'audit-program'].map((s) => `.claude/skills/${s}/SKILL.md`)];
  for (const f of harness) put(join(ROOT, f), ['DESIGN.md', 'trajectories.md', 'live-test.md', 'design-interview.md'].includes(f) ? `data/${f}` : `data/harness/${f.replace(/^\.claude\//, 'claude/')}`); // static hosts may not serve dot-folders
  for (const d of existsSync(join(ROOT, 'eval/skill/runs')) ? readdirSync(join(ROOT, 'eval/skill/runs')) : []) {
    put(join(ROOT, 'eval/skill/runs', d, 'rules.json'), `data/eval/skill-runs/${d}.json`);
  }
  for (const f of walk(join(ROOT, 'runs')).filter((f) => f.endsWith('.json'))) put(f, `data/runs/${posix(relative(join(ROOT, 'runs'), f))}`);
  put(join(ROOT, 'reports/report.json'), 'evals/report.json');
  put(join(ROOT, 'reports/PRODUCT_EVAL.md'), 'evals/PRODUCT_EVAL.md');

  // leak check: no supplier name of eight or more characters may survive anywhere we publish
  const leaks = [];
  const long = [...map.keys()].filter((n) => n.length >= 8);
  for (const p of published) {
    const text = readFileSync(join(DIST, p.path), 'utf8');
    for (const n of long) if (text.includes(n)) { leaks.push(`${p.path}: ${n.slice(0, 3)}…`); break; }
  }
  const manifest = {
    generatedAt: new Date().toISOString(),
    files: published,
    pseudonymisation: {
      suppliers: map.size,
      method: 'sha256(trimmed name) -> first 10 hex digits -> each mapped 0-f to a-p',
      prefixes: { 'SUP-': 'supplier name as published by the council', 'SUPN-': 'normalised supplier name' },
      leaks: leaks.length,
    },
  };
  writeFileSync(join(DIST, 'data/manifest.json'), JSON.stringify(manifest, null, 2));

  console.log(`viewer/dist: ${published.length} files published, ${map.size} supplier names pseudonymised`);
  console.log(existsSync(join(ROOT, 'reports/report.json')) ? '/evals/report.json: from reports/report.json'
    : '/evals/report.json: MISSING. Run `python eval/build_report.py` first; /evals will say so.');
  if (leaks.length) {
    console.error(`LEAK: a supplier name survived pseudonymisation in ${leaks.length} file(s): ${leaks.slice(0, 5).join('; ')}`);
    process.exit(1);
  }
}

main();
