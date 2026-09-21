#!/usr/bin/env node
// Lint an FDE assignment folder against the house pattern.
//   node .claude/skills/fde-assignment/scripts/lint-assignment.mjs <assignment-dir>
// Exit 0 clean, 1 warnings only, 2 errors. Zero dependencies.

import { readFileSync, existsSync, statSync } from 'node:fs';
import { join, dirname, resolve } from 'node:path';

const root = resolve(process.argv[2] || '.');
const errors = [];
const warns = [];
const err = (m) => errors.push(m);
const warn = (m) => warns.push(m);
const read = (p) => readFileSync(join(root, p), 'utf8');
const has = (p) => existsSync(join(root, p));
const words = (s) => s.split(/\s+/).filter(Boolean).length;

// ---------------------------------------------------------------- presence
const REQUIRED = ['README.md', 'PRD.md', 'TECHNICAL.md', 'AGENTS.md', 'SPEC.md', 'DESIGN.template.md',
  'benchmark/sla.json', 'expectations.json', 'eval/rubric.json', 'quality/rules.json', 'quality/check.mjs'];
for (const f of REQUIRED) if (!has(f)) err(`missing ${f}`);
const docs = Object.fromEntries(REQUIRED.filter((f) => f.endsWith('.md') && has(f)).map((f) => [f, read(f)]));

// ---------------------------------------------------------------- word budgets (warn)
const BUDGET = { 'README.md': 800, 'PRD.md': 1500, 'AGENTS.md': 1600 };
const ladder = ['README.md', 'PRD.md', 'TECHNICAL.md', 'AGENTS.md', 'SPEC.md'].filter((f) => docs[f]).map((f) => `${f} ${words(docs[f])}`);
for (const [f, max] of Object.entries(BUDGET)) {
  if (docs[f] && words(docs[f]) > max) warn(`${f} is ${words(docs[f])} words, budget ${max}`);
}

// ---------------------------------------------------------------- PRD has no digits
if (docs['PRD.md']) {
  const lines = docs['PRD.md'].split('\n');
  const survivors = [];
  lines.forEach((line, i) => {
    if (i < 4) return;                                   // title + byline: the one place dates live
    let s = line.replace(/`[^`]*`/g, '');                // code spans
    s = s.replace(/\]\([^)]*\)/g, ']');                  // link targets
    s = s.replace(/^\s*\d+\.\s/, '');                    // ordered-list markers
    s = s.replace(/\b(Week|Module|Assignment|cohort)\s+[\d-]+/g, '$1'); // course structure, not thresholds
    if (/\d/.test(s)) survivors.push(`  L${i + 1}: ${line.trim().slice(0, 90)}`);
  });
  if (survivors.length) err(`PRD.md contains digits outside code spans (thresholds belong in JSON):\n${survivors.join('\n')}`);
}

// ---------------------------------------------------------------- SPEC header
if (docs['SPEC.md']) {
  const head = docs['SPEC.md'].slice(0, 3000);
  for (const needle of ['written to be read by a coding agent', 'If you are a human, read', 'No number in here is authoritative']) {
    if (!head.includes(needle)) err(`SPEC.md header is missing the sentence containing "${needle}"`);
  }
}

// ---------------------------------------------------------------- AGENTS / README / TECHNICAL structure
if (docs['AGENTS.md'] && !/DO NOT EDIT/.test(docs['AGENTS.md'])) err('AGENTS.md has no DO NOT EDIT list');
if (docs['AGENTS.md'] && !/runs\/failing/.test(docs['AGENTS.md'])) warn('AGENTS.md does not state the runs/failing/ convention (P1 vs A2 trap)');
if (docs['README.md']) {
  if (!/PRD\.md/.test(docs['README.md']) || !/SPEC\.md/.test(docs['README.md'])) err('README.md reading ladder does not name PRD.md and SPEC.md');
  if (!/501/.test(docs['README.md'])) warn('README.md does not mention the 501 skeleton (step 1 of the reading path)');
  if (!/Vercel/.test(docs['README.md'])) warn('README.md does not mention where the UI deploys (Vercel)');
}
if (docs['TECHNICAL.md']) {
  if (!/\|\s*Piece\s*\|\s*Host\s*\|/.test(docs['TECHNICAL.md'])) err('TECHNICAL.md has no deploy table (| Piece | Host | Fixed? |)');
  if (!/[Tt]roubleshooting/.test(docs['TECHNICAL.md'])) warn('TECHNICAL.md has no Troubleshooting section');
}
if (docs['DESIGN.template.md']) {
  for (const h of ['Components', 'Responsibilities', 'Communication', 'State', 'Trade-offs']) {
    if (!new RegExp(`^##\\s+${h}`, 'm').test(docs['DESIGN.template.md'])) err(`DESIGN.template.md is missing the "## ${h}" heading (the report builder parses by heading)`);
  }
}

// ---------------------------------------------------------------- relative links resolve
for (const [f, text] of Object.entries(docs)) {
  const re = /\]\(([^)#\s]+)(#[^)]*)?\)/g;
  let m;
  while ((m = re.exec(text))) {
    const target = m[1];
    if (/^(https?:|mailto:)/.test(target)) continue;
    const p = resolve(join(root, dirname(f), target));
    if (!existsSync(p)) err(`${f}: link to ${target} does not resolve`);
  }
}

// ---------------------------------------------------------------- JSON gates
const json = (p) => { try { return JSON.parse(read(p)); } catch (e) { err(`${p}: invalid JSON (${e.message})`); return null; } };
const sla = has('benchmark/sla.json') ? json('benchmark/sla.json') : null;
const exp = has('expectations.json') ? json('expectations.json') : null;
const rubric = has('eval/rubric.json') ? json('eval/rubric.json') : null;
const rules = has('quality/rules.json') ? json('quality/rules.json') : null;

if (sla) {
  if (!sla.sla || typeof sla.sla !== 'object') err('sla.json has no "sla" object');
  else for (const [k, v] of Object.entries(sla.sla)) {
    if (typeof v !== 'number' || !Number.isFinite(v)) err(`sla.sla.${k} is not a number`);
    if (!sla._sla_notes?.[k]) warn(`sla.sla.${k} has no note in _sla_notes explaining why that number`);
  }
  if (!sla.cost_model) warn('sla.json has no cost_model');
}
if (exp) {
  for (const [k, v] of Object.entries(exp.budget || {})) if (!(typeof v === 'number' && v > 0)) err(`expectations.budget.${k} must be a positive number (C1)`);
  for (const [k, v] of Object.entries(exp.eval || {})) {
    if (!/^(min|max)/.test(k)) continue;
    if (typeof v !== 'number' || v < 0 || v > 1) err(`expectations.eval.${k}=${v} is outside 0..1 (C1)`);
  }
  if (!exp.eval?.goldSetPath) warn('expectations.eval.goldSetPath not declared (E1)');
  else if (!has(exp.eval.goldSetPath)) warn(`gold set ${exp.eval.goldSetPath} does not exist yet (E1 will fail until staff builds it)`);
  const t = exp.trajectory || {};
  for (const a of t.mustCallTools || []) if ((t.mustNotCallTools || []).includes(a)) err(`tool "${a}" both required and forbidden (C1)`);
}
if (rubric) {
  const auto = rubric.automated || [], manual = rubric.manual || [];
  const sum = [...auto, ...manual].reduce((s, r) => s + (r.points || 0), 0);
  if (sum !== (rubric.total_points || 100)) err(`rubric points sum to ${sum}, total_points is ${rubric.total_points}`);
  const autoPts = auto.reduce((s, r) => s + r.points, 0);
  if (autoPts < 70 || autoPts > 90) warn(`automated rows are ${autoPts} pts; house split is about 80/20`);
  if (manual.length < 2) warn('fewer than two manual rows; the lesson\'s human half and the P1 human gate are expected');
  if (!(rubric.red_lines || []).length) err('rubric has no red_lines');
  if (!(rubric.stretch_bonus || []).some((b) => b.id === 'new_rule_with_precedent')) warn('bonus new_rule_with_precedent missing');
  const known = new Set((rules?.rules || []).map((r) => r.id));
  for (const r of [...auto, ...manual]) {
    if (!r.check) err(`rubric row ${r.id} has no check text`);
    for (const id of r.rules || []) if (rules && !known.has(id)) err(`rubric row ${r.id} cites rule ${id}, which is not in quality/rules.json`);
  }
}

// ---------------------------------------------------------------- report
console.log(`lint ${root}`);
console.log(`reading ladder: ${ladder.join(' -> ')}`);
for (const e of errors) console.log(`ERROR ${e}`);
for (const w of warns) console.log(`warn  ${w}`);
console.log(errors.length ? `${errors.length} error(s), ${warns.length} warning(s)` : warns.length ? `clean, ${warns.length} warning(s)` : 'clean');
process.exit(errors.length ? 2 : warns.length ? 1 : 0);
