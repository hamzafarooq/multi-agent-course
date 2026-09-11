const express = require("express");
const crypto = require("crypto");
const { db } = require("../db");
const { sendError, bodyOf } = require("../lib/http");
const { nowIso, normalizeEmail, isEmail } = require("../lib/text");
const { serializeSite, serializePost, serializeMember } = require("../lib/serialize");
const { searchPosts } = require("../search");
const { answerMode, writeAnswer } = require("../answer");

const router = express.Router();

const findSiteBySlug = db.prepare("SELECT * FROM sites WHERE slug = ?");
const listPublished = db.prepare(
  "SELECT * FROM posts WHERE site_id = ? AND status = 'published' ORDER BY published_at DESC"
);
const findPublishedBySlug = db.prepare(
  "SELECT * FROM posts WHERE site_id = ? AND slug = ? AND status = 'published'"
);
const findMember = db.prepare("SELECT * FROM members WHERE site_id = ? AND email = ?");
const insertMember = db.prepare(
  "INSERT INTO members (id, site_id, email, status, created_at) VALUES (?, ?, ?, 'free', ?)"
);

const ANSWER_ERROR = "An answer could not be written; showing matching passages instead.";

function loadSite(req, res) {
  const site = findSiteBySlug.get(req.params.slug);
  if (!site) sendError(res, 404, "not_found", "Site not found.");
  return site || null;
}

router.get("/:slug", (req, res) => {
  const site = loadSite(req, res);
  if (!site) return;
  res.json(serializeSite(site));
});

router.get("/:slug/posts", (req, res) => {
  const site = loadSite(req, res);
  if (!site) return;
  const posts = listPublished.all(site.id).map((row) => serializePost(row, { summary: true }));
  res.json({ posts });
});

router.get("/:slug/posts/:postSlug", (req, res) => {
  const site = loadSite(req, res);
  if (!site) return;
  const post = findPublishedBySlug.get(site.id, req.params.postSlug);
  if (!post) return sendError(res, 404, "not_found", "Post not found.");
  res.json(serializePost(post));
});

router.post("/:slug/members", (req, res) => {
  const site = loadSite(req, res);
  if (!site) return;
  const email = normalizeEmail(bodyOf(req).email);
  if (!isEmail(email)) {
    return sendError(res, 400, "validation_error", "Please enter a valid email address.");
  }
  const existing = findMember.get(site.id, email);
  if (existing) {
    return res.json({ member: serializeMember(existing), already_member: true });
  }
  const id = crypto.randomUUID();
  insertMember.run(id, site.id, email, nowIso());
  const member = db.prepare("SELECT * FROM members WHERE id = ?").get(id);
  res.status(201).json({ member: serializeMember(member), already_member: false });
});

router.post("/:slug/ask", async (req, res) => {
  const site = loadSite(req, res);
  if (!site) return;
  const raw = bodyOf(req).question;
  const question = typeof raw === "string" ? raw.trim() : "";
  if (!question || question.length > 500) {
    return sendError(res, 400, "validation_error", "Please enter a question.");
  }

  const results = searchPosts(site.id, question);
  if (results.length === 0) return res.json({ mode: "search", results: [] });
  if (!answerMode) return res.json({ mode: "search", results });

  const outcome = await writeAnswer(question, results);
  if (!outcome.ok) {
    return res.json({ mode: "search", results, answer_error: ANSWER_ERROR });
  }
  res.json({ mode: "answer", results, answer: outcome.answer, citations: outcome.citations });
});

module.exports = router;
