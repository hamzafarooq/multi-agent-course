// Inkwell API integration tests. Run from server/: `node tests/integration.test.js`
// against a server already listening on BASE (default http://localhost:3001).
//
// Ask me expectations: set ASK_EXPECT=search|answer|degraded to force a mode.
// Otherwise it is inferred: ANTHROPIC_API_KEY present in this shell -> "answer",
// absent -> "search". The key itself is never read beyond its presence.

const BASE = process.env.BASE_URL || "http://localhost:3001";
const SITE = "traversaal-ai";
const DEMO = { email: "demo@traversaal.ai", password: "inkwell-demo" };
const LEAK_PHRASE = "zebrafish quantum marmalade";
const ASK_EXPECT =
  process.env.ASK_EXPECT || (process.env.ANTHROPIC_API_KEY ? "answer" : "search");

let passed = 0;
let failed = 0;
const failures = [];

function check(name, cond, detail) {
  if (cond) {
    passed += 1;
    console.log(`PASS ${name}`);
  } else {
    failed += 1;
    failures.push(name);
    console.log(`FAIL ${name}${detail === undefined ? "" : " -> " + JSON.stringify(detail)}`);
  }
}

async function call(method, path, { body, token, raw } = {}) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: raw !== undefined ? raw : body === undefined ? undefined : JSON.stringify(body),
  });
  const text = await res.text();
  let json = null;
  try {
    json = text ? JSON.parse(text) : null;
  } catch {
    json = null;
  }
  return { status: res.status, json, text };
}

const isUuid = (v) =>
  typeof v === "string" && /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(v);
const isIso = (v) => typeof v === "string" && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(v);
const sameKeys = (obj, keys) =>
  obj && typeof obj === "object" && JSON.stringify(Object.keys(obj).sort()) === JSON.stringify([...keys].sort());

const POST_SUMMARY_KEYS = [
  "id", "site_id", "title", "slug", "excerpt", "status", "published_at",
  "author_name", "reading_time_minutes", "created_at", "updated_at",
];
const POST_FULL_KEYS = [...POST_SUMMARY_KEYS, "body_markdown"];
const SITE_KEYS = ["id", "slug", "title", "description", "accent_color", "created_at", "updated_at"];
const ASK_RESULT_KEYS = ["post_id", "title", "slug", "excerpt", "snippet"];

async function main() {
  const stamp = Date.now();
  console.log(`Inkwell integration tests against ${BASE} (ASK_EXPECT=${ASK_EXPECT})`);

  // ---- health -------------------------------------------------------------
  const health = await call("GET", "/health");
  check("GET /health returns 200 ok", health.status === 200 && health.json?.status === "ok", health.json);
  check("GET /health reports fts5 boolean", typeof health.json?.fts5 === "boolean", health.json);
  const expectedHealthMode = ASK_EXPECT === "search" ? "search" : "answer";
  check(`GET /health answer_mode is "${expectedHealthMode}"`, health.json?.answer_mode === expectedHealthMode, health.json);

  // ---- auth ---------------------------------------------------------------
  const freshEmail = `qa-${stamp}@example.com`;
  const freshPassword = "compost-2026";
  const signup = await call("POST", "/auth/signup", { body: { email: freshEmail.toUpperCase(), password: freshPassword } });
  check("POST /auth/signup fresh email -> 201", signup.status === 201, signup.json);
  check("signup returns access_token, user, site:null",
    typeof signup.json?.access_token === "string" && signup.json?.site === null &&
    sameKeys(signup.json?.user, ["id", "email", "created_at"]), signup.json);
  check("signup lowercases and trims email", signup.json?.user?.email === freshEmail, signup.json?.user);
  check("signup user id is UUID v4 and created_at ISO", isUuid(signup.json?.user?.id) && isIso(signup.json?.user?.created_at), signup.json?.user);
  const freshToken = signup.json?.access_token;

  const dupe = await call("POST", "/auth/signup", { body: DEMO });
  check("POST /auth/signup demo email -> 409 email_taken", dupe.status === 409 && dupe.json?.error === "email_taken", dupe.json);
  check("409 message contains 'already'", /already/.test(dupe.json?.message || ""), dupe.json);

  const shortPw = await call("POST", "/auth/signup", { body: { email: `qa-short-${stamp}@example.com`, password: "short" } });
  check("POST /auth/signup short password -> 400 validation_error", shortPw.status === 400 && shortPw.json?.error === "validation_error", shortPw.json);

  const login = await call("POST", "/auth/login", { body: DEMO });
  check("POST /auth/login demo -> 200 with site traversaal-ai", login.status === 200 && login.json?.site?.slug === SITE, login.json?.site);
  check("login site has exactly the Site keys", sameKeys(login.json?.site, SITE_KEYS), login.json?.site);
  const demoToken = login.json?.access_token;

  const badLogin = await call("POST", "/auth/login", { body: { email: DEMO.email, password: "wrong-password" } });
  check("POST /auth/login wrong password -> 401 invalid_credentials", badLogin.status === 401 && badLogin.json?.error === "invalid_credentials", badLogin.json);
  check("401 login message contains 'Invalid'", /Invalid/.test(badLogin.json?.message || ""), badLogin.json);

  const emptyLogin = await call("POST", "/auth/login", { body: { email: DEMO.email } });
  check("POST /auth/login missing password -> 400", emptyLogin.status === 400 && emptyLogin.json?.error === "validation_error", emptyLogin.json);

  const me = await call("GET", "/auth/me", { token: demoToken });
  check("GET /auth/me with token -> 200 user + site", me.status === 200 && me.json?.user?.email === DEMO.email && me.json?.site?.slug === SITE, me.json);
  const meExpired = await call("GET", "/auth/me", { token: "expired" });
  check("GET /auth/me with token 'expired' -> 401 unauthorized shape",
    meExpired.status === 401 && meExpired.json?.error === "unauthorized" && meExpired.json?.message === "Missing or invalid token.", meExpired.json);
  const meNone = await call("GET", "/me/posts");
  check("GET /me/posts without token -> 401 unauthorized", meNone.status === 401 && meNone.json?.error === "unauthorized", meNone.json);

  // ---- site ---------------------------------------------------------------
  const noSite = await call("GET", "/me/site", { token: freshToken });
  check("GET /me/site before create -> 404 not_found", noSite.status === 404 && noSite.json?.error === "not_found", noSite.json);
  const noPosts = await call("GET", "/me/posts", { token: freshToken });
  check("GET /me/posts before site -> 404", noPosts.status === 404, noPosts.json);

  const badSite = await call("POST", "/me/site", { token: freshToken, body: { title: "Field Notes", description: "", accent_color: "green" } });
  check("POST /me/site bad accent -> 400 validation_error", badSite.status === 400 && badSite.json?.error === "validation_error", badSite.json);

  const siteRes = await call("POST", "/me/site", { token: freshToken, body: { title: "Field Notes", description: "Essays on soil and weather", accent_color: "#1F6F43" } });
  check("POST /me/site -> 201 Site", siteRes.status === 201 && sameKeys(siteRes.json, SITE_KEYS), siteRes.json);
  check("site slug derived from title", /^field-notes(-\d+)?$/.test(siteRes.json?.slug || ""), siteRes.json?.slug);
  check("site accent_color stored lowercased", siteRes.json?.accent_color === "#1f6f43", siteRes.json?.accent_color);
  const fresh = siteRes.json;

  const siteAgain = await call("POST", "/me/site", { token: freshToken, body: { title: "Other", description: "", accent_color: "#000000" } });
  check("POST /me/site twice -> 409 site_exists", siteAgain.status === 409 && siteAgain.json?.error === "site_exists", siteAgain.json);

  const getSite = await call("GET", "/me/site", { token: freshToken });
  check("GET /me/site -> 200 same site", getSite.status === 200 && getSite.json?.id === fresh.id, getSite.json);

  const putSite = await call("PUT", "/me/site", { token: freshToken, body: { title: "Field Notes", description: "Essays on soil, weather and patience", accent_color: "#1f6f43" } });
  check("PUT /me/site -> 200 updated, slug unchanged", putSite.status === 200 && putSite.json?.slug === fresh.slug && putSite.json?.description === "Essays on soil, weather and patience", putSite.json);

  const loginFresh = await call("POST", "/auth/login", { body: { email: freshEmail, password: freshPassword } });
  check("login after site creation returns the site", loginFresh.status === 200 && loginFresh.json?.site?.id === fresh.id, loginFresh.json?.site);

  const publicSite = await call("GET", `/sites/${fresh.slug}`);
  check("GET /sites/:slug fresh site -> 200 public Site", publicSite.status === 200 && publicSite.json?.id === fresh.id && sameKeys(publicSite.json, SITE_KEYS), publicSite.json);
  const emptyFeed = await call("GET", `/sites/${fresh.slug}/posts`);
  check("GET /sites/:slug/posts empty site -> { posts: [] }", emptyFeed.status === 200 && Array.isArray(emptyFeed.json?.posts) && emptyFeed.json.posts.length === 0, emptyFeed.json);
  const emptyAsk = await call("POST", `/sites/${fresh.slug}/ask`, { body: { question: "mulch" } });
  check("POST ask on site with zero published posts -> search, results []",
    emptyAsk.status === 200 && sameKeys(emptyAsk.json, ["mode", "results"]) && emptyAsk.json.mode === "search" && emptyAsk.json.results.length === 0, emptyAsk.json);

  // ---- posts: core loop ----------------------------------------------------
  const body1 = "Mulch is the cheapest thing you can do for soil. It shades the surface and feeds the worms. It also holds water.";
  const badPost = await call("POST", "/me/posts", { token: freshToken, body: { title: "", body_markdown: body1 } });
  check("POST /me/posts empty title -> 400 'Title is required.'", badPost.status === 400 && badPost.json?.message === "Title is required.", badPost.json);

  const created = await call("POST", "/me/posts", { token: freshToken, body: { title: "On mulch", body_markdown: body1, excerpt: "" } });
  check("POST /me/posts -> 201 full draft Post", created.status === 201 && sameKeys(created.json, POST_FULL_KEYS), created.json);
  check("new post is draft with published_at null", created.json?.status === "draft" && created.json?.published_at === null, created.json);
  check("new post slug derived from title", created.json?.slug === "on-mulch", created.json?.slug);
  check("excerpt derived from first two sentences", created.json?.excerpt === "Mulch is the cheapest thing you can do for soil. It shades the surface and feeds the worms.", created.json?.excerpt);
  check("author_name defaults to site title", created.json?.author_name === "Field Notes", created.json?.author_name);
  check("reading_time_minutes is 1 for a short body", created.json?.reading_time_minutes === 1, created.json?.reading_time_minutes);
  check("post site_id is the writer's site; no owner_id/user_id/password_hash", created.json?.site_id === fresh.id && !("owner_id" in created.json) && !("user_id" in created.json), created.json);
  const post = created.json;

  const dupeTitle = await call("POST", "/me/posts", { token: freshToken, body: { title: "On mulch", body_markdown: "Second one." } });
  check("second post with same title gets slug on-mulch-2", dupeTitle.status === 201 && dupeTitle.json?.slug === "on-mulch-2", dupeTitle.json?.slug);

  const list = await call("GET", "/me/posts", { token: freshToken });
  check("GET /me/posts -> { posts } summaries newest first", list.status === 200 && list.json?.posts?.length === 2 && list.json.posts[0].id === dupeTitle.json.id && list.json.posts.every((p) => sameKeys(p, POST_SUMMARY_KEYS)), list.json);

  const getOne = await call("GET", `/me/posts/${post.id}`, { token: freshToken });
  check("GET /me/posts/:id -> 200 full post with body_markdown", getOne.status === 200 && getOne.json?.body_markdown === body1, getOne.json);

  const notMine = await call("GET", `/me/posts/${post.id}`, { token: demoToken });
  check("GET /me/posts/:id as another writer -> 403 forbidden", notMine.status === 403 && notMine.json?.error === "forbidden", notMine.json);
  const unknownPost = await call("GET", `/me/posts/00000000-0000-4000-8000-000000000000`, { token: freshToken });
  check("GET /me/posts/:id unknown -> 404 not_found", unknownPost.status === 404 && unknownPost.json?.error === "not_found", unknownPost.json);

  const body2 = body1 + " It holds water through August.";
  const updated = await call("PUT", `/me/posts/${post.id}`, { token: freshToken, body: { title: "On mulch", body_markdown: body2, excerpt: "" } });
  check("PUT /me/posts/:id -> 200 body updated, status/slug unchanged", updated.status === 200 && updated.json?.body_markdown === body2 && updated.json?.status === "draft" && updated.json?.slug === "on-mulch", updated.json);

  const hiddenFeed = await call("GET", `/sites/${fresh.slug}/posts`);
  check("draft absent from public feed", hiddenFeed.json?.posts?.length === 0, hiddenFeed.json);
  const hiddenPost = await call("GET", `/sites/${fresh.slug}/posts/on-mulch`);
  check("draft public GET by slug -> 404", hiddenPost.status === 404 && hiddenPost.json?.error === "not_found", hiddenPost.json);

  const published = await call("POST", `/me/posts/${post.id}/publish`, { token: freshToken });
  check("POST publish -> 200 status published, published_at set", published.status === 200 && published.json?.status === "published" && isIso(published.json?.published_at), published.json);
  const publishedAt = published.json?.published_at;
  check("published_at is within a minute of now", Math.abs(Date.now() - new Date(publishedAt).getTime()) < 60_000, publishedAt);

  const republished = await call("POST", `/me/posts/${post.id}/publish`, { token: freshToken });
  check("publish is idempotent (same published_at)", republished.status === 200 && republished.json?.published_at === publishedAt, republished.json?.published_at);

  const feed = await call("GET", `/sites/${fresh.slug}/posts`);
  check("published post appears in public feed as a summary", feed.json?.posts?.length === 1 && feed.json.posts[0].slug === "on-mulch" && sameKeys(feed.json.posts[0], POST_SUMMARY_KEYS), feed.json);
  const publicPost = await call("GET", `/sites/${fresh.slug}/posts/on-mulch`);
  check("GET /sites/:slug/posts/:postSlug -> 200 full post", publicPost.status === 200 && publicPost.json?.body_markdown === body2 && sameKeys(publicPost.json, POST_FULL_KEYS), publicPost.json);

  const askFresh = await call("POST", `/sites/${fresh.slug}/ask`, { body: { question: "what does mulch do for soil?" } });
  check("published post is findable in Ask me on its own site", askFresh.json?.results?.[0]?.post_id === post.id, askFresh.json);
  const askCross = await call("POST", `/sites/${SITE}/ask`, { body: { question: "mulch worms" } });
  check("Ask me is scoped: mulch post absent from traversaal-ai", (askCross.json?.results || []).every((r) => r.post_id !== post.id), askCross.json);

  const editPublished = await call("PUT", `/me/posts/${post.id}`, { token: freshToken, body: { title: "On mulch, revisited", body_markdown: body2 + " Edited.", excerpt: "" } });
  check("editing a published post keeps slug and published_at", editPublished.status === 200 && editPublished.json?.slug === "on-mulch" && editPublished.json?.published_at === publishedAt && editPublished.json?.status === "published", editPublished.json);

  const unpublished = await call("POST", `/me/posts/${post.id}/unpublish`, { token: freshToken });
  check("POST unpublish -> 200 draft, published_at kept", unpublished.status === 200 && unpublished.json?.status === "draft" && unpublished.json?.published_at === publishedAt, unpublished.json);
  const goneFeed = await call("GET", `/sites/${fresh.slug}/posts`);
  const gonePost = await call("GET", `/sites/${fresh.slug}/posts/on-mulch`);
  const goneAsk = await call("POST", `/sites/${fresh.slug}/ask`, { body: { question: "mulch" } });
  check("unpublished post leaves feed, address (404) and Ask me", goneFeed.json?.posts?.length === 0 && gonePost.status === 404 && goneAsk.json?.results?.length === 0, { feed: goneFeed.json, post: gonePost.status, ask: goneAsk.json });

  const back = await call("POST", `/me/posts/${post.id}/publish`, { token: freshToken });
  check("republish keeps original published_at", back.json?.status === "published" && back.json?.published_at === publishedAt, back.json?.published_at);

  const del = await call("DELETE", `/me/posts/${dupeTitle.json.id}`, { token: freshToken });
  check("DELETE /me/posts/:id -> 204 no body", del.status === 204 && del.text === "", { status: del.status, text: del.text });
  const afterDel = await call("GET", `/me/posts/${dupeTitle.json.id}`, { token: freshToken });
  check("deleted post -> 404", afterDel.status === 404, afterDel.json);

  // ---- seeded site ----------------------------------------------------------
  const seedSite = await call("GET", `/sites/${SITE}`);
  check("GET /sites/traversaal-ai -> seeded Site", seedSite.status === 200 && seedSite.json?.title === "Traversaal.ai" && seedSite.json?.accent_color === "#fc654a" &&
    seedSite.json?.description === "Technical insights and updates from the forefront of AI orchestration", seedSite.json);
  const seedFeed = await call("GET", `/sites/${SITE}/posts`);
  const sp = seedFeed.json?.posts || [];
  check("seeded feed has 10 published summaries", sp.length === 10 && sp.every((p) => p.status === "published" && sameKeys(p, POST_SUMMARY_KEYS)), sp.length);
  check("seeded feed newest first: self-hosting post first", sp[0]?.slug === "self-hosting-llms-cost-benefit-framework-api-vs-on-premise", sp[0]?.slug);
  check("seeded feed oldest last: LLM caching post", /caching/.test(sp[9]?.slug || ""), sp[9]?.slug);
  check("seeded feed sorted by published_at descending",
    sp.every((p, i) => i === 0 || new Date(sp[i - 1].published_at) >= new Date(p.published_at)) && sp.every((p) => isIso(p.published_at)), sp.map((p) => p.published_at));
  check("seeded posts authored by Hamza Farooq", sp.every((p) => p.author_name === "Hamza Farooq"), sp.map((p) => p.author_name));
  check("no duplicate slugs in seeded feed", new Set(sp.map((p) => p.slug)).size === sp.length);
  const routerPost = await call("GET", `/sites/${SITE}/posts/llm-router-cost-optimization-route-requests-cheapest-model`);
  check("seeded router post readable with body", routerPost.status === 200 && routerPost.json?.author_name === "Hamza Farooq" && routerPost.json?.body_markdown?.length > 500, routerPost.status);
  const demoPosts = await call("GET", "/me/posts", { token: demoToken });
  const demoBaseline = demoPosts.json?.posts?.length ?? -1;
  check("demo writer /me/posts has exactly 10 published rows", demoPosts.json?.posts?.filter((p) => p.status === "published").length === 10, demoPosts.json?.posts?.map((p) => [p.slug, p.status]));
  const noSuchSite = await call("GET", "/sites/no-such-site-xyz");
  check("GET /sites/unknown -> 404 not_found", noSuchSite.status === 404 && noSuchSite.json?.error === "not_found", noSuchSite.json);
  const noSuchPost = await call("GET", `/sites/${SITE}/posts/no-such-post-xyz`);
  check("GET /sites/:slug/posts/unknown -> 404", noSuchPost.status === 404, noSuchPost.json);

  // ---- members --------------------------------------------------------------
  const memberEmail = `  QA+${stamp}@Example.com `;
  const normalized = `qa+${stamp}@example.com`;
  const join1 = await call("POST", `/sites/${SITE}/members`, { body: { email: memberEmail } });
  check("POST members new email -> 201 already_member false", join1.status === 201 && join1.json?.already_member === false, join1.json);
  check("member email trimmed and lowercased, status free", join1.json?.member?.email === normalized && join1.json?.member?.status === "free" &&
    sameKeys(join1.json?.member, ["id", "site_id", "email", "status", "created_at"]), join1.json?.member);
  const join2 = await call("POST", `/sites/${SITE}/members`, { body: { email: memberEmail } });
  check("POST members repeat -> 200 already_member true, same id", join2.status === 200 && join2.json?.already_member === true && join2.json?.member?.id === join1.json?.member?.id, join2.json);
  const join3 = await call("POST", `/sites/${fresh.slug}/members`, { body: { email: normalized } });
  check("same email on a different site -> 201 second row", join3.status === 201 && join3.json?.member?.site_id === fresh.id && join3.json?.member?.id !== join1.json?.member?.id, join3.json);
  const badJoin = await call("POST", `/sites/${SITE}/members`, { body: { email: "not-an-email" } });
  check("POST members invalid email -> 400", badJoin.status === 400 && badJoin.json?.message === "Please enter a valid email address.", badJoin.json);
  const joinNoSite = await call("POST", "/sites/no-such-site-xyz/members", { body: { email: normalized } });
  check("POST members unknown site -> 404", joinNoSite.status === 404, joinNoSite.json);

  // ---- ask me --------------------------------------------------------------
  const badAsk = await call("POST", `/sites/${SITE}/ask`, { body: { question: "   " } });
  check("POST ask empty question -> 400 'Please enter a question.'", badAsk.status === 400 && badAsk.json?.message === "Please enter a question.", badAsk.json);
  const askNoSite = await call("POST", "/sites/no-such-site-xyz/ask", { body: { question: "hello" } });
  check("POST ask unknown site -> 404", askNoSite.status === 404, askNoSite.json);

  const sourdough = await call("POST", `/sites/${SITE}/ask`, { body: { question: "how do I bake sourdough?" } });
  check("ask sourdough -> exactly { mode: 'search', results: [] } (no answer, no answer_error)",
    sourdough.status === 200 && sameKeys(sourdough.json, ["mode", "results"]) && sourdough.json.mode === "search" && sourdough.json.results.length === 0, sourdough.json);

  const punct = await call("POST", `/sites/${SITE}/ask`, { body: { question: 'what "is" NOT (this) AND that* ^ near/2 -x?' } });
  check("ask with FTS operators and quotes never errors", punct.status === 200 && ["search", "answer"].includes(punct.json?.mode), punct.json);

  const t0 = Date.now();
  const pd = await call("POST", `/sites/${SITE}/ask`, { body: { question: "what is progressive disclosure in context engineering?" } });
  const pdMs = Date.now() - t0;
  const pdr = pd.json?.results || [];
  check("ask progressive disclosure -> 200 within 15s", pd.status === 200 && pdMs < 15_000, { status: pd.status, ms: pdMs });
  check("first result is the context-engineering article", /^Context Engineering Techniques/.test(pdr[0]?.title || ""), pdr[0]?.title);
  check("results have exactly post_id,title,slug,excerpt,snippet and <= 5 items", pdr.length > 0 && pdr.length <= 5 && pdr.every((r) => sameKeys(r, ASK_RESULT_KEYS)), pdr.map((r) => Object.keys(r)));
  check("first snippet highlights matches with <mark>", /<mark>[^<]+<\/mark>/.test(pdr[0]?.snippet || ""), pdr[0]?.snippet);
  check("results come only from published traversaal-ai posts", pdr.every((r) => sp.some((p) => p.id === r.post_id && p.slug === r.slug)), pdr.map((r) => r.slug));

  if (ASK_EXPECT === "search") {
    check("search mode: mode 'search' with results, no answer/citations/answer_error",
      pd.json?.mode === "search" && sameKeys(pd.json, ["mode", "results"]), Object.keys(pd.json || {}));
  } else if (ASK_EXPECT === "answer") {
    check("answer mode: mode 'answer'", pd.json?.mode === "answer", { mode: pd.json?.mode, answer_error: pd.json?.answer_error });
    check("answer mode: non-empty answer string", typeof pd.json?.answer === "string" && pd.json.answer.trim().length > 0, pd.json?.answer);
    check("answer mode: citations array, every post_id in results",
      Array.isArray(pd.json?.citations) && pd.json.citations.every((c) => sameKeys(c, ["post_id", "title", "slug"]) && pdr.some((r) => r.post_id === c.post_id)), pd.json?.citations);
    check("answer mode: at least one citation, naming the context-engineering article",
      (pd.json?.citations || []).some((c) => /^Context Engineering Techniques/.test(c.title)), pd.json?.citations);
    check("answer mode: no answer_error key", !("answer_error" in (pd.json || {})), pd.json?.answer_error);
  } else {
    check("degraded: mode 'search' with results and answer_error",
      pd.json?.mode === "search" && pdr.length > 0 && typeof pd.json?.answer_error === "string", pd.json);
    check("degraded: answer_error contains 'could not be written'", /could not be written/.test(pd.json?.answer_error || ""), pd.json?.answer_error);
    check("degraded: no answer/citations keys", !("answer" in (pd.json || {})) && !("citations" in (pd.json || {})), Object.keys(pd.json || {}));
  }

  const mlops = await call("POST", `/sites/${SITE}/ask`, { body: { question: "why does MLOps observability break for agents?" } });
  check("ask MLOps -> first result is the observability article", /^Why MLOps Observability Breaks/.test(mlops.json?.results?.[0]?.title || ""), mlops.json?.results?.[0]?.title);
  if (ASK_EXPECT === "answer") {
    check("answer mode: MLOps answer cites the observability article",
      mlops.json?.mode === "answer" && (mlops.json?.citations || []).some((c) => /^Why MLOps Observability Breaks/.test(c.title)), { mode: mlops.json?.mode, citations: mlops.json?.citations });
  }

  // ---- draft leak (seeded writer) -------------------------------------------
  const leakDraft = await call("POST", "/me/posts", { token: demoToken, body: { title: "Compost secrets", body_markdown: `Nobody tells you the pile should smell like a forest floor. The secret ingredient is ${LEAK_PHRASE}.` } });
  check("demo writer creates draft 'Compost secrets'", leakDraft.status === 201 && leakDraft.json?.status === "draft", leakDraft.json);
  const leakSlug = leakDraft.json?.slug;
  try {
    const leakFeed = await call("GET", `/sites/${SITE}/posts`);
    check("draft absent from GET /sites/traversaal-ai/posts (title, slug, phrase)",
      leakFeed.json?.posts?.length === 10 && !leakFeed.json.posts.some((p) => /^Compost secrets/.test(p.title) || p.slug === leakSlug) && !leakFeed.text.includes(LEAK_PHRASE), leakFeed.json?.posts?.map((p) => p.slug));
    const leakGet = await call("GET", `/sites/${SITE}/posts/${leakSlug}`);
    check("draft direct GET by slug -> 404, no body", leakGet.status === 404 && !leakGet.text.includes(LEAK_PHRASE), leakGet.json);
    const leakAsk = await call("POST", `/sites/${SITE}/ask`, { body: { question: LEAK_PHRASE } });
    check(`ask '${LEAK_PHRASE}' -> results [] and no answer (${ASK_EXPECT} mode)`,
      leakAsk.status === 200 && sameKeys(leakAsk.json, ["mode", "results"]) && leakAsk.json.mode === "search" && leakAsk.json.results.length === 0 && !leakAsk.text.includes(LEAK_PHRASE), leakAsk.json);
    const leakAsk2 = await call("POST", `/sites/${SITE}/ask`, { body: { question: "compost secrets forest floor pile" } });
    check("ask with the draft's other words -> no result for the draft", (leakAsk2.json?.results || []).every((r) => r.post_id !== leakDraft.json?.id) && !leakAsk2.text.includes(LEAK_PHRASE), leakAsk2.json);
    const demoList = await call("GET", "/me/posts", { token: demoToken });
    check("draft visible to its owner in /me/posts (one more row than before)", demoList.json?.posts?.length === demoBaseline + 1 && demoList.json.posts[0].id === leakDraft.json?.id, demoList.json?.posts?.length);
  } finally {
    const cleanup = await call("DELETE", `/me/posts/${leakDraft.json?.id}`, { token: demoToken });
    check("cleanup: draft deleted (204), demo writer back to baseline row count", cleanup.status === 204 && (await call("GET", "/me/posts", { token: demoToken })).json?.posts?.length === demoBaseline, cleanup.status);
  }

  // ---- conventions ------------------------------------------------------------
  const unknownRoute = await call("GET", "/nope/nothing");
  check("unknown route -> 404 not_found", unknownRoute.status === 404 && unknownRoute.json?.error === "not_found", unknownRoute.json);
  const badJson = await call("POST", "/auth/login", { raw: "{not json", body: {} });
  check("invalid JSON body -> 400 validation_error", badJson.status === 400 && badJson.json?.error === "validation_error", badJson.json);

  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed) {
    console.log("Failures:\n - " + failures.join("\n - "));
    process.exit(1);
  }
}

main().catch((err) => {
  console.error("Test run crashed:", err);
  process.exit(1);
});
