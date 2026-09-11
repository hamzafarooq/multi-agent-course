function sendError(res, status, error, message) {
  return res.status(status).json({ error, message });
}

function bodyOf(req) {
  return req.body && typeof req.body === "object" ? req.body : {};
}

module.exports = { sendError, bodyOf };
