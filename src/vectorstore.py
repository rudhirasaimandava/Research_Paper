"""
vectorstore.py
--------------
Embeds chunks and stores them in a FAISS index for semantic retrieval.

VIVA NOTE — why semantic (vector) search instead of keyword search?
    Keyword search (e.g. TF-IDF, BM25) matches literal words. A question
    like "What data was used to train the model?" would miss a paper that
    says "the corpus consisted of..." because there's no literal overlap.
    Embedding both the question and the chunks into the same vector space
    lets us match on *meaning* via cosine/L2 similarity, so paraphrases and
    synonyms are still retrieved correctly.

We use a local, free Sentence-Transformers model (all-MiniLM-L6-v2) for
embeddings -- no API key or network dependency required for this stage,
which keeps the retrieval pipeline fast and reproducible.
"""

import os
import pickle
import re
import hashlib
from dataclasses import asdict
from typing import List, Tuple

import faiss
import numpy as np

from src.chunking import Chunk


class HashEmbeddingModel:
    """Small dependency-free embedding fallback for restricted environments."""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def encode(self, texts, **_kwargs):
        vectors = np.zeros((len(texts), self.dimension), dtype=np.float32)
        for row, text in enumerate(texts):
            tokens = re.findall(r"\b\w+\b", text.lower())
            for token in tokens:
                digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
                index = int.from_bytes(digest[:4], "little") % self.dimension
                sign = 1.0 if digest[4] % 2 else -1.0
                vectors[row, index] += sign
        return vectors


class VectorStore:
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2"):
        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(embedding_model)
            self.embedding_backend = "sentence-transformers"
        except (ImportError, OSError) as error:
            self.model = HashEmbeddingModel()
            self.embedding_backend = "hash-fallback"
            self.embedding_error = str(error)
        self.index: faiss.Index | None = None
        self.chunks: List[Chunk] = []

    def build(self, chunks: List[Chunk]) -> None:
        """Embed all chunks and build a fresh FAISS index (cosine similarity
        via L2-normalized inner product)."""
        self.chunks = chunks
        if not chunks:
            self.index = None
            return

        texts = [c.text for c in chunks]
        embeddings = self.model.encode(
            texts, show_progress_bar=False, convert_to_numpy=True
        )
        faiss.normalize_L2(embeddings)
        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)  # inner product == cosine sim (normalized)
        self.index.add(embeddings)

    def search(self, query: str, top_k: int = 5) -> List[Tuple[Chunk, float]]:
        """Return the top_k most semantically similar chunks to the query,
        each paired with its similarity score."""
        if self.index is None or not self.chunks:
            return []
        query_vec = self.model.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(query_vec)
        scores, indices = self.index.search(query_vec, top_k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            results.append((self.chunks[idx], float(score)))
        return results

    # ------------------------------------------------------------------
    # Persistence: save/load so a processed paper doesn't need re-embedding
    # every time the app restarts.
    # ------------------------------------------------------------------
    def save(self, dir_path: str) -> None:
        os.makedirs(dir_path, exist_ok=True)
        faiss.write_index(self.index, os.path.join(dir_path, "index.faiss"))
        with open(os.path.join(dir_path, "chunks.pkl"), "wb") as f:
            pickle.dump([asdict(c) for c in self.chunks], f)

    def load(self, dir_path: str) -> None:
        self.index = faiss.read_index(os.path.join(dir_path, "index.faiss"))
        with open(os.path.join(dir_path, "chunks.pkl"), "rb") as f:
            raw = pickle.load(f)
        self.chunks = [Chunk(**c) for c in raw]
