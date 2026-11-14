"""Self-contained sparse retrieval for hotel policies and amenities."""

from __future__ import annotations

import re
import sqlite3
import unicodedata
from pathlib import Path


KNOWLEDGE_ROOT = Path(__file__).resolve().parent.parent / "knowledge"

_STOP_WORDS = {
    "a", "about", "and", "are", "can", "do", "does", "for", "hotel", "i", "in",
    "is", "me", "of", "policy", "tell", "the", "to", "what", "your",
    "cual", "cuál", "de", "del", "el", "es", "la", "las", "los", "me", "politica",
    "política", "que", "qué", "sobre", "una", "y",
}

_QUERY_EXPANSIONS = {
    "cancelacion": ["cancellation", "cancelled"],
    "desayuno": ["breakfast"],
    "estacionamiento": ["parking"],
    "mascota": ["pets", "dogs"],
    "mascotas": ["pets", "dogs"],
    "perro": ["pets", "dogs"],
    "perros": ["pets", "dogs"],
    "accesibilidad": ["accessibility", "accessible"],
}


def _normalized(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.lower())
    return "".join(character for character in decomposed if not unicodedata.combining(character))


def _chunks_from_markdown(path: Path) -> list[dict]:
    chunks: list[dict] = []
    title = path.stem.replace("_", " ").title()
    heading = title
    body: list[str] = []

    def flush() -> None:
        text = " ".join(line.strip() for line in body if line.strip()).strip()
        if text:
            chunks.append({
                "source": path.name,
                "section": heading,
                "text": text,
            })

    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            flush()
            body = []
            heading = line[3:].strip()
        elif not line.startswith("# "):
            body.append(line)
    flush()
    return chunks


class KnowledgeBase:
    """Index Markdown chunks with SQLite FTS5 and a lexical fallback."""

    def __init__(self, root: Path = KNOWLEDGE_ROOT):
        self.chunks: list[dict] = []
        for path in sorted(root.glob("*.md")):
            self.chunks.extend(_chunks_from_markdown(path))
        self.connection: sqlite3.Connection | None = None
        try:
            self.connection = sqlite3.connect(":memory:", check_same_thread=False)
            self.connection.execute(
                "CREATE VIRTUAL TABLE knowledge USING fts5(source, section, text)"
            )
            self.connection.executemany(
                "INSERT INTO knowledge(source, section, text) VALUES (?, ?, ?)",
                [(c["source"], c["section"], c["text"]) for c in self.chunks],
            )
        except sqlite3.OperationalError:
            self.connection = None

    def search(self, query: str, limit: int = 3) -> list[dict]:
        original_tokens = re.findall(r"[a-zA-Z0-9áéíóúüñ]+", query.lower())
        tokens = []
        for token in original_tokens:
            if token in _STOP_WORDS:
                continue
            normalized = _normalized(token)
            tokens.append(normalized)
            tokens.extend(_QUERY_EXPANSIONS.get(normalized, []))
        tokens = list(dict.fromkeys(tokens))
        if not tokens:
            return []
        if self.connection is not None:
            fts_query = " OR ".join(f'"{token}"' for token in tokens)
            try:
                rows = self.connection.execute(
                    "SELECT source, section, text, bm25(knowledge) AS score "
                    "FROM knowledge WHERE knowledge MATCH ? ORDER BY score LIMIT ?",
                    (fts_query, limit),
                ).fetchall()
                if rows:
                    return [
                        {"source": row[0], "section": row[1], "text": row[2], "score": row[3]}
                        for row in rows
                    ]
            except sqlite3.OperationalError:
                pass

        scored = []
        for chunk in self.chunks:
            haystack = f"{chunk['section']} {chunk['text']}".lower()
            score = sum(haystack.count(token) for token in tokens)
            if score:
                scored.append((score, chunk))
        ranked = sorted(scored, key=lambda item: item[0], reverse=True)
        return [dict(chunk, score=-score) for score, chunk in ranked[:limit]]


KNOWLEDGE_BASE = KnowledgeBase()


def search_hotel_knowledge(query: str, limit: int = 3) -> dict:
    matches = KNOWLEDGE_BASE.search(query, limit=limit)
    if not matches:
        return {
            "result": "No grounded hotel policy was found. Offer a transfer to the front desk.",
            "sources": [],
        }
    passages = [
        f"[{match['section']}] {match['text']}"
        for match in matches
    ]
    sources = [f"{match['source']}#{match['section']}" for match in matches]
    return {
        "result": "Grounded hotel knowledge:\n" + "\n".join(passages),
        "sources": sources,
    }
