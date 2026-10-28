from __future__ import annotations

import json
from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader

from .config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DOCUMENTS_DIR,
    INDEX_FILE,
    SUPPORTED_EXTENSIONS,
)


def clean_text(text: str) -> str:
    return " ".join(text.replace("\x00", " ").split())


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    text = clean_text(text)
    if not text:
        return []
    if overlap >= size:
        raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")

    chunks = []
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
    """Return (text, page_number). PDF pages are 1-based; other formats use None."""
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


def ingest_file(path: Path) -> list[dict]:
    path = path.resolve()
    source_root = DOCUMENTS_DIR.resolve()
    source = str(path.relative_to(source_root)) if path.is_relative_to(source_root) else str(path)

    chunks = []
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


def ingest_all() -> dict:
    """Read all supported files and create a simple JSON search index."""
    records = []
    files = []

    for path in sorted(DOCUMENTS_DIR.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        try:
            file_records = ingest_file(path)
            records.extend(file_records)
            files.append({"file": str(path.relative_to(DOCUMENTS_DIR)), "chunks": len(file_records)})
        except Exception as exc:
            files.append({"file": str(path.relative_to(DOCUMENTS_DIR)), "chunks": 0, "error": str(exc)})

    payload = {"version": 1, "records": records}
    INDEX_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"files": files, "total_chunks": len(records)}


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
    print(f"Indexed {result['total_chunks']} text chunks.")
    for item in result["files"]:
        if "error" in item:
            print(f"- {item['file']}: ERROR - {item['error']}")
        else:
            print(f"- {item['file']}: {item['chunks']} chunks")
    print(f"Index saved to: {INDEX_FILE}")
