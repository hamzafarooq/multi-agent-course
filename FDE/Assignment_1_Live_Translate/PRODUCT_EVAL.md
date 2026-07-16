# Product Evaluation — Live Translate

- **Student:** Sarang
- **Date:** 2026-07-16
- **Video demo:** TODO: add video URL after recording
- **LLM provider / model:** Anthropic — claude-sonnet-4-6
- **Backend target:** https://sarang-livetranslate-gw.fly.dev (deployed) · http://localhost:8787 (local rubric run)

## Verdict

> This is shippable. The core contract, two-tier cache, tracing, and SLA are all solid and independently verified against a real, uncontrolled website (homedepot.com), not just the demo page — a genuine product page (212 text chunks) translated correctly with prices, model codes, and SKUs preserved, and a re-translate showed a 98× cache speedup (199,564 ms → 2,035 ms) with a 99% hit rate. The strongest part is caching correctness — it's provable, persistent, and dramatically faster on repeat. The weakest part is handling very large pages: a 91-result search listing (653 text chunks) timed out on a single giant batch call, which is a real scaling gap worth fixing before pointing this at arbitrary large e-commerce pages.

**Rubric score (from `eval/report.json`):** 70 / 70 auto (+ 30 manual)

## 1. Performance & cost (from `benchmark/bench.py`, fresh cache, localhost)

| Metric | Result | SLA | Pass? |
|---|---|---|---|
| Cache hit p95 | 11.2 ms | ≤ 60 ms | ✅ |
| Cache miss p95 | 1749.3 ms | ≤ 3500 ms | ✅ |
| Cache hit rate | 77.5 % | ≥ 60 % | ✅ |
| Throughput | 1062.9 req/s | ≥ 20 | ✅ |
| Error rate | 0.0 % | ≤ 1 % | ✅ |
| Cost per miss | $0.00017 | — | — |
| Monthly savings from cache | $65.81 (at 500k/mo, placeholder pricing) | — | — |

`python benchmark/bench.py` exits `0` — all SLAs met. (A second independent fresh-cache run in `benchmark/_bench.json` corroborates: hit p95 10.5 ms, miss p95 2061 ms, hit rate 75%, 1191 rps — same conclusion.)

## 2. Live-website test

- **Site tested:** `https://www.homedepot.com` — a real DEWALT drill product page (`/p/DEWALT-Atomic-20V-.../322138372`), loaded via the console-loader mechanism pointed at the **deployed** gateway (not localhost), per the assignment's requirement that the live test run against the public URL.
- **Translated whole page?** Yes. 212 text chunks (69 cache hits on first pass) translated end-to-end — header nav, breadcrumbs, product title, price block, bullet features, stock/store info, and footer all flipped to Mexican Spanish. Layout stayed intact.
- **Coverage gaps:** Text baked into raster images (the "SPECIAL BUY" price tag graphic, the "VALUE OF $307" badge graphic) stayed in English — expected, since the widget translates DOM text nodes, not image pixels. No live DOM text was left silently untranslated on this page.
- **Cache on re-translate:** Restored the page, translated again — **217 chunks, 215 cache hits (99%), 2,035 ms total**, versus **212 chunks, 69 hits, 199,564 ms** on the first (cold) pass. That's roughly a **98× speedup** on the warm run — the cache is doing real, dramatic work.
- **Resilience:** On this same site's 91-result "cordless drill" search-listing page (653 text chunks), a single `Translate page` click issued one giant batch call that never returned — status eventually flipped to "Can't reach backend," even though `curl` confirmed the gateway/AI service were healthy throughout. This points to the single-request-per-batch design timing out on very content-heavy pages (Fly's edge proxy and/or the browser's own fetch have finite request timeouts). No console/CSP errors were observed blocking injection on either page. No layout breakage on the page that did complete.
- **Screenshots:** Not attached to this file; captured live via the in-app browser tool during the session (translated product page, and the widget panel showing "217 chunks · 215 cache hits · 2035 ms"). Attach your own screen-recording frames to the video submission.

> **Note on test method:** This test used the console-loader injection mechanism (via script injection) rather than the packaged Chrome extension, because `Claude in Chrome` wasn't connected in this session to drive a real Chrome profile with the unpacked extension loaded. It worked without any CSP block in this instance. The assignment recommends the extension as the more CSP-robust path for strict sites — re-verify with the actual extension loaded in real Chrome before final submission, since some sites that permit console injection in one context may behave differently under the extension's content-script injection or vice versa.

### Sample translations (8)

| Original (EN) | Translation (es-MX) | Numbers/prices/codes kept? | OK? |
|---|---|---|---|
| #1 Home Improvement Retailer | #1 Minorista de Mejoras para el Hogar | ✅ (#1) | ✅ |
| Model # DCD794D1 | Modelo #DCD794D1 | ✅ | ✅ |
| Atomic 20V Lithium-Ion Cordless Compact 1/2 in. Drill/Driver Kit with 2.0Ah Battery and Charger | Atómica de 20V de iones de litio, taladro/destornillador compacto inalámbrico de 1/2 pulg. con batería de 2.0Ah y cargador | ✅ (20V, 1/2, 2.0Ah) | ✅ |
| $99.00 ... $189.00 ... Save $90.00 (48%) | $99.00 ... $189.00 ... Guardar $90.00 (48%) | ✅ all figures | ✅ |
| Lightweight 2.75 lbs. and Compact at 5.88in Front to Back Design | Ligera de 2.75 lbs. y compacta con un diseño de 5.88 in de frente a atrás | ✅ (2.75, 5.88) | ✅ |
| 140 in stock | 140 en existencia (rendered as "140en existencia" — missing space) | ✅ (140) | ⚠️ cosmetic |
| Free & Easy Returns In Store or Online | Devoluciones gratis y sin complicaciones en tienda o en línea | — | ✅ |
| How doers get more done™ | Cómo los hacedores logran más™ | ✅ (™) | ⚠️ slightly literal ("hacedores" is grammatical but uncommon in natural es-MX; a native copywriter would likely phrase the tagline differently) |

## 3. Dimension scorecard

| Dimension | Pass / Partial / Fail | Evidence |
|---|---|---|
| Translation accuracy | Pass | 8/8 sample pairs above are correct and readable; 212-chunk real page translated coherently |
| Mexican-Spanish register (es-MX) | Partial | Mostly natural ("Guardar", "en existencia", "Tienda"); one tagline ("hacedores") reads slightly calque-y |
| Numbers / prices / codes preserved | Pass | Model # DCD794D1, SKU, $99.00/$189.00/48%, 20V/2.0Ah/1/2in/2.75lbs/5.88in all preserved across every sample |
| Page coverage | Pass | All live DOM text translated on the product page; only raster-image text (expected) stayed English |
| Cache effectiveness | Pass | 99% hit rate and 98× speedup (199,564 ms → 2,035 ms) on real-site re-translate; SQLite persists across restarts (verified separately) |
| Latency vs SLA | Pass (local gate) | `bench.py` exits 0, all 5 SLA targets met on two independent fresh-cache runs |
| Error handling (no silent English) | Pass | On the timeout case, status surfaced "Can't reach backend..." rather than silently leaving/mislabeling text as translated |
| Resilience on a real site | Partial | Product page: clean, no errors. 91-result listing page (653 chunks): single batch call timed out — a real scaling gap on very large pages |
| UX polish | Partial | Minor missing-whitespace artifacts where translated fragments are stitched around interpolated dynamic values (e.g. "140en existencia") — a widget-side text-chunking behavior, not something in scope to fix (widget is provided/fixed) |

## 4. Top fixes before shipping

1. **Large-page batch timeout** — the 653-chunk search-listing page never completed; investigate client-side sub-batching (smaller chunk groups per request) or a longer-lived streaming/polling pattern so very content-heavy pages degrade gracefully instead of hanging.
2. **Re-verify with the real Chrome extension** — this test used console-injection since `Claude in Chrome` wasn't available; confirm the packaged extension behaves the same on both a product page and a large listing page before recording the final demo.
3. **Tagline/idiom polish** — "How doers get more done™" → "Cómo los hacedores logran más™" is technically correct but a little stiff; consider whether the prompt should nudge toward more idiomatic marketing copy for taglines specifically.
