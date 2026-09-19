"""
generator.py
------------
Takes retrieved chunks + the user's question and produces a grounded,
cited answer using an LLM.

VIVA NOTE -- why RAG instead of asking the LLM directly?
    1. Grounding / reduced hallucination: the LLM is instructed to answer
       ONLY from the retrieved passages, not from its parametric memory.
       A general-purpose LLM was never trained on this specific paper (or
       may have never seen it at all if it's unpublished/recent), so
       asking it directly risks a fluent but fabricated answer.
    2. Verifiability: because every claim is tied to a retrieved chunk, we
       can cite the exact page it came from, so a human can check the
       source.
    3. Freshness & scope: the paper can be brand-new, private, or paywalled
       -- nothing the LLM's training data could ever contain. RAG lets the
       model answer about content it never "learned".
    4. Cost/context efficiency: instead of stuffing the entire paper (which
       may exceed the context window) into every prompt, we retrieve only
       the handful of chunks relevant to the specific question.

Supports three free-tier, OpenAI-API-compatible providers, selected via
the LLM_PROVIDER environment variable:
    - groq        (https://console.groq.com)
    - gemini      (https://aistudio.google.com/apikey)
    - openrouter  (https://openrouter.ai)
"""

import os
from dataclasses import dataclass
from typing import List, Tuple

from openai import OpenAI

from src.chunking import Chunk

SYSTEM_PROMPT = """You are a research-paper assistant. Answer the user's \
question using ONLY the numbered CONTEXT passages provided below, which are \
excerpts from a single research paper.

Rules:
1. If the answer is not contained in the context, say clearly: \
"The paper does not appear to address this." Do not guess or use outside \
knowledge.
2. Every factual sentence in your answer must end with a citation marker \
like [1], [2], referring to the numbered context passage(s) it is based on.
3. Be concise and precise. Prefer the paper's own terminology.
4. If asked about objective, methodology, datasets, findings, or \
limitations, structure the answer with a short heading + bullet points \
where helpful.
"""

PROVIDER_CONFIG = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key_env": "GROQ_API_KEY",
        "model_env": "GROQ_MODEL",
        "default_model": "openai/gpt-oss-20b",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key_env": "GEMINI_API_KEY",
        "model_env": "GEMINI_MODEL",
        "default_model": "gemini-3.6-flash",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY",
        "model_env": "OPENROUTER_MODEL",
        "default_model": "openrouter/free",
    },
}


@dataclass
class GeneratedAnswer:
    answer: str
    sources: List[Tuple[int, Chunk, float]]  # (citation_number, chunk, score)


class AnswerGenerator:
    def __init__(self):
        provider = os.getenv("LLM_PROVIDER", "groq").strip().lower()
        if provider not in PROVIDER_CONFIG:
            raise ValueError(
                f"Unknown LLM_PROVIDER '{provider}'. "
                f"Choose one of: {', '.join(PROVIDER_CONFIG)}"
            )
        cfg = PROVIDER_CONFIG[provider]
        api_key = os.getenv(cfg["api_key_env"])
        if not api_key:
            raise ValueError(
                f"Missing {cfg['api_key_env']} for provider '{provider}'. "
                "Set it in your environment or .env file before asking a question."
            )
        self.client = OpenAI(
            base_url=cfg["base_url"],
            api_key=api_key,
        )
        self.model = os.getenv(cfg["model_env"], cfg["default_model"])
        self.provider = provider

    def generate(
        self, question: str, retrieved: List[Tuple[Chunk, float]]
    ) -> GeneratedAnswer:
        numbered_sources = list(enumerate(retrieved, start=1))

        context_block = "\n\n".join(
            f"[{i}] (page {chunk.page_number}) {chunk.text}"
            for i, (chunk, _score) in numbered_sources
        )

        user_prompt = f"CONTEXT:\n{context_block}\n\nQUESTION: {question}"

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,  # low temperature: favor grounded, deterministic answers
        )

        answer_text = response.choices[0].message.content

        sources = [(i, chunk, score) for i, (chunk, score) in numbered_sources]
        return GeneratedAnswer(answer=answer_text, sources=sources)
