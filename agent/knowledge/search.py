"""Retrieval-Augmented Generation (RAG) search.

Strategy
--------
1. **Vector search** (primary): Embed the query with sentence-transformers,
   query the FAISS index, return the top-K most semantically similar chunks.
2. **Keyword fallback** (automatic): If the FAISS index doesn't exist yet
   (e.g. sentence-transformers/faiss-cpu not installed) the old keyword scorer
   is used transparently so the agent still works out of the box.

The returned string is formatted for direct injection into the LLM context.
"""
from __future__ import annotations

import json
import re
import unicodedata

from .config import FAISS_ID_MAP_FILE, FAISS_INDEX_FILE, TOP_K
from .ingest import ingest_all, load_index


# ---------------------------------------------------------------------------
# Keyword fallback (original implementation — preserved as safety net)
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text.lower()


def _keywords(text: str) -> list[str]:
    stop_words = {
        "le", "la", "les", "un", "une", "des", "de", "du", "dans", "pour", "sur",
        "avec", "est", "sont", "que", "qui", "quoi", "comment", "et", "ou", "a", "au",
        "aux", "en", "the", "a", "an", "of", "in", "on", "for", "and", "or", "is",
        "are", "to", "what", "how", "about", "je", "tu", "il", "elle", "nous", "vous",
        "ils", "elles",
    }
    words = re.findall(r"[a-zA-ZÀ-ÿ0-9]{2,}", _normalize(text))
    return [w for w in words if w not in stop_words]


def _score_record(query_words: list[str], record: dict) -> int:
    if not query_words:
        return 0
    text = _normalize(record.get("text", ""))
    title = _normalize(record.get("file_name", ""))
    score = 0
    for word in query_words:
        score += text.count(word)
        if word in title:
            score += 5
    return score


def _keyword_search(query: str, records: list[dict], top_k: int) -> list[dict]:
    """Return the top-K records ranked by keyword frequency."""
    query_words = _keywords(query)
    ranked = [
        (score, rec)
        for rec in records
        if (score := _score_record(query_words, rec)) > 0
    ]
    ranked.sort(key=lambda x: x[0], reverse=True)
    return [rec for _, rec in ranked[:max(1, top_k)]]


# ---------------------------------------------------------------------------
# Vector search (RAG)
# ---------------------------------------------------------------------------

def _vector_search(query: str, records: list[dict], top_k: int) -> list[dict] | None:
    """
    Return the top-K semantically similar records using FAISS + sentence-transformers.
    Returns None if the vector index is unavailable (triggers keyword fallback).
    """
    if not FAISS_INDEX_FILE.exists() or not FAISS_ID_MAP_FILE.exists():
        return None

    try:
        import faiss  # type: ignore
        import numpy as np
        from .embed import embed_query
    except ImportError:
        return None  # packages not installed → fall back to keywords

    try:
        index = faiss.read_index(str(FAISS_INDEX_FILE))
        id_map: list[int] = json.loads(FAISS_ID_MAP_FILE.read_text(encoding="utf-8"))

        q_vec: np.ndarray = embed_query(query)  # shape (1, dim), normalised
        k = min(top_k, index.ntotal)
        scores, indices = index.search(q_vec, k)

        results: list[dict] = []
        for faiss_idx, score in zip(indices[0], scores[0]):
            if faiss_idx < 0:  # FAISS returns -1 for empty slots
                continue
            record_idx = id_map[faiss_idx]
            rec = dict(records[record_idx])
            rec["_score"] = float(score)   # cosine similarity ∈ [-1, 1]
            results.append(rec)
        return results
    except Exception as exc:
        print(f"[search] Vector search error ({exc}); falling back to keywords.")
        return None


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def _format_results(results: list[dict], method: str) -> str:
    blocks: list[str] = []
    for i, record in enumerate(results, start=1):
        page = record.get("page")
        location = f"page {page}" if page else f"chunk {record.get('chunk', '?')}"
        score_str = (
            f"  [similarity: {record['_score']:.3f}]"
            if "_score" in record
            else ""
        )
        blocks.append(
            f"[SOURCE {i}] {record.get('source', 'unknown')} | {location}{score_str}\n"
            f"{record.get('text', '')}"
        )
    header = f"[RAG — {method} search, {len(results)} result(s)]\n\n"
    return header + "\n\n".join(blocks)


def search_documents(query: str, top_k: int = TOP_K) -> str:
    """
    Semantic RAG search over the local document index.

    Uses FAISS + sentence-transformers when available; falls back to keyword
    search automatically so the agent is never broken during setup.
    """
    query = query.strip()
    if not query:
        return "Error: empty document search query."

    # Ensure the index exists; auto-ingest if needed.
    records = load_index()
    if not records:
        ingest_all()
        records = load_index()
        if not records:
            return (
                "No readable documents were found. "
                "Put PDF, DOCX, TXT or MD files in data/documents/ and run:\n"
                "  python -m agent.knowledge.ingest"
            )

    # 1. Try semantic (vector) search
    results = _vector_search(query, records, top_k)
    if results is not None:
        if not results:
            return "No relevant information was found in the indexed documents."
        return _format_results(results, method="semantic")

    # 2. Keyword fallback
    results = _keyword_search(query, records, top_k)
    if not results:
        return "No relevant information was found in the indexed documents."
    return _format_results(results, method="keyword")


# Alias kept for backwards compatibility
def search_knowledge(query: str, top_k: int = TOP_K) -> str:
    return search_documents(query, top_k)


if __name__ == "__main__":
    query = input("Question: ")
    print(search_documents(query))
