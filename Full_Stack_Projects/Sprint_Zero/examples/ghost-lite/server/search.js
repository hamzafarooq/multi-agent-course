const { db, fts5 } = require("./db");
const { escapeHtml } = require("./lib/text");

const OPEN = "";
const CLOSE = "";
const LIMIT = 5;

const STOP_WORDS = new Set(
  (
    "a an the and or but is are was were be been being do does did what when where which " +
    "who whom why how in on at to of for from by with about as into it its this that these " +
    "those i you we they he she my our your their me us them can could should would will " +
    "shall may might not no yes if then than so there here have has had some any all much " +
    "many more most very just also up down out over under again own same s t"
  ).split(" ")
);

function extractTerms(question) {
  const words = String(question).toLowerCase().match(/[\p{L}\p{N}]+/gu) || [];
  return [...new Set(words.filter((w) => !STOP_WORDS.has(w)))];
}

function markSnippet(raw) {
  return escapeHtml(raw).split(OPEN).join("<mark>").split(CLOSE).join("</mark>");
}

const ftsQuery = fts5
  ? db.prepare(`
      SELECT p.id AS post_id, p.title, p.slug, p.excerpt,
             snippet(posts_fts, -1, '${OPEN}', '${CLOSE}', '...', 40) AS raw_snippet
      FROM posts_fts
      JOIN posts p ON p.id = posts_fts.post_id
      WHERE posts_fts MATCH ? AND p.site_id = ? AND p.status = 'published'
      ORDER BY bm25(posts_fts, 0, 5.0, 1.0)
      LIMIT ${LIMIT}
    `)
  : null;

function ftsSearch(siteId, terms) {
  const match = terms.map((t) => `"${t.replace(/"/g, '""')}"`).join(" OR ");
  return ftsQuery.all(match, siteId).map((row) => ({
    post_id: row.post_id,
    title: row.title,
    slug: row.slug,
    excerpt: row.excerpt,
    snippet: markSnippet(row.raw_snippet),
  }));
}

const likeCandidates = db.prepare(
  "SELECT id, title, slug, excerpt, body_markdown FROM posts WHERE site_id = ? AND status = 'published'"
);

function likeWindow(text, terms) {
  const lower = text.toLowerCase();
  let first = -1;
  for (const term of terms) {
    const idx = lower.indexOf(term);
    if (idx !== -1 && (first === -1 || idx < first)) first = idx;
  }
  if (first === -1) return null;
  const start = Math.max(0, first - 80);
  const end = Math.min(text.length, first + 120);
  let window = text.slice(start, end);
  const pattern = new RegExp(`(${terms.join("|")})`, "gi");
  window = window.replace(pattern, `${OPEN}$1${CLOSE}`);
  return (start > 0 ? "..." : "") + markSnippet(window) + (end < text.length ? "..." : "");
}

function likeSearch(siteId, terms) {
  const scored = [];
  for (const row of likeCandidates.all(siteId)) {
    const haystack = `${row.title}\n${row.body_markdown}`.toLowerCase();
    let score = 0;
    for (const term of terms) {
      let idx = haystack.indexOf(term);
      while (idx !== -1) {
        score += 1;
        idx = haystack.indexOf(term, idx + term.length);
      }
    }
    if (score > 0) scored.push({ row, score });
  }
  scored.sort((a, b) => b.score - a.score);
  return scored.slice(0, LIMIT).map(({ row }) => ({
    post_id: row.id,
    title: row.title,
    slug: row.slug,
    excerpt: row.excerpt,
    snippet: likeWindow(row.body_markdown, terms) || likeWindow(row.title, terms) || "",
  }));
}

const PASSAGE_MIN = 1200;
const PASSAGE_MAX = 1800;

function cleanParagraph(text) {
  return text
    .replace(/!\[[^\]]*\]\([^)]*\)/g, "")
    .replace(/\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/^\s{0,3}#{1,6}\s+/gm, "")
    .replace(/^\s{0,3}>\s?/gm, "")
    .replace(/^\s*[-*+]\s+/gm, "- ")
    .replace(/^\s*([-*_]\s*){3,}$/gm, "")
    .replace(/```/g, "")
    .replace(/\*\*|__|(?<!\w)[*_](?=\w)|(?<=\w)[*_](?!\w)/g, "")
    .replace(/[ \t]+/g, " ")
    .replace(/\n{2,}/g, "\n")
    .trim();
}

function splitParagraphs(markdown) {
  const chunks = String(markdown || "").split(/\n\s*\n/);
  const paragraphs = [];
  let pendingHeading = "";
  for (const chunk of chunks) {
    const cleaned = cleanParagraph(chunk);
    if (!cleaned) continue;
    if (/^\s{0,3}#{1,6}\s/.test(chunk)) {
      pendingHeading = pendingHeading ? `${pendingHeading}\n${cleaned}` : cleaned;
      continue;
    }
    paragraphs.push(pendingHeading ? `${pendingHeading}\n${cleaned}` : cleaned);
    pendingHeading = "";
  }
  if (pendingHeading) paragraphs.push(pendingHeading);
  return paragraphs;
}

function clip(text, max) {
  if (text.length <= max) return text;
  const cut = text.lastIndexOf(" ", max);
  return text.slice(0, cut > max * 0.6 ? cut : max).trim() + "...";
}

function buildPassage(bodyMarkdown, terms) {
  const paragraphs = splitParagraphs(bodyMarkdown);
  if (paragraphs.length === 0) return "";
  const scored = paragraphs.map((text, index) => {
    const lower = text.toLowerCase();
    const score = terms.reduce((n, t) => n + (lower.includes(t) ? 1 : 0), 0);
    return { index, text, score };
  });
  const matched = scored.filter((p) => p.score > 0).sort((a, b) => b.score - a.score || a.index - b.index);
  if (matched.length === 0) return clip(paragraphs.join("\n\n"), 1500);

  const chosen = new Set();
  let total = 0;
  for (const p of matched) {
    if (total >= PASSAGE_MIN) break;
    chosen.add(p.index);
    total += p.text.length + 2;
  }
  let cursor = Math.min(...chosen) + 1;
  while (total < PASSAGE_MIN && cursor < paragraphs.length) {
    if (!chosen.has(cursor)) {
      chosen.add(cursor);
      total += paragraphs[cursor].length + 2;
    }
    cursor += 1;
  }
  const ordered = [...chosen].sort((a, b) => a - b).map((i) => paragraphs[i]);
  return clip(ordered.join("\n\n"), PASSAGE_MAX);
}

function searchPosts(siteId, question) {
  const terms = extractTerms(question);
  if (terms.length === 0) return [];
  return fts5 ? ftsSearch(siteId, terms) : likeSearch(siteId, terms);
}

module.exports = { searchPosts, extractTerms, buildPassage };
