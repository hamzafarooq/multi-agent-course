const { db } = require("./db");
const { extractTerms, buildPassage } = require("./search");

const answerMode = Boolean(process.env.ANTHROPIC_API_KEY);

const MODEL = "claude-opus-5";
const TIMEOUT_MS = 12_000;
const UUID_RE = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi;
const MAX_PASSAGES = 5;

const SYSTEM_PROMPT = [
  "You answer a reader's question about a writer's blog using only the passages supplied.",
  "Each passage is labelled with its post_id and title. Do not use outside knowledge.",
  "If the passages do not cover the question, say so plainly instead of guessing.",
  "Write a short answer of one to three paragraphs in plain prose, no markdown headings.",
  "End your reply with a final line of exactly this form, listing every post_id you drew on:",
  "SOURCES: <post_id>, <post_id>",
  "If you used no passage, write: SOURCES: none",
].join(" ");

let client = null;

function getClient() {
  if (!client) {
    const Anthropic = require("@anthropic-ai/sdk");
    client = new Anthropic({ timeout: TIMEOUT_MS, maxRetries: 0 });
  }
  return client;
}

function plainText(snippetHtml) {
  return String(snippetHtml)
    .replace(/<\/?mark>/g, "")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&amp;/g, "&");
}

const bodyById = db.prepare("SELECT body_markdown FROM posts WHERE id = ?");

function passageFor(result, terms) {
  const row = bodyById.get(result.post_id);
  const passage = row ? buildPassage(row.body_markdown, terms) : "";
  return passage || plainText(result.snippet);
}

function buildUserMessage(question, results) {
  const terms = extractTerms(question);
  const passages = results
    .slice(0, MAX_PASSAGES)
    .map(
      (r, i) =>
        `Passage ${i + 1}\npost_id: ${r.post_id}\ntitle: ${r.title}\ntext:\n${passageFor(r, terms)}`
    )
    .join("\n\n---\n\n");
  return `Question: ${question}\n\nPassages from the blog's published posts:\n\n${passages}`;
}

function parseReply(text, results) {
  const lines = text.trim().split("\n");
  let citedIds = [];
  let answerLines = lines;
  const lastIdx = lines.map((l) => l.trim()).findLastIndex((l) => /^SOURCES:/i.test(l));
  if (lastIdx !== -1) {
    citedIds = lines[lastIdx].match(UUID_RE) || [];
    answerLines = lines.slice(0, lastIdx);
  }
  const answer = answerLines.join("\n").trim();
  const known = new Map(results.map((r) => [r.post_id.toLowerCase(), r]));
  const seen = new Set();
  const citations = [];
  for (const id of citedIds) {
    const hit = known.get(id.toLowerCase());
    if (hit && !seen.has(hit.post_id)) {
      seen.add(hit.post_id);
      citations.push({ post_id: hit.post_id, title: hit.title, slug: hit.slug });
    }
  }
  return { answer, citations };
}

async function writeAnswer(question, results) {
  if (!answerMode || results.length === 0) return { ok: false };
  try {
    const response = await getClient().messages.create({
      model: MODEL,
      max_tokens: 1500,
      system: SYSTEM_PROMPT,
      messages: [{ role: "user", content: buildUserMessage(question, results) }],
    });
    if (response.stop_reason === "refusal") {
      console.warn("Ask me: the model refused to answer.");
      return { ok: false };
    }
    let text = "";
    for (const block of response.content) {
      if (block.type === "text") text += block.text;
    }
    const parsed = parseReply(text, results);
    if (!parsed.answer) return { ok: false };
    return { ok: true, ...parsed };
  } catch (err) {
    console.warn("Ask me: answer could not be written:", err.message);
    return { ok: false };
  }
}

module.exports = { answerMode, writeAnswer };
