const express = require("express");
const crypto = require("crypto");
const { db, syncPostIndex } = require("../db");
const { requireAuth } = require("../auth");
const { sendError, bodyOf } = require("../lib/http");
const {
  nowIso,
  isHexColor,
  slugify,
  uniqueSlug,
  deriveExcerpt,
} = require("../lib/text");
const { serializeSite, serializePost } = require("../lib/serialize");

const router = express.Router();
router.use(requireAuth);

const findSiteByOwner = db.prepare("SELECT * FROM sites WHERE owner_id = ?");
const siteSlugExists = db.prepare("SELECT 1 FROM sites WHERE slug = ?");
const insertSite = db.prepare(`
  INSERT INTO sites (id, owner_id, slug, title, description, accent_color, created_at, updated_at)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?)
`);
const updateSite = db.prepare(
  "UPDATE sites SET title = ?, description = ?, accent_color = ?, updated_at = ? WHERE id = ?"
);
const findSiteById = db.prepare("SELECT * FROM sites WHERE id = ?");

const listPosts = db.prepare(
  "SELECT * FROM posts WHERE site_id = ? ORDER BY created_at DESC"
);
const findPostById = db.prepare("SELECT * FROM posts WHERE id = ?");
const postSlugExists = db.prepare("SELECT 1 FROM posts WHERE site_id = ? AND slug = ?");
const insertPost = db.prepare(`
  INSERT INTO posts (id, site_id, title, slug, body_markdown, excerpt, excerpt_explicit,
                     status, published_at, author_name, created_at, updated_at)
  VALUES (?, ?, ?, ?, ?, ?, ?, 'draft', NULL, ?, ?, ?)
`);
const updatePost = db.prepare(`
  UPDATE posts SET title = ?, body_markdown = ?, excerpt = ?, excerpt_explicit = ?,
                   author_name = ?, updated_at = ?
  WHERE id = ?
`);
const setStatus = db.prepare(
  "UPDATE posts SET status = ?, published_at = ?, updated_at = ? WHERE id = ?"
);
const deletePost = db.prepare("DELETE FROM posts WHERE id = ?");

function validateSite(body) {
  const title = typeof body.title === "string" ? body.title.trim() : "";
  const description = typeof body.description === "string" ? body.description.trim() : "";
  const accent = typeof body.accent_color === "string" ? body.accent_color.trim() : "";
  if (!title || title.length > 120 || description.length > 500 || !isHexColor(accent)) {
    return null;
  }
  return { title, description, accent_color: accent.toLowerCase() };
}

const SITE_VALIDATION_MESSAGE =
  "Title is required; accent_color must be a #rrggbb hex colour.";

router.post("/site", (req, res) => {
  const fields = validateSite(bodyOf(req));
  if (!fields) return sendError(res, 400, "validation_error", SITE_VALIDATION_MESSAGE);
  if (findSiteByOwner.get(req.user.id)) {
    return sendError(
      res,
      409,
      "site_exists",
      "You already have a site. Use PUT /me/site to change it."
    );
  }
  const id = crypto.randomUUID();
  const now = nowIso();
  const slug = uniqueSlug(slugify(fields.title), (s) => siteSlugExists.get(s));
  insertSite.run(id, req.user.id, slug, fields.title, fields.description, fields.accent_color, now, now);
  res.status(201).json(serializeSite(findSiteById.get(id)));
});

router.get("/site", (req, res) => {
  const site = findSiteByOwner.get(req.user.id);
  if (!site) return sendError(res, 404, "not_found", "You have not created a site yet.");
  res.json(serializeSite(site));
});

router.put("/site", (req, res) => {
  const fields = validateSite(bodyOf(req));
  if (!fields) return sendError(res, 400, "validation_error", SITE_VALIDATION_MESSAGE);
  const site = findSiteByOwner.get(req.user.id);
  if (!site) return sendError(res, 404, "not_found", "You have not created a site yet.");
  updateSite.run(fields.title, fields.description, fields.accent_color, nowIso(), site.id);
  res.json(serializeSite(findSiteById.get(site.id)));
});

router.get("/posts", (req, res) => {
  const site = findSiteByOwner.get(req.user.id);
  if (!site) return sendError(res, 404, "not_found", "You have not created a site yet.");
  const posts = listPosts.all(site.id).map((row) => serializePost(row, { summary: true }));
  res.json({ posts });
});

function readPostFields(body) {
  const title = typeof body.title === "string" ? body.title.trim() : "";
  if (!title || title.length > 200) return { error: "Title is required." };
  if (body.body_markdown !== undefined && typeof body.body_markdown !== "string") {
    return { error: "body_markdown must be a string." };
  }
  const bodyMarkdown = typeof body.body_markdown === "string" ? body.body_markdown : "";
  const excerpt = typeof body.excerpt === "string" ? body.excerpt.trim() : "";
  const authorName = typeof body.author_name === "string" ? body.author_name.trim() : "";
  return { title, bodyMarkdown, excerpt, authorName };
}

router.post("/posts", (req, res) => {
  const fields = readPostFields(bodyOf(req));
  if (fields.error) return sendError(res, 400, "validation_error", fields.error);
  const site = findSiteByOwner.get(req.user.id);
  if (!site) return sendError(res, 404, "not_found", "You have not created a site yet.");

  const id = crypto.randomUUID();
  const now = nowIso();
  const slug = uniqueSlug(slugify(fields.title), (s) => postSlugExists.get(site.id, s));
  const explicit = fields.excerpt ? 1 : 0;
  const excerpt = explicit ? fields.excerpt : deriveExcerpt(fields.bodyMarkdown, fields.title);
  const authorName = fields.authorName || site.title;
  insertPost.run(id, site.id, fields.title, slug, fields.bodyMarkdown, excerpt, explicit, authorName, now, now);
  res.status(201).json(serializePost(findPostById.get(id)));
});

function loadOwnedPost(req, res) {
  const post = findPostById.get(req.params.id);
  if (!post) {
    sendError(res, 404, "not_found", "Post not found.");
    return null;
  }
  const site = findSiteByOwner.get(req.user.id);
  if (!site || site.id !== post.site_id) {
    sendError(res, 403, "forbidden", "You do not own this post.");
    return null;
  }
  return post;
}

router.get("/posts/:id", (req, res) => {
  const post = loadOwnedPost(req, res);
  if (!post) return;
  res.json(serializePost(post));
});

router.put("/posts/:id", (req, res) => {
  const fields = readPostFields(bodyOf(req));
  if (fields.error) return sendError(res, 400, "validation_error", fields.error);
  const post = loadOwnedPost(req, res);
  if (!post) return;

  let explicit = post.excerpt_explicit;
  let excerpt = post.excerpt;
  if (fields.excerpt) {
    explicit = 1;
    excerpt = fields.excerpt;
  } else if (!explicit) {
    excerpt = deriveExcerpt(fields.bodyMarkdown, fields.title);
  }
  const authorName = fields.authorName || post.author_name;
  updatePost.run(fields.title, fields.bodyMarkdown, excerpt, explicit, authorName, nowIso(), post.id);
  const updated = findPostById.get(post.id);
  syncPostIndex(updated);
  res.json(serializePost(updated));
});

router.post("/posts/:id/publish", (req, res) => {
  const post = loadOwnedPost(req, res);
  if (!post) return;
  if (post.status !== "published") {
    const now = nowIso();
    setStatus.run("published", post.published_at || now, now, post.id);
  }
  const updated = findPostById.get(post.id);
  syncPostIndex(updated);
  res.json(serializePost(updated));
});

router.post("/posts/:id/unpublish", (req, res) => {
  const post = loadOwnedPost(req, res);
  if (!post) return;
  if (post.status !== "draft") {
    setStatus.run("draft", post.published_at, nowIso(), post.id);
  }
  const updated = findPostById.get(post.id);
  syncPostIndex(updated);
  res.json(serializePost(updated));
});

router.delete("/posts/:id", (req, res) => {
  const post = loadOwnedPost(req, res);
  if (!post) return;
  deletePost.run(post.id);
  syncPostIndex({ id: post.id, status: "deleted" });
  res.status(204).end();
});

module.exports = router;
