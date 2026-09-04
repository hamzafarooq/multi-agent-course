"""Vercel entrypoint.

Vercel bundles this file as a serverless function and serves the FastAPI app
from it. The real applications live in ../backend and ../search-lab; this only
fixes up the import paths and the document locations, which are relative paths
locally, and mounts the Search Lab at /lab.
"""
import os
import sys

from starlette.responses import RedirectResponse
from starlette.routing import Mount, Route

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))

# Locally these default to paths relative to backend/. In the bundle everything
# sits under the project root, so point at it explicitly.
os.environ.setdefault(
    "RAG_DOCUMENT_PATH",
    os.path.join(ROOT, "Project-Management-2nd-Edition-1729807212.pdf"),
)
os.environ.setdefault("RAG_DATA_DIR", os.path.join(ROOT, "data"))

from main import app  # noqa: E402

# The Search Lab is its own application - its own FastAPI app, its own
# frontend, its own port locally (uvicorn --app-dir search-lab app:app --port
# 8010). It rides in this function rather than a second Vercel project because
# a project's bundle cannot reach above its root and the lab imports the
# module's embeddings provider. One deployment also means one set of API keys
# and one password to hand out.
#
# It is deployable at all because EMBEDDING_PROVIDER defaults to `openai`: the
# offline nomic model pulls in ~525MB of torch, far past the function size
# limit. Locally either provider works.
sys.path.insert(0, os.path.join(ROOT, "search-lab"))
from app import app as lab  # noqa: E402

def _lab_slash(request):
    # The lab's frontend asks for `styles.css` and `api/search` relative to its
    # own URL, so it has to be served from /lab/ rather than /lab. Starlette
    # would normally redirect for us, but only when nothing else matched - and
    # `main`'s catch-all frontend mount matches /lab first.
    return RedirectResponse("/lab/", status_code=308)


# Inserted at the front: `main` mounts its own frontend at "/", and Starlette
# matches routes in order, so an appended mount would never be reached.
app.router.routes.insert(0, Mount("/lab", lab))
app.router.routes.insert(0, Route("/lab", _lab_slash))

__all__ = ["app"]
