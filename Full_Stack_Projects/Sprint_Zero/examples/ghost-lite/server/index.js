const express = require("express");
const cors = require("cors");
const { fts5 } = require("./db");
const { runSeed } = require("./seed");
const { answerMode } = require("./answer");
const { sendError } = require("./lib/http");

const PORT = Number(process.env.PORT) || 3001;
const ALLOWED_ORIGINS = (process.env.CORS_ORIGIN || "http://localhost:5173,http://127.0.0.1:5173")
  .split(",")
  .map((origin) => origin.trim())
  .filter(Boolean);

const app = express();

app.use(
  cors({
    origin: ALLOWED_ORIGINS,
    methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allowedHeaders: ["Authorization", "Content-Type"],
  })
);
app.use(express.json({ limit: "2mb" }));

app.get("/health", (req, res) => {
  res.json({ status: "ok", fts5, answer_mode: answerMode ? "answer" : "search" });
});

app.use("/auth", require("./routes/auth"));
app.use("/me", require("./routes/me"));
app.use("/sites", require("./routes/sites"));

app.use((req, res) => sendError(res, 404, "not_found", "Route not found."));

app.use((err, req, res, next) => {
  if (err && (err.type === "entity.parse.failed" || err instanceof SyntaxError)) {
    return sendError(res, 400, "validation_error", "Request body must be valid JSON.");
  }
  console.error(err);
  sendError(res, 500, "internal_error", "Something went wrong.");
});

try {
  runSeed();
} catch (err) {
  console.error("Seed skipped:", err.message);
}

app.listen(PORT, () => {
  console.log(`Inkwell API listening on http://localhost:${PORT}`);
  console.log(`Ask me: fts5=${fts5} answer_mode=${answerMode ? "answer" : "search"}`);
});
