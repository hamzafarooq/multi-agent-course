"""
Turning documents into chunks.

Only ever runs offline, from build_index.py, which is why pypdf lives here and
not in the request path. The deployed function loads the finished index and
never sees a PDF.
"""
import os
import pathlib
import re

CHUNK_SIZE = 900
CHUNK_OVERLAP = 150


def chunk_pages(pages: list[str], document: str, start_index: int) -> list[dict]:
    """Split each page into overlapping windows, tagged with its document."""
    chunks: list[dict] = []
    idx = start_index
    for page_num, raw in enumerate(pages, start=1):
        text = re.sub(r"\s+", " ", raw).strip()
        if not text:
            continue
        start = 0
        while start < len(text):
            end = start + CHUNK_SIZE
            piece = text[start:end].strip()
            if len(piece) > 40:
                chunks.append(
                    {
                        "chunk_index": idx,
                        "document": document,
                        "page": page_num,
                        "text": piece,
                    }
                )
                idx += 1
            if end >= len(text):
                break
            start = end - CHUNK_OVERLAP
    return chunks


def pdf_pages(path: str) -> list[str]:
    from pypdf import PdfReader

    reader = PdfReader(path)
    return [page.extract_text() or "" for page in reader.pages]


def markdown_sections(path: str) -> list[str]:
    """Markdown has no pages, so split on headings to keep a useful locator."""
    raw = pathlib.Path(path).read_text(encoding="utf-8", errors="replace")
    # Drop the human-facing disclaimer blockquote: it is identical in every
    # sample document, so indexing it makes all their headers look alike.
    raw = "\n".join(
        line for line in raw.splitlines() if not line.lstrip().startswith(">")
    )
    return [s for s in re.split(r"\n(?=##\s)", raw) if s.strip()]


def title_for(path: str) -> str:
    """Prefer the document's own H1 over its filename."""
    try:
        for line in (
            pathlib.Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
        ):
            if line.startswith("# "):
                return line[2:].strip()
    except Exception:
        pass
    return pathlib.Path(path).stem.replace("-", " ").replace("_", " ").title()


def load_corpus(document_path: str, data_dir: str | None) -> list[dict]:
    """Every chunk of every document, in a stable order."""
    sources: list[tuple[str, list[str]]] = []

    if document_path and os.path.exists(document_path):
        sources.append(("Project Management (2nd Edition)", pdf_pages(document_path)))

    if data_dir and os.path.isdir(data_dir):
        for path in sorted(pathlib.Path(data_dir).glob("*")):
            if path.suffix.lower() not in {".md", ".txt", ".markdown"}:
                continue
            sources.append((title_for(str(path)), markdown_sections(str(path))))

    chunks: list[dict] = []
    for title, pages in sources:
        chunks.extend(chunk_pages(pages, title, len(chunks)))
    return chunks
