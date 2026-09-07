#!/usr/bin/env node
/**
 * Render the authored sources into the corpus a learner uploads. PROVIDED.
 *
 *   node eval/gold/build-corpus.mjs
 *
 * sources/*.md  →  corpus/*.pdf   (two of them, so page locators can be graded)
 *               →  corpus/*.md    (two of them, so heading locators can be graded)
 *               →  pages.json     (which heading landed on which page)
 *
 * The paginator is fixed — 44 lines a page, wrapped at 92 characters — so `p. 3` is `p. 3`
 * on every machine. That is the whole reason the corpus is generated rather than borrowed:
 * a gold item can name a page and still be true next week.
 *
 * Zero dependencies. The PDF is written by hand; it is a text-only 1.4 file with one
 * Helvetica font, which is all a page-locator test needs.
 */
import { mkdirSync, readFileSync, writeFileSync, copyFileSync, readdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const SRC = join(HERE, 'sources');
const OUT = join(HERE, 'corpus');

/** Which sources become PDFs (page locators) and which stay Markdown (heading locators). */
const AS_PDF = ['retrieval-basics.md', 'vector-search-on-mongodb.md'];
const AS_MD = ['agent-loops-and-failure.md', 'streaming-and-latency.md'];

const LINES_PER_PAGE = 44;
const WRAP = 92;
const FONT_SIZE = 11;
const LEADING = 15.2;
const TOP = 748;
const LEFT = 58;

mkdirSync(OUT, { recursive: true });

// ---------------------------------------------------------------- markdown → lines

const wrap = (text, width) => {
  const out = [];
  let line = '';
  for (const word of text.split(/\s+/).filter(Boolean)) {
    if (!line.length) line = word;
    else if (line.length + 1 + word.length <= width) line += ` ${word}`;
    else {
      out.push(line);
      line = word;
    }
  }
  if (line) out.push(line);
  return out.length ? out : [''];
};

/** Flatten Markdown to plain lines, keeping headings and code blocks recognizable. */
function toLines(md) {
  const lines = [];
  let inCode = false;

  for (const raw of md.split('\n')) {
    if (/^```/.test(raw)) {
      inCode = !inCode;
      continue;
    }
    if (inCode) {
      lines.push({ text: raw, kind: 'code' });
      continue;
    }

    const heading = /^(#{1,6})\s+(.*)$/.exec(raw);
    if (heading) {
      lines.push({ text: '', kind: 'blank' });
      lines.push({ text: heading[2].trim(), kind: 'heading', level: heading[1].length });
      lines.push({ text: '', kind: 'blank' });
      continue;
    }
    if (!raw.trim()) {
      lines.push({ text: '', kind: 'blank' });
      continue;
    }
    // Indented (four-space) blocks are preformatted; keep them verbatim.
    if (/^ {4}/.test(raw)) {
      lines.push({ text: raw.trimEnd(), kind: 'code' });
      continue;
    }

    const plain = raw
      .replace(/\*\*(.+?)\*\*/g, '$1')
      .replace(/\*(.+?)\*/g, '$1')
      .replace(/`(.+?)`/g, '$1')
      .replace(/\[(.+?)\]\((.+?)\)/g, '$1')
      .trim();
    const bullet = /^([-*]|\d+\.)\s+(.*)$/.exec(plain);
    if (bullet) {
      const [first, ...rest] = wrap(bullet[2], WRAP - 4);
      lines.push({ text: `  • ${first}`, kind: 'text' });
      for (const r of rest) lines.push({ text: `    ${r}`, kind: 'text' });
      continue;
    }
    if (/^\|/.test(plain)) {
      lines.push({ text: plain, kind: 'code' });
      continue;
    }
    for (const w of wrap(plain, WRAP)) lines.push({ text: w, kind: 'text' });
  }

  // Collapse runs of blanks so pagination is not dominated by whitespace.
  return lines.filter((l, i) => !(l.kind === 'blank' && lines[i - 1]?.kind === 'blank'));
}

function paginate(lines) {
  const pages = [];
  let current = [];
  for (const line of lines) {
    // Never leave a heading stranded as the last line of a page.
    if (line.kind === 'heading' && current.length > LINES_PER_PAGE - 4) {
      pages.push(current);
      current = [];
    }
    if (current.length >= LINES_PER_PAGE) {
      pages.push(current);
      current = [];
    }
    if (!current.length && line.kind === 'blank') continue;
    current.push(line);
  }
  if (current.length) pages.push(current);
  return pages;
}

// ---------------------------------------------------------------- lines → pdf

const esc = (s) => s.replace(/\\/g, '\\\\').replace(/\(/g, '\\(').replace(/\)/g, '\\)');

function pageContent(lines) {
  let y = TOP;
  let out = '';
  for (const line of lines) {
    if (line.kind === 'blank') {
      y -= LEADING * 0.55;
      continue;
    }
    const font = line.kind === 'heading' ? '/F2' : line.kind === 'code' ? '/F3' : '/F1';
    const size = line.kind === 'heading' ? (line.level === 1 ? 17 : 13) : FONT_SIZE;
    if (line.kind === 'heading') y -= 4;
    out += `BT ${font} ${size} Tf ${LEFT} ${y.toFixed(1)} Td (${esc(line.text)}) Tj ET\n`;
    y -= line.kind === 'heading' ? size + 6 : LEADING;
  }
  return out;
}

function buildPdf(pages, title) {
  const objects = [];
  const add = (body) => {
    objects.push(body);
    return objects.length;
  };

  const f1 = add('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>');
  const f2 = add('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>');
  const f3 = add('<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>');

  const contentIds = pages.map((lines, i) => {
    const body = pageContent(lines) + `BT /F1 8 Tf ${LEFT} 42 Td (${esc(title)} — page ${i + 1} of ${pages.length}) Tj ET\n`;
    return add(`<< /Length ${Buffer.byteLength(body, 'latin1')} >>\nstream\n${body}endstream`);
  });

  const pagesId = objects.length + pages.length + 1;
  const pageIds = contentIds.map((cid) =>
    add(
      `<< /Type /Page /Parent ${pagesId} 0 R /MediaBox [0 0 612 792] ` +
        `/Resources << /Font << /F1 ${f1} 0 R /F2 ${f2} 0 R /F3 ${f3} 0 R >> >> /Contents ${cid} 0 R >>`
    )
  );
  add(`<< /Type /Pages /Kids [${pageIds.map((i) => `${i} 0 R`).join(' ')}] /Count ${pages.length} >>`);
  const infoId = add(`<< /Title (${esc(title)}) /Producer (lumina build-corpus) >>`);
  const catalogId = add(`<< /Type /Catalog /Pages ${pagesId} 0 R >>`);

  let pdf = '%PDF-1.4\n';
  const offsets = [];
  objects.forEach((body, i) => {
    offsets[i] = Buffer.byteLength(pdf, 'latin1');
    pdf += `${i + 1} 0 obj\n${body}\nendobj\n`;
  });
  const xref = Buffer.byteLength(pdf, 'latin1');
  pdf += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
  for (const off of offsets) pdf += `${String(off).padStart(10, '0')} 00000 n \n`;
  pdf +=
    `trailer\n<< /Size ${objects.length + 1} /Root ${catalogId} 0 R /Info ${infoId} 0 R >>\n` +
    `startxref\n${xref}\n%%EOF\n`;

  return Buffer.from(pdf, 'latin1');
}

// ---------------------------------------------------------------- main

const manifest = { builtAt: new Date().toISOString(), documents: {} };

for (const name of AS_PDF) {
  const md = readFileSync(join(SRC, name), 'utf8');
  const title = (/^#\s+(.*)$/m.exec(md)?.[1] ?? name).trim();
  const pages = paginate(toLines(md));
  const outName = name.replace(/\.md$/, '.pdf');
  writeFileSync(join(OUT, outName), buildPdf(pages, title));

  manifest.documents[outName] = {
    kind: 'pdf',
    title,
    pages: pages.map((lines, i) => ({
      page: i + 1,
      headings: lines.filter((l) => l.kind === 'heading').map((l) => l.text),
      // Full page text so validate-gold.mjs can check a page number without a PDF parser.
      text: lines.map((l) => l.text).join(' ').replace(/\s+/g, ' ').trim()
    }))
  };
  console.log(`  ✓ ${outName} — ${pages.length} pages`);
}

for (const name of AS_MD) {
  copyFileSync(join(SRC, name), join(OUT, name));
  const md = readFileSync(join(SRC, name), 'utf8');
  manifest.documents[name] = {
    kind: 'markdown',
    title: (/^#\s+(.*)$/m.exec(md)?.[1] ?? name).trim(),
    headings: [...md.matchAll(/^#{2,6}\s+(.*)$/gm)].map((m) => m[1].trim()),
    text: toLines(md).map((l) => l.text).join(' ').replace(/\s+/g, ' ').trim()
  };
  console.log(`  ✓ ${name} — copied (${manifest.documents[name].headings.length} headings)`);
}

writeFileSync(join(HERE, 'pages.json'), JSON.stringify(manifest, null, 2));
console.log(`\ncorpus: ${readdirSync(OUT).length} file(s) in eval/gold/corpus`);
console.log('manifest: eval/gold/pages.json — check it after editing a source, pages move');
