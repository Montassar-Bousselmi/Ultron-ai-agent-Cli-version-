from __future__ import annotations

import re
import unicodedata

from .config import TOP_K
from .ingest import ingest_all, load_index


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text.lower()


def keywords(text: str) -> list[str]:
    # Ignore very common words so the search focuses on meaningful terms.
    stop_words = {
        "le", "la", "les", "un", "une", "des", "de", "du", "dans", "pour", "sur",
        "avec", "est", "sont", "que", "qui", "quoi", "comment", "et", "ou", "a", "au",
        "aux", "en", "the", "a", "an", "of", "in", "on", "for", "and", "or", "is", "are",
        "to", "what", "how", "about", "je", "tu", "il", "elle", "nous", "vous", "ils", "elles",
    }
    words = re.findall(r"[a-zA-ZÀ-ÿ0-9]{2,}", normalize(text))
    return [word for word in words if word not in stop_words]


def score_record(query_words: list[str], record: dict) -> int:
    if not query_words:
        return 0
    text = normalize(record.get("text", ""))
    title = normalize(record.get("file_name", ""))
    score = 0
    for word in query_words:
        score += text.count(word)
        if word in title:
            score += 5
    return score


def search_documents(query: str, top_k: int = TOP_K) -> str:
    """Simple keyword search over the local document index. No embeddings or vector DB."""
    query = query.strip()
    if not query:
        return "Error: empty document search query."

    records = load_index()
    if not records:
        result = ingest_all()
        records = load_index()
        if not records:
            return (
                "No readable documents were found. Put PDF, DOCX, TXT or MD files in "
                "data/documents/ and run: python -m agent.knowledge.ingest"
            )

    query_words = keywords(query)
    ranked = []
    for record in records:
        score = score_record(query_words, record)
        if score > 0:
            ranked.append((score, record))

    ranked.sort(key=lambda item: item[0], reverse=True)
    ranked = ranked[:max(1, top_k)]

    if not ranked:
        return "No relevant information was found in the indexed documents."

    blocks = []
    for i, (score, record) in enumerate(ranked, start=1):
        page = record.get("page")
        location = f"page {page}" if page else f"chunk {record.get('chunk', '?')}"
        blocks.append(
            f"[SOURCE {i}] {record.get('source', 'unknown')} | {location}\n"
            f"{record.get('text', '')}"
        )

    return "\n\n".join(blocks)


# Keep the name used by the agent easy to understand.
def search_knowledge(query: str, top_k: int = TOP_K) -> str:
    return search_documents(query, top_k)


if __name__ == "__main__":
    query = input("Question: ")
    print(search_documents(query))
