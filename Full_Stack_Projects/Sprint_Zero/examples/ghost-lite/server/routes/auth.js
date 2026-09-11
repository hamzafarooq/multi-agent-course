const express = require("express");
const bcrypt = require("bcryptjs");
const crypto = require("crypto");
const { db } = require("../db");
const { signToken, requireAuth } = require("../auth");
const { sendError, bodyOf } = require("../lib/http");
const { nowIso, normalizeEmail, isEmail } = require("../lib/text");
const { serializeUser, serializeSite } = require("../lib/serialize");

const router = express.Router();

const findUserByEmail = db.prepare("SELECT * FROM users WHERE email = ?");
const findUserById = db.prepare("SELECT * FROM users WHERE id = ?");
const findSiteByOwner = db.prepare("SELECT * FROM sites WHERE owner_id = ?");
const insertUser = db.prepare(
  "INSERT INTO users (id, email, password_hash, created_at) VALUES (?, ?, ?, ?)"
);

function sessionResponse(user) {
  return {
    access_token: signToken(user),
    user: serializeUser(user),
    site: serializeSite(findSiteByOwner.get(user.id)),
  };
}

router.post("/signup", async (req, res) => {
  const body = bodyOf(req);
  const email = normalizeEmail(body.email);
  const password = typeof body.password === "string" ? body.password : "";
  if (!isEmail(email) || password.length < 8) {
    return sendError(
      res,
      400,
      "validation_error",
      "Email must be a valid address and password at least 8 characters."
    );
  }
  if (findUserByEmail.get(email)) {
    return sendError(res, 409, "email_taken", "An account with that email already exists.");
  }
  const user = {
    id: crypto.randomUUID(),
    email,
    password_hash: await bcrypt.hash(password, 10),
    created_at: nowIso(),
  };
  insertUser.run(user.id, user.email, user.password_hash, user.created_at);
  res.status(201).json(sessionResponse(user));
});

router.post("/login", async (req, res) => {
  const body = bodyOf(req);
  const email = normalizeEmail(body.email);
  const password = typeof body.password === "string" ? body.password : "";
  if (!email || !password) {
    return sendError(res, 400, "validation_error", "Email and password are required.");
  }
  const user = findUserByEmail.get(email);
  const ok = user ? await bcrypt.compare(password, user.password_hash) : false;
  if (!ok) {
    return sendError(res, 401, "invalid_credentials", "Invalid email or password.");
  }
  res.json(sessionResponse(user));
});

router.get("/me", requireAuth, (req, res) => {
  const user = findUserById.get(req.user.id);
  if (!user) return sendError(res, 401, "unauthorized", "Missing or invalid token.");
  res.json({
    user: serializeUser(user),
    site: serializeSite(findSiteByOwner.get(user.id)),
  });
});

module.exports = router;
