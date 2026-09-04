"""
Password gate.

Vercel's own password protection needs a paid plan, and these apps are deployed
with live API keys behind them: an open URL means anyone can spend the owner's
credits. When APP_PASSWORD is set, every /api/ call needs a signed cookie that
only the password can mint. Unset - the default, so local runs are unchanged -
the gate is disabled entirely.

Shared by the assistant and the Search Lab so there is one implementation of
the check, and so one login covers both: same cookie, same signature.
"""
import hashlib
import hmac
import os

from fastapi.responses import JSONResponse
from pydantic import BaseModel

COOKIE = "alex_access"


def password() -> str:
    # Read lazily: the entrypoint loads .env after importing this module.
    return os.environ.get("APP_PASSWORD", "")


def _token() -> str:
    # Signed rather than storing the password in the cookie, so a leaked cookie
    # does not reveal the password itself.
    secret = password()
    if not secret:
        return ""
    return hmac.new(secret.encode(), b"alex-access-v1", hashlib.sha256).hexdigest()


class LoginRequest(BaseModel):
    password: str


def _api_path(request) -> str:
    """The path as the app itself sees it.

    The Search Lab is mounted under /lab in the deployed bundle and served at /
    locally, so match on the /api/ segment rather than on a fixed prefix.
    """
    return request.scope.get("path", "") or request.url.path


def install(app) -> None:
    @app.get("/api/gate")
    def gate():
        """Whether a password is required at all."""
        return {"required": bool(password())}

    @app.post("/api/login")
    def login(req: LoginRequest):
        secret = password()
        if not secret:
            return JSONResponse({"ok": True})
        if not hmac.compare_digest(req.password.strip(), secret):
            return JSONResponse(
                {"ok": False, "error": "Incorrect password."}, status_code=401
            )

        response = JSONResponse({"ok": True})
        response.set_cookie(
            COOKIE,
            _token(),
            path="/",
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=60 * 60 * 12,
        )
        return response

    @app.middleware("http")
    async def require_password(request, call_next):
        path = _api_path(request)
        public = path.endswith("/api/login") or path.endswith("/api/gate")
        if (
            password()
            and "/api/" in path
            and not public
            and not hmac.compare_digest(request.cookies.get(COOKIE, ""), _token())
        ):
            return JSONResponse({"error": "password required"}, status_code=401)
        return await call_next(request)
