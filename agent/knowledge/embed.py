"""Embedding helper — thin wrapper around sentence-transformers.

Lazy-loads the model on first call so import is instant even if the model
has not been downloaded yet.  All public functions return plain numpy arrays
so the rest of the codebase never imports sentence-transformers directly.
"""
from __future__ import annotations

import numpy as np

from .config import EMBEDDING_MODEL

_model = None  # loaded once, reused forever within the process


def _get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers is not installed.  "
                "Run:  pip install sentence-transformers faiss-cpu"
            ) from exc
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    """Return a float32 array of shape (N, dim) — L2-normalised embeddings."""
    model = _get_model()
    vecs = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    vecs = vecs.astype("float32")
    # Normalise so dot-product == cosine similarity
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    return vecs / norms


def embed_query(query: str) -> np.ndarray:
    """Return a float32 array of shape (1, dim) for a single query string."""
    return embed_texts([query])

