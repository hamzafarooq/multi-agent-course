"""Optional: rebuild the embedding index from the committed enriched chunks.

The repo already ships `data/embeddings/`, so the app runs without this. Use it only
if you change the chunking or add episodes. It re-embeds chunk text + HyDE questions
with OpenAI (no Whisper, no LLM enrichment) — a few cents.

    python build_index.py
"""
from src.config import EMBED_DIR
from src.embed import build_chunk_embeddings, build_question_embeddings


def main():
    for f in ("chunks.npz", "chunks_index.json", "questions.npz"):
        p = EMBED_DIR / f
        if p.exists():
            p.unlink()
            print(f"[clean] removed {f}")
    vecs, chunks = build_chunk_embeddings(force=True)
    build_question_embeddings(chunks, force=True)
    print(f"Rebuilt index: {len(chunks)} chunks.")


if __name__ == "__main__":
    main()
