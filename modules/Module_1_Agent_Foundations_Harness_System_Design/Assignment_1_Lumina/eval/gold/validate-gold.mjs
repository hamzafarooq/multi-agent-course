#!/usr/bin/env node
/**
 * Check the gold set against the corpus manifest. PROVIDED.
 *
 *   node eval/gold/validate-gold.mjs
 *
 * For every item it asserts: the document exists in the corpus, the `anchor` text really
 * appears in that document, and — for a PDF item — appears on the `page` the item claims.
 * A gold set nobody validated is a gold set that fails a learner for being right.
 *
 * Run it after editing a source: the paginator is fixed, but adding a paragraph on page 2
 * pushes facts onto page 3, and this is what tells you which items moved.
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const manifest = JSON.parse(readFileSync(join(HERE, 'pages.json'), 'utf8'));
const items = readFileSync(join(HERE, 'rag_gold.jsonl'), 'utf8')
  .split('\n')
  .filter((l) => l.trim())
  .map((l, i) => {
    try {
      return JSON.parse(l);
    } catch (err) {
      console.error(`line ${i + 1} is not JSON: ${err.message}`);
      process.exit(2);
    }
  });

const norm = (s) =>
  String(s ?? '')
    .toLowerCase()
    .replace(/[‘’“”]/g, "'")
    .replace(/[^a-z0-9']+/g, ' ')
    .trim();

const problems = [];
const seen = new Set();
const MIN_ITEMS = 30;

for (const item of items) {
  const where = `${item.id}`;
  if (seen.has(item.id)) problems.push(`${where}: duplicate id`);
  seen.add(item.id);

  for (const field of ['question', 'doc', 'anchor']) {
    if (!String(item[field] ?? '').trim()) problems.push(`${where}: missing ${field}`);
  }

  const doc = manifest.documents[item.doc];
  if (!doc) {
    problems.push(`${where}: doc "${item.doc}" is not in the corpus manifest`);
    continue;
  }

  const anchor = norm(item.anchor);
  if (doc.kind === 'pdf') {
    if (!item.page) {
      problems.push(`${where}: a PDF item needs a page`);
      continue;
    }
    const page = doc.pages.find((p) => p.page === item.page);
    if (!page) {
      problems.push(`${where}: ${item.doc} has no page ${item.page} (it has ${doc.pages.length})`);
      continue;
    }
    if (!norm(page.text).includes(anchor)) {
      const actual = doc.pages.find((p) => norm(p.text).includes(anchor));
      problems.push(
        `${where}: anchor is not on page ${item.page}` +
          (actual ? ` — it is on page ${actual.page}` : ' — it is nowhere in this document')
      );
    }
  } else {
    if (item.page) problems.push(`${where}: a Markdown item should use anchor only, not page`);
    if (!norm(doc.text).includes(anchor)) problems.push(`${where}: anchor is not in ${item.doc}`);
  }
}

if (items.length < MIN_ITEMS) problems.push(`only ${items.length} items — rule E1 needs at least ${MIN_ITEMS}`);

const byDoc = items.reduce((acc, i) => ({ ...acc, [i.doc]: (acc[i.doc] ?? 0) + 1 }), {});
console.log(`gold set: ${items.length} items over ${Object.keys(byDoc).length} documents`);
for (const [doc, n] of Object.entries(byDoc)) console.log(`  ${String(n).padStart(3)}  ${doc}`);

if (problems.length) {
  console.error(`\n✗ ${problems.length} problem(s):`);
  for (const p of problems) console.error(`  · ${p}`);
  process.exit(2);
}
console.log('\n✓ every anchor resolves to its declared document and page');
