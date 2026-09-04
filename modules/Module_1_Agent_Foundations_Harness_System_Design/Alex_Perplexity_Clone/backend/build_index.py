"""
Build the retrieval index, offline, once.

Reads the PDF and every markdown file in data/, chunks them, embeds every
chunk, and writes the result to index/. Splitting this out is the point: the
deployed app then never parses a PDF, never loads a model, and starts
instantly. It only has to embed the incoming question.

index/ is gitignored - 12MB of vectors that change whenever the documents do -
so a fresh clone has to run this once before the app has anything to retrieve
from. Vercel gets it from the local directory at deploy time.

    python backend/build_index.py                      # OpenAI, needs a key
    EMBEDDING_PROVIDER=local python backend/build_index.py   # offline, no key

Re-run it whenever the documents change.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

import embeddings
from chunking import load_corpus

load_dotenv()

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX_DIR = os.environ.get("RAG_INDEX_DIR", os.path.join(HERE, "..", "index"))


def main() -> int:
    # Relative paths in .env are written relative to backend/, so resolve them
    # against HERE rather than the working directory the script was run from.
    def resolve(value: str) -> str:
        return value if os.path.isabs(value) else os.path.normpath(os.path.join(HERE, value))

    doc_path = resolve(
        os.environ.get(
            "RAG_DOCUMENT_PATH", "../Project-Management-2nd-Edition-1729807212.pdf"
        )
    )
    data_dir = resolve(os.environ.get("RAG_DATA_DIR", "../data"))

    print(f"provider : {embeddings.provider()} ({embeddings.model_name()})")
    print(f"pdf      : {doc_path}")
    print(f"data dir : {data_dir}")

    chunks = load_corpus(doc_path, data_dir)
    if not chunks:
        print("no documents found", file=sys.stderr)
        return 1

    documents = []
    for c in chunks:
        if c["document"] not in documents:
            documents.append(c["document"])

    print(f"\n{len(chunks)} chunks across {len(documents)} documents:")
    for d in documents:
        print("  %5d  %s" % (sum(1 for c in chunks if c["document"] == d), d))

    print(f"\nembedding {len(chunks)} chunks...")
    started = time.time()
    vectors = embeddings.embed_documents([c["text"] for c in chunks])
    elapsed = time.time() - started
    print(f"done in {elapsed:.1f}s ({len(vectors[0])} dimensions)")

    os.makedirs(INDEX_DIR, exist_ok=True)

    # Vectors go in their own file, rounded: full float64 repr triples the file
    # size for precision that cosine similarity cannot notice.
    with open(os.path.join(INDEX_DIR, "vectors.json"), "w") as f:
        json.dump([[round(v, 6) for v in vec] for vec in vectors], f)

    with open(os.path.join(INDEX_DIR, "chunks.json"), "w") as f:
        json.dump(
            {
                "provider": embeddings.provider(),
                "model": embeddings.model_name(),
                "dimensions": len(vectors[0]),
                "documents": documents,
                "chunks": chunks,
            },
            f,
        )

    size = sum(
        os.path.getsize(os.path.join(INDEX_DIR, n))
        for n in ("vectors.json", "chunks.json")
    )
    print(f"wrote {INDEX_DIR} ({size / 1e6:.1f} MB)")
    print("\nCommit index/ so the deployed app does not have to rebuild it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
