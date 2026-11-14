/*
 * FDE · Assignment 1 · Extension content bootstrap  (PROVIDED)
 * -----------------------------------------------------------
 * Runs BEFORE translation-widget.js (see manifest content_scripts order).
 * Two jobs:
 *   1. Read the saved backend URL from chrome.storage and expose it as
 *      window.FDE_CONFIG so the widget picks it up on load.
 *   2. Relay popup commands (translate page / restore / open) to the widget
 *      via window events.
 */
(function () {
  try {
    chrome.storage.sync.get({ apiUrl: "http://localhost:8787" }, (cfg) => {
      window.FDE_CONFIG = Object.assign({}, window.FDE_CONFIG, { API_URL: cfg.apiUrl });
    });
  } catch (_) {
    /* storage not available; widget falls back to its default */
  }

  chrome.runtime.onMessage.addListener((msg) => {
    if (!msg || !msg.type) return;
    if (msg.type === "TRANSLATE_PAGE") window.dispatchEvent(new Event("FDE_TRANSLATE_PAGE"));
    if (msg.type === "RESTORE_PAGE") window.dispatchEvent(new Event("FDE_RESTORE_PAGE"));
    if (msg.type === "OPEN") window.dispatchEvent(new Event("FDE_OPEN"));
  });
})();
