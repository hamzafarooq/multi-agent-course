const path = require("path");
const Database = require("better-sqlite3");

const DB_PATH = process.env.DB_PATH || path.join(__dirname, "data.db");
const db = new Database(DB_PATH);
db.pragma("foreign_keys = ON");

db.exec(`
  CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
  );

  CREATE TABLE IF NOT EXISTS sites (
    id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL UNIQUE REFERENCES users(id),
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    accent_color TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
  );

  CREATE TABLE IF NOT EXISTS posts (
    id TEXT PRIMARY KEY,
    site_id TEXT NOT NULL REFERENCES sites(id),
    title TEXT NOT NULL,
    slug TEXT NOT NULL,
    body_markdown TEXT NOT NULL DEFAULT '',
    excerpt TEXT NOT NULL,
    excerpt_explicit INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL CHECK (status IN ('draft', 'published')),
    published_at TEXT,
    author_name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (site_id, slug)
  );

  CREATE TABLE IF NOT EXISTS members (
    id TEXT PRIMARY KEY,
    site_id TEXT NOT NULL REFERENCES sites(id),
    email TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'free',
    created_at TEXT NOT NULL,
    UNIQUE (site_id, email)
  );
`);

let fts5 = true;
try {
  db.exec(`
    CREATE VIRTUAL TABLE IF NOT EXISTS posts_fts
    USING fts5(post_id UNINDEXED, title, body_markdown, tokenize = 'porter unicode61')
  `);
} catch (err) {
  fts5 = false;
  console.warn("WARNING: this SQLite build has no FTS5 module (" + err.message + ").");
  console.warn("WARNING: Ask me is running in degraded LIKE-search mode. /health reports fts5: false.");
}

const deleteFromIndex = fts5 ? db.prepare("DELETE FROM posts_fts WHERE post_id = ?") : null;
const insertIntoIndex = fts5
  ? db.prepare("INSERT INTO posts_fts (post_id, title, body_markdown) VALUES (?, ?, ?)")
  : null;

function syncPostIndex(post) {
  if (!fts5) return;
  deleteFromIndex.run(post.id);
  if (post.status === "published") {
    insertIntoIndex.run(post.id, post.title, post.body_markdown);
  }
}

function rebuildIndex() {
  if (!fts5) return;
  const rebuild = db.transaction(() => {
    db.prepare("DELETE FROM posts_fts").run();
    const published = db
      .prepare("SELECT id, title, body_markdown FROM posts WHERE status = 'published'")
      .all();
    for (const post of published) {
      insertIntoIndex.run(post.id, post.title, post.body_markdown);
    }
    return published.length;
  });
  return rebuild();
}

module.exports = { db, fts5, syncPostIndex, rebuildIndex };
