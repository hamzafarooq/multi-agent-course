const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const bcrypt = require("bcryptjs");
const { db, rebuildIndex } = require("./db");
const { nowIso, slugify, uniqueSlug, deriveExcerpt } = require("./lib/text");

const SEED_PATH = path.join(__dirname, "..", ".sprint-zero", "seed", "traversaal-posts.json");
const DEMO_EMAIL = "demo@traversaal.ai";
const DEMO_PASSWORD = "inkwell-demo";

function toIso(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? nowIso() : date.toISOString();
}

function loadSeedFile() {
  if (!fs.existsSync(SEED_PATH)) {
    throw new Error(
      `Seed file not found at ${SEED_PATH}.\n` +
        "The demo site cannot be loaded without it. Restore .sprint-zero/seed/traversaal-posts.json and run `node seed.js` again."
    );
  }
  return JSON.parse(fs.readFileSync(SEED_PATH, "utf8"));
}

function upsertWriter() {
  const existing = db.prepare("SELECT * FROM users WHERE email = ?").get(DEMO_EMAIL);
  if (existing) return existing;
  const user = {
    id: crypto.randomUUID(),
    email: DEMO_EMAIL,
    password_hash: bcrypt.hashSync(DEMO_PASSWORD, 10),
    created_at: nowIso(),
  };
  db.prepare(
    "INSERT INTO users (id, email, password_hash, created_at) VALUES (?, ?, ?, ?)"
  ).run(user.id, user.email, user.password_hash, user.created_at);
  return user;
}

function upsertSite(owner, site) {
  const accent = String(site.accent_color || "#000000").toLowerCase();
  const existing = db.prepare("SELECT * FROM sites WHERE owner_id = ?").get(owner.id);
  if (existing) {
    db.prepare(
      "UPDATE sites SET title = ?, description = ?, accent_color = ?, updated_at = ? WHERE id = ?"
    ).run(site.title, site.description || "", accent, nowIso(), existing.id);
    return db.prepare("SELECT * FROM sites WHERE id = ?").get(existing.id);
  }
  const slugTaken = db.prepare("SELECT 1 FROM sites WHERE slug = ?");
  const slug = uniqueSlug(slugify(site.title), (s) => slugTaken.get(s));
  const now = nowIso();
  const id = crypto.randomUUID();
  db.prepare(`
    INSERT INTO sites (id, owner_id, slug, title, description, accent_color, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  `).run(id, owner.id, slug, site.title, site.description || "", accent, now, now);
  return db.prepare("SELECT * FROM sites WHERE id = ?").get(id);
}

function upsertPosts(site, posts) {
  const findBySlug = db.prepare("SELECT id FROM posts WHERE site_id = ? AND slug = ?");
  const update = db.prepare(`
    UPDATE posts SET title = ?, body_markdown = ?, excerpt = ?, excerpt_explicit = 1,
                     status = 'published', published_at = ?, author_name = ?, updated_at = ?
    WHERE id = ?
  `);
  const insert = db.prepare(`
    INSERT INTO posts (id, site_id, title, slug, body_markdown, excerpt, excerpt_explicit,
                       status, published_at, author_name, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, 1, 'published', ?, ?, ?, ?)
  `);

  for (const entry of posts) {
    const publishedAt = toIso(entry.published_at);
    const body = entry.body_markdown || "";
    const excerpt = (entry.excerpt || "").trim() || deriveExcerpt(body, entry.title);
    const author = entry.author || site.title;
    const existing = findBySlug.get(site.id, entry.slug);
    if (existing) {
      update.run(entry.title, body, excerpt, publishedAt, author, nowIso(), existing.id);
    } else {
      insert.run(
        crypto.randomUUID(), site.id, entry.title, entry.slug, body, excerpt,
        publishedAt, author, publishedAt, publishedAt
      );
    }
  }
}

function runSeed() {
  const data = loadSeedFile();
  const seed = db.transaction(() => {
    const writer = upsertWriter();
    const site = upsertSite(writer, data.site);
    upsertPosts(site, data.posts || []);
    return site;
  });
  const site = seed();
  const indexed = rebuildIndex();
  const postCount = db
    .prepare("SELECT COUNT(*) AS n FROM posts WHERE site_id = ?")
    .get(site.id).n;

  console.log(`Seed complete: site "${site.title}" (/s/${site.slug}) with ${postCount} published posts` +
    (indexed === undefined ? " (FTS5 unavailable, LIKE search)" : `, ${indexed} indexed for Ask me`) + ".");
  console.log(`Demo writer login: ${DEMO_EMAIL} / ${DEMO_PASSWORD}`);
  return { email: DEMO_EMAIL, password: DEMO_PASSWORD, site };
}

if (require.main === module) {
  try {
    runSeed();
  } catch (err) {
    console.error("Seed failed:", err.message);
    process.exit(1);
  }
}

module.exports = { runSeed, SEED_PATH, DEMO_EMAIL, DEMO_PASSWORD };
