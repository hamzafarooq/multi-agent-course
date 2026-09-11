const { readingTimeMinutes } = require("./text");

function serializeUser(row) {
  return { id: row.id, email: row.email, created_at: row.created_at };
}

function serializeSite(row) {
  if (!row) return null;
  return {
    id: row.id,
    slug: row.slug,
    title: row.title,
    description: row.description,
    accent_color: row.accent_color,
    created_at: row.created_at,
    updated_at: row.updated_at,
  };
}

function serializePost(row, { summary = false } = {}) {
  const post = {
    id: row.id,
    site_id: row.site_id,
    title: row.title,
    slug: row.slug,
  };
  if (!summary) post.body_markdown = row.body_markdown;
  post.excerpt = row.excerpt;
  post.status = row.status;
  post.published_at = row.published_at;
  post.author_name = row.author_name;
  post.reading_time_minutes = readingTimeMinutes(row.body_markdown);
  post.created_at = row.created_at;
  post.updated_at = row.updated_at;
  return post;
}

function serializeMember(row) {
  return {
    id: row.id,
    site_id: row.site_id,
    email: row.email,
    status: row.status,
    created_at: row.created_at,
  };
}

module.exports = { serializeUser, serializeSite, serializePost, serializeMember };
