const jwt = require("jsonwebtoken");
const { sendError } = require("./lib/http");

const JWT_SECRET = process.env.JWT_SECRET || "sprint-zero-dev-secret";

function signToken(user) {
  return jwt.sign({ sub: user.id, email: user.email }, JWT_SECRET, {
    algorithm: "HS256",
    expiresIn: "7d",
  });
}

function requireAuth(req, res, next) {
  const header = req.headers.authorization || "";
  const token = header.startsWith("Bearer ") ? header.slice(7).trim() : "";
  if (!token) return sendError(res, 401, "unauthorized", "Missing or invalid token.");
  try {
    const payload = jwt.verify(token, JWT_SECRET, { algorithms: ["HS256"] });
    req.user = { id: payload.sub, email: payload.email };
    next();
  } catch (err) {
    return sendError(res, 401, "unauthorized", "Missing or invalid token.");
  }
}

module.exports = { signToken, requireAuth };
