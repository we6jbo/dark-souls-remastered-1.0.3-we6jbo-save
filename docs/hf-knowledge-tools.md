# Hugging Face Knowledge Tools

These tools are part of the we6jbo Dark Souls Text/Schematic Simulator. All model inference runs locally after public Hugging Face model files are downloaded. Hugging Face hosted inference is not authorized.

## Tools

- **Knowledge Search**: semantic retrieval, reranking, and duplicate similarity checks.
- **Classifier**: local zero-shot classification.
- **Summarizer**: local summarization.
- **Knowledge QA**: local extractive question answering.

## Installed models

- **Semantic search**: `sentence-transformers/all-MiniLM-L6-v2`
- **Reranker**: `cross-encoder/ms-marco-MiniLM-L6-v2`
- **Zero-shot classification**: `typeform/distilbert-base-uncased-mnli`
- **Summarization**: `sshleifer/distilbart-cnn-12-6`
- **Question answering**: `distilbert/distilbert-base-cased-distilled-squad`
- **Duplicate detection**: `sentence-transformers/all-MiniLM-L6-v2`

## How to use

Open the appropriate GUI tab, enter public-safe text or a question, and press its action button. The simulator keeps these actions disabled until every module passes a fresh automatic validation.

Private-book entries are excluded from the HF Knowledge retrieval corpus. HF paid inference is disabled and HF authorized spend is **$0**. The separate overall project ceiling remains **$34**.

## Project

https://we6jbo.github.io/dark-souls-remastered-1.0.3-we6jbo-save/
