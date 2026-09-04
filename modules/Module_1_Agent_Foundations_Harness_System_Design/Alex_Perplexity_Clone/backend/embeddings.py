"""
Embedding providers.

Two of them, deliberately:

  openai  text-embedding-3-small over the API. Nothing to install beyond the
          `openai` client, so the deployed function stays small - no torch, no
          model weights. This is what production uses.

  local   nomic-embed-text-v1.5 through sentence-transformers. No API key and
          no network, which is useful for building an index offline or working
          on a plane, but it drags in ~525MB of torch and cannot be deployed.

Both produce plain lists of floats, so the rest of the system does not know or
care which one built the index. `EMBEDDING_PROVIDER` picks; `openai` is default.
"""
import os

# Read lazily, never at import time: callers load their .env after importing
# this module, so a module-level constant would capture the wrong value and
# silently fall back to the default provider.
def provider() -> str:
    return os.environ.get("EMBEDDING_PROVIDER", "openai").lower()


def openai_model() -> str:
    return os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")


def local_model() -> str:
    return os.environ.get("LOCAL_EMBEDDING_MODEL", "nomic-ai/nomic-embed-text-v1.5")

# nomic is trained with task prefixes and quietly loses accuracy without them.
# OpenAI's models take raw text, so these are only applied for the local model.
LOCAL_DOC_PREFIX = "search_document: "
LOCAL_QUERY_PREFIX = "search_query: "

_local_model = None
_openai_client = None


def model_name() -> str:
    return openai_model() if provider() == "openai" else local_model()


def _openai():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI

        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Either set it, or build and run with "
                "EMBEDDING_PROVIDER=local to use the offline model instead."
            )
        _openai_client = OpenAI(api_key=key)
    return _openai_client


def _local():
    global _local_model
    if _local_model is None:
        from sentence_transformers import SentenceTransformer

        _local_model = SentenceTransformer(local_model(), trust_remote_code=True)
    return _local_model


def embed_documents(texts: list[str], batch_size: int = 128) -> list[list[float]]:
    """Embed passages for storage. Called offline by build_index.py."""
    if not texts:
        return []

    if provider() == "openai":
        client = _openai()
        out: list[list[float]] = []
        # The API caps how much can go in one request, so batch.
        for i in range(0, len(texts), batch_size):
            chunk = texts[i : i + batch_size]
            response = client.embeddings.create(model=openai_model(), input=chunk)
            out.extend(item.embedding for item in response.data)
        return out

    model = _local()
    vectors = model.encode([LOCAL_DOC_PREFIX + t for t in texts], batch_size=32)
    return [v.tolist() for v in vectors]


def embed_query(text: str) -> list[float]:
    """Embed one question. This is the only embedding work done at request time."""
    if provider() == "openai":
        response = _openai().embeddings.create(model=openai_model(), input=[text])
        return response.data[0].embedding

    return _local().encode([LOCAL_QUERY_PREFIX + text])[0].tolist()
