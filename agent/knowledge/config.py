from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DOCUMENTS_DIR = BASE_DIR / "data" / "documents"
INDEX_DIR = BASE_DIR / "data" / "index"
INDEX_FILE = INDEX_DIR / "documents.json"

# ---------- RAG / vector-search settings ----------
# FAISS flat index stored alongside the JSON index.
FAISS_INDEX_FILE = INDEX_DIR / "vectors.faiss"
# Mapping from FAISS row → record position in documents.json
FAISS_ID_MAP_FILE = INDEX_DIR / "id_map.json"

# sentence-transformers model used to embed chunks and queries.
# A lightweight but strong multilingual model; swap to
# "BAAI/bge-large-en-v1.5" or "intfloat/e5-large-v2" for higher accuracy.
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ---------- chunking / retrieval ----------
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150
TOP_K = 5

DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
INDEX_DIR.mkdir(parents=True, exist_ok=True)
