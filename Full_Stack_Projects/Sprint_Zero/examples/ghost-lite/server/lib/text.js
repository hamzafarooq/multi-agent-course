const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const HEX_COLOR_RE = /^#[0-9a-fA-F]{6}$/;

function nowIso() {
  return new Date().toISOString();
}

function normalizeEmail(value) {
  return typeof value === "string" ? value.trim().toLowerCase() : "";
}

function isEmail(value) {
  return EMAIL_RE.test(value);
}

function isHexColor(value) {
  return typeof value === "string" && HEX_COLOR_RE.test(value);
}

function slugify(text) {
  return String(text || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function uniqueSlug(base, exists) {
  const root = base || "untitled";
  let slug = root;
  let n = 2;
  while (exists(slug)) {
    slug = `${root}-${n}`;
    n += 1;
  }
  return slug;
}

function stripMarkdown(markdown) {
  return String(markdown || "")
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/`([^`]*)`/g, "$1")
    .replace(/!\[[^\]]*\]\([^)]*\)/g, " ")
    .replace(/\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/<[^>]+>/g, " ")
    .replace(/^\s{0,3}(#{1,6}|>|[-*+]|\d+\.)\s+/gm, "")
    .replace(/^\s*([-*_]\s*){3,}$/gm, " ")
    .replace(/[*_~]+/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

function deriveExcerpt(bodyMarkdown, fallback) {
  const text = stripMarkdown(bodyMarkdown);
  if (!text) return fallback;
  const sentences = text.match(/[^.!?]+[.!?]+(?=\s|$)|[^.!?]+$/g) || [text];
  let excerpt = sentences.slice(0, 2).join(" ").replace(/\s+/g, " ").trim();
  if (excerpt.length > 300) excerpt = excerpt.slice(0, 300).trim();
  return excerpt || fallback;
}

function readingTimeMinutes(bodyMarkdown) {
  const words = String(bodyMarkdown || "").trim().split(/\s+/).filter(Boolean).length;
  return Math.max(1, Math.round(words / 250));
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

module.exports = {
  nowIso,
  normalizeEmail,
  isEmail,
  isHexColor,
  slugify,
  uniqueSlug,
  deriveExcerpt,
  readingTimeMinutes,
  escapeHtml,
};
