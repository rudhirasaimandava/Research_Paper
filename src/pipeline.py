"""
pipeline.py
-----------
High-level orchestrator: PDF -> text -> chunks -> vector index -> retrieval
-> grounded answer. This is the single entry point the UI (app.py) talks to,
so the UI layer stays free of RAG internals.
"""

import os
from typing import Optional

from src.ingestion import PDFIngestor
from src.chunking import Chunker
from src.vectorstore import VectorStore
from src.generator import AnswerGenerator, GeneratedAnswer

# A few canned questions the Streamlit UI offers as quick-click buttons,
# matching the standard "read a paper" checklist.
SUGGESTED_QUESTIONS = [
    "What is the objective of the paper?",
    "What methodology was used?",
    "What datasets were used?",
    "What are the major findings?",
    "What are the limitations?",
]


class RAGPipeline:
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        top_k: int = 5,
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k

        self.ingestor = PDFIngestor()
        self.chunker = Chunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.store = VectorStore(embedding_model=embedding_model)
        self.generator: Optional[AnswerGenerator] = None  # lazy: needs API key present

        self.source_name: Optional[str] = None
        self.num_pages: int = 0
        self.num_chunks: int = 0

    def ingest_pdf(self, pdf_path: str, source_name: str) -> None:
        """Run the full ingestion+indexing pipeline for one PDF."""
        pages = self.ingestor.extract(pdf_path)
        chunks = self.chunker.chunk_pages(pages, source=source_name)
        self.store.build(chunks)

        self.source_name = source_name
        self.num_pages = len(pages)
        self.num_chunks = len(chunks)

    def save_index(self, dir_path: str) -> None:
        self.store.save(dir_path)

    def load_index(self, dir_path: str, source_name: str) -> None:
        self.store.load(dir_path)
        self.source_name = source_name
        self.num_chunks = len(self.store.chunks)

    def answer(self, question: str) -> GeneratedAnswer:
        if not self.store.chunks or self.store.index is None:
            raise ValueError(
                "No document has been ingested yet. Upload and process a PDF before asking a question."
            )
        if self.generator is None:
            self.generator = AnswerGenerator()
        retrieved = self.store.search(question, top_k=self.top_k)
        if not retrieved:
            return GeneratedAnswer(
                answer="The paper does not appear to address this.",
                sources=[],
            )
        return self.generator.generate(question, retrieved)
