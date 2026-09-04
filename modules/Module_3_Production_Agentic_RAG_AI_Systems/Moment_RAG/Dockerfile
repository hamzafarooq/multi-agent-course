FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    FASTEMBED_CACHE_PATH=/opt/fastembed_cache

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

# Pre-download the fastembed models (BM25 sparse + cross-encoder reranker) at
# build time so the first query doesn't pay a ~1 min cold download.
RUN python - <<'PY'
from fastembed import SparseTextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder
SparseTextEmbedding("Qdrant/bm25")
TextCrossEncoder(model_name="jinaai/jina-reranker-v1-tiny-en")
print("fastembed models cached")
PY

COPY . .

EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
