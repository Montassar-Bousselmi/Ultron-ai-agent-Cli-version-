"""Document ingestion pipeline.

1.  Reads PDF / DOCX / TXT / MD files from data/documents/.
2.  Splits them into overlapping text chunks.
3.  Persists the chunks to data/index/documents.json  (keyword fallback).
4.  Embeds every chunk with sentence-transformers and writes a FAISS flat-IP
    index to data/index/vectors.faiss plus an id_map.json that maps FAISS
    row numbers back to chunk records.
"""
from __future__ import annotations

import json
from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader

from .config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DOCUMENTS_DIR,
    FAISS_ID_MAP_FILE,
    FAISS_INDEX_FILE,
    INDEX_FILE,
    SUPPORTED_EXTENSIONS,
)


# ---------------------------------------------------------------------------
# Text extraction helpers
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    return " ".join(text.replace("\x00", " ").split())


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    text = clean_text(text)
    if not text:
        return []
    if overlap >= size:
        raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = end - overlap
    return chunks


def extract_document(path: Path) -> list[tuple[str, int | None]]:
    """Return [(text, page_number)].  PDF pages are 1-based; others use None."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(str(path))
        return [(page.extract_text() or "", i + 1) for i, page in enumerate(reader.pages)]
    if suffix == ".docx":
        doc = DocxDocument(str(path))
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        return [(text, None)]
    if suffix in {".txt", ".md"}:
        return [(path.read_text(encoding="utf-8", errors="ignore"), None)]
    raise ValueError(f"Unsupported file type: {suffix}")


# ---------------------------------------------------------------------------
# Per-file ingestion
# ---------------------------------------------------------------------------

def ingest_file(path: Path) -> list[dict]:
    path = path.resolve()
    source_root = DOCUMENTS_DIR.resolve()
    source = (
        str(path.relative_to(source_root))
        if path.is_relative_to(source_root)
        else str(path)
    )
    chunks: list[dict] = []
    chunk_number = 0
    for page_text, page_number in extract_document(path):
        for chunk in chunk_text(page_text):
            chunks.append(
                {
                    "source": source,
                    "file_name": path.name,
                    "file_type": path.suffix.lower().lstrip("."),
                    "page": page_number,
                    "chunk": chunk_number,
                    "text": chunk,
                }
            )
            chunk_number += 1
    return chunks


# ---------------------------------------------------------------------------
# Full ingestion (JSON + FAISS)
# ---------------------------------------------------------------------------

def _build_faiss_index(records: list[dict]) -> None:
    """Embed all chunk texts and write vectors.faiss + id_map.json."""
    try:
        import faiss  # type: ignore
        import numpy as np
        from .embed import embed_texts
    except ImportError as exc:
        print(
            f"[ingest] WARNING: skipping FAISS index — missing package: {exc}\n"
            "         Run: pip install sentence-transformers faiss-cpu"
        )
        return

    texts = [r["text"] for r in records]
    if not texts:
        return

    print(f"[ingest] Embedding {len(texts)} chunks with sentence-transformers …")
    vecs: np.ndarray = embed_texts(texts)      # shape (N, dim), L2-normalised
    dim = vecs.shape[1]

    # IndexFlatIP with normalised vectors == cosine similarity search
    index = faiss.IndexFlatIP(dim)
    index.add(vecs)

    faiss.write_index(index, str(FAISS_INDEX_FILE))

    # Store the ordered list of record indices so we can retrieve metadata
    id_map = list(range(len(records)))
    FAISS_ID_MAP_FILE.write_text(
        json.dumps(id_map, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[ingest] FAISS index saved → {FAISS_INDEX_FILE}  ({dim}-dim, {len(texts)} vectors)")


def ingest_all() -> dict:
    """Read all supported files, persist JSON index, and build FAISS index."""
    records: list[dict] = []
    files: list[dict] = []

    for path in sorted(DOCUMENTS_DIR.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        try:
            file_records = ingest_file(path)
            records.extend(file_records)
            files.append(
                {"file": str(path.relative_to(DOCUMENTS_DIR)), "chunks": len(file_records)}
            )
        except Exception as exc:
            files.append(
                {"file": str(path.relative_to(DOCUMENTS_DIR)), "chunks": 0, "error": str(exc)}
            )

    # Always persist the JSON index (keyword-search fallback)
    payload = {"version": 2, "records": records}
    INDEX_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # Try to build the vector index
    _build_faiss_index(records)

    return {"files": files, "total_chunks": len(records)}


# ---------------------------------------------------------------------------
# Load helpers (used by search.py)
# ---------------------------------------------------------------------------

def load_index() -> list[dict]:
    if not INDEX_FILE.exists():
        return []
    try:
        payload = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
        return payload.get("records", [])
    except (json.JSONDecodeError, OSError):
        return []


if __name__ == "__main__":
    result = ingest_all()
    print(f"\nIndexed {result['total_chunks']} text chunks.")
    for item in result["files"]:
        if "error" in item:
            print(f"  - {item['file']}: ERROR — {item['error']}")
        else:
            print(f"  - {item['file']}: {item['chunks']} chunks")
    print(f"\nJSON index → {INDEX_FILE}")
    print(f"FAISS index → {FAISS_INDEX_FILE}")
