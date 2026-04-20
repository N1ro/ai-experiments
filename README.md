# AI Experiments 🚀

Applied AI engineering portfolio — built to demonstrate hands-on experience with RAG, MCP, agentic workflows, and LLM integration. **All projects run 100% locally with no cloud costs.**

## Projects

| # | Name | Purpose | Key Technologies |
|---|------|---------|------------------|
| 01 | [Local RAG Pipeline](./01-local-rag-pipeline/) | Personal AI search engine that understands your documents | FastAPI, ChromaDB, LangChain, Ollama, embeddings |
| 02 | [RAG MCP Server](./02-mcp-server/) | Expose your RAG system to Claude via Model Context Protocol | MCP SDK, Python, API integration |
| 03 | [Agentic QA Workflow](./03-agentic-qa/) | Autonomous AI agent that writes tests for GitHub repos | LangGraph, Claude API, GitHub API, tool use |

## What You'll Learn

- **RAG** — Retrieval-Augmented Generation: combining semantic search with LLM generation
- **Vector embeddings** — Converting text to meaningful numerical representations
- **MCP** — Model Context Protocol: letting LLMs use external tools safely
- **Agentic workflows** — Building AI that makes decisions and iterates toward goals
- **Local AI** — Running models on your machine (Ollama) without cloud costs

## Local Setup

See [SETUP.md](./SETUP.md) for complete local AI environment setup (Ollama, Python, models).

## Tech Stack

- **Local LLM Runtime:** Ollama (exposes models via HTTP API)
- **Language Models:** Qwen3:14b via Ollama
- **Embeddings:** nomic-embed-text via Ollama
- **Vector Storage:** ChromaDB (pure Python, no dependencies)
- **Orchestration:** LangChain, LangGraph
- **Web Framework:** FastAPI
- **Testing:** pytest

## Why This Stack?

- **Qwen3:14b** — Fast, efficient, good for coding tasks
- **nomic-embed-text** — Lightweight embeddings (768-dim vectors)
- **ChromaDB** — Pure Python vector DB (no PostgreSQL/pgvector system dependencies)
- **Ollama** — Single binary for local model serving
- **FastAPI** — Async Python web framework for AI APIs
- **LangChain/LangGraph** — Industry standard for AI application orchestration

## Project Progression

**Project 1 is foundational:**
```
Project 1 (RAG API)
    ↓ HTTP API
Project 2 (MCP Server) — uses Project 1's API
    ↓
Project 3 (Agent) — could use Project 2's tools
```

Start with Project 1, then explore how 2 and 3 integrate with it.

## Licence

MIT — model weights carry their own licences (see each project README).
# ai-experiments
