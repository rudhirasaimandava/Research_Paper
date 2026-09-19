# 📄 Research Paper Question-Answering System (RAG)

A Retrieval-Augmented Generation (RAG) application that lets you upload a research
paper PDF and ask questions about it — objective, methodology, datasets, findings,
limitations, or anything else — with every answer **grounded in the paper and cited
by page number**.

```
┌──────────┐    ┌───────────┐    ┌───────────┐    ┌─────────────┐    ┌────────────┐
│  Upload  │───▶│  Extract  │───▶│   Chunk   │───▶│    Embed +   │───▶│   Store    │
│   PDF    │    │   Text    │    │  (overlap)│    │  index (FAISS│    │  (FAISS +  │
└──────────┘    └───────────┘    └───────────┘    │   IndexFlat) │    │  pickle)   │
                                                     └─────────────┘    └────────────┘
                                                                                │
┌──────────┐    ┌────────────┐    ┌──────────────┐    ┌───────────────┐        │
│  Answer  │◀───│    LLM     │◀───│  Build cited │◀───│  Retrieve top-K│◀──────┘
│ + Sources│    │ generation │    │    prompt    │    │  similar chunks│
└──────────┘    └────────────┘    └──────────────┘    └───────────────┘
        ▲
        └── User question
```

## Features

- **PDF ingestion** — page-accurate text extraction via PyMuPDF
- **Chunking** — recursive, paragraph/sentence-aware splitting with configurable
  size & overlap (`src/chunking.py`)
- **Semantic retrieval** — local `sentence-transformers` embeddings + FAISS
  cosine-similarity search (`src/vectorstore.py`)
- **Context-grounded generation** — LLM is instructed to answer *only* from
  retrieved passages, refusing when the paper doesn't cover something
  (`src/generator.py`)
- **Source citation** — every answer includes `[1] [2]` markers mapped to the
  exact page number the claim came from
- **Streamlit UI** with live sliders for chunk size, overlap, and retrieval depth
  — useful for demonstrating trade-offs in a viva

## Project Structure

```
research-paper-qa-rag/
├── app.py                 # Streamlit UI (entry point)
├── src/
│   ├── ingestion.py        # PDF → page-tagged text (PyMuPDF)
│   ├── chunking.py         # Text → overlapping chunks (LangChain splitter)
│   ├── vectorstore.py       # Chunks → embeddings → FAISS index, save/load
│   ├── generator.py         # Retrieved chunks + question → cited LLM answer
│   └── pipeline.py          # Orchestrates the full flow end-to-end
├── data/
│   ├── uploads/             # (gitignored) uploaded PDFs land here temporarily
│   └── vectorstore/          # (gitignored) persisted FAISS indices
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Setup

### 1. Clone & create a virtual environment

```bash
git clone <your-repo-url>
cd research-paper-qa-rag
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Then edit `.env`:

Pick one LLM provider and set `LLM_PROVIDER` accordingly in `.env`:

| Provider | Cost | Setup | Notes |
|---|---|---|---|
| **Groq** (recommended) | Free tier | Get a key at [console.groq.com](https://console.groq.com), set `GROQ_API_KEY` | Fastest, no card required, OpenAI-compatible |
| **OpenRouter** | Free models available | Get a key at [openrouter.ai](https://openrouter.ai), set `OPENROUTER_API_KEY`, use a model tagged `:free` | Wide model choice |
| **Ollama** | Free, fully local | Install [Ollama](https://ollama.com), `ollama pull llama3.1` | No API key, no internet needed for the LLM call, but needs decent RAM |
| **OpenAI** | Paid (pay-as-you-go) | Get a key at [platform.openai.com](https://platform.openai.com), set `OPENAI_API_KEY` | Cheap with `gpt-4o-mini`, but requires billing setup |

Embeddings (`sentence-transformers`) already run 100% locally regardless of
which LLM provider you choose — only the final answer-generation step calls
out to the LLM API.

### 4. Run the app

```bash
streamlit run app.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`), upload a PDF,
click **Process paper**, and start asking questions.

## Pushing to GitHub

```bash
git init
git add .
git commit -m "Initial commit: Research Paper QA RAG system"
git branch -M main
git remote add origin https://github.com/<your-username>/research-paper-qa-rag.git
git push -u origin main
```

`.env` and everything under `data/uploads` and `data/vectorstore` are already
excluded via `.gitignore` so you never accidentally commit your API key or a
copyrighted PDF.

## How each requirement is implemented

| Requirement | Where | Notes |
|---|---|---|
| PDF ingestion | `src/ingestion.py` | `PyMuPDF (fitz)` opens the PDF and extracts text per page |
| Text extraction | `src/ingestion.py` | Whitespace/newline cleanup; near-empty pages (title pages, figures) skipped |
| Chunking | `src/chunking.py` | `RecursiveCharacterTextSplitter` — tries paragraph, then sentence, then word boundaries before hard-cutting |
| Semantic retrieval | `src/vectorstore.py` | `all-MiniLM-L6-v2` embeddings, FAISS `IndexFlatIP` (cosine similarity after L2-normalization) |
| Context-grounded generation | `src/generator.py` | System prompt forces the LLM to answer only from numbered context passages, refuse otherwise, `temperature=0.1` |
| Source citation | `src/generator.py`, `app.py` | Each context passage is numbered `[1]..[k]`; the LLM must cite them; UI shows page number + similarity score per citation |

## Viva Prep — Likely Questions & Answers

### Q: Why RAG instead of just asking the LLM directly?

1. **Grounding / hallucination reduction** — a general LLM wasn't trained on
   this specific paper (it may be unpublished, paywalled, or newer than the
   model's training cutoff). Asking directly risks a fluent but fabricated
   answer. RAG forces the model to answer only from retrieved, real text.
2. **Verifiability** — every claim is traceable to a page number, so a human
   can check it.
3. **Freshness/scope** — works on any paper you feed it, including brand-new
   or private documents the LLM never saw during training.
4. **Efficiency** — instead of stuffing an entire paper into every prompt
   (which may exceed the context window and costs more tokens), we retrieve
   only the handful of chunks relevant to the specific question.

### Q: Why chunk the text instead of embedding the whole paper as one vector?

A single embedding for an entire paper would average together many unrelated
topics (methodology, related work, results, limitations), producing a vague
vector that matches poorly against specific questions. Chunking lets each
piece of text get its own precise embedding, so retrieval can zero in on the
paragraph that actually discusses "datasets" or "limitations".

### Q: How did you choose chunk size and overlap?

- **Chunk size (default 1000 characters ≈ 150-200 words)**: large enough to
  contain a complete idea/paragraph, small enough to keep the embedding
  focused and keep the number of chunks fed to the LLM manageable.
  - Too small → context fragmented across many chunks, retrieval noisy.
  - Too large → embeddings become diluted/generic, retrieval less precise,
    higher token cost per LLM call.
- **Overlap (default 200 characters, ~20%)**: prevents ideas that straddle a
  chunk boundary from being split in half and becoming unretrievable as a
  coherent unit. Common practice is 10-20% of chunk size.

Both are exposed as sliders in the UI so you can demonstrate the effect live —
e.g. shrink chunk size to 300 and show how retrieval becomes noisier/more
fragmented for a "what are the findings" question.

### Q: What does "retrieval depth" (top-K) control, and what's the trade-off?

`top_k` is how many chunks are retrieved per question and passed to the LLM.

- **Too low (e.g. K=1)** → the LLM may miss a relevant passage that scored
  slightly lower, giving an incomplete answer.
- **Too high (e.g. K=15)** → irrelevant/low-similarity chunks get included,
  which can dilute the prompt, increase cost, and occasionally confuse the
  model into citing weakly-relevant text. Default K=5 balances coverage and
  precision for typical research-paper questions.

### Q: How do you measure/ensure retrieval quality?

We use cosine similarity (via L2-normalized inner product in FAISS) between
the question embedding and each chunk embedding. The UI surfaces the
similarity score for each retrieved source, so low-confidence retrievals are
visible rather than hidden.

### Q: What happens if the paper doesn't contain the answer?

The system prompt in `src/generator.py` explicitly instructs the LLM to
respond "The paper does not appear to address this" rather than guessing —
this is what makes the system grounded instead of just another chatbot with
extra text pasted in.

### Q: Why sentence-transformers for embeddings instead of OpenAI embeddings?

`all-MiniLM-L6-v2` runs entirely locally, is fast, free, and has no
rate limits — ideal for a project/demo setting. The architecture is
provider-agnostic: swapping in `text-embedding-3-small` (OpenAI) would only
require changing `src/vectorstore.py`.

## Possible Extensions (good talking points if asked "what would you improve")

- Multi-paper support (compare/contrast across several PDFs)
- Hybrid retrieval (BM25 keyword search + semantic search, reranked)
- Table/figure-aware extraction (papers often put key results in tables)
- Streaming LLM responses in the UI
- Automated evaluation harness (e.g. compare answers against a gold Q&A set,
  measure citation accuracy)
