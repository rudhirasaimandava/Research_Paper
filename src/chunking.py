"""
chunking.py
-----------
Splits page-level text into overlapping chunks suitable for embedding.

VIVA NOTE — why chunk at all?
    LLMs and embedding models have a limited context window, and retrieval
    is more precise when it can point to a small, semantically coherent
    passage rather than an entire paper. Smaller chunks -> higher precision
    but risk losing context; larger chunks -> more context but noisier
    retrieval and higher token cost. We use a recursive splitter that tries
    to break on paragraph/sentence boundaries first, only falling back to
    hard character cuts when necessary, to keep chunks semantically clean.

VIVA NOTE — why overlap?
    Without overlap, a sentence that starts at the end of chunk N and
    finishes at the start of chunk N+1 gets split in half, and neither
    chunk alone contains the full idea. Overlap (commonly 10-20% of chunk
    size) repeats a small window of text between consecutive chunks so
    that ideas near chunk boundaries are still retrievable intact.
"""

from dataclasses import dataclass
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.ingestion import PageText


@dataclass
class Chunk:
    chunk_id: str
    text: str
    page_number: int
    source: str


class Chunker:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def chunk_pages(self, pages: List[PageText], source: str) -> List[Chunk]:
        chunks: List[Chunk] = []
        counter = 0
        for page in pages:
            pieces = self.splitter.split_text(page.text)
            for piece in pieces:
                counter += 1
                chunks.append(
                    Chunk(
                        chunk_id=f"{source}-p{page.page_number}-c{counter}",
                        text=piece,
                        page_number=page.page_number,
                        source=source,
                    )
                )
        return chunks
