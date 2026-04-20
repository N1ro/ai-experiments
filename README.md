# AI Experiments

Applied AI engineering portfolio — built to demonstrate hands-on experience with RAG, MCP, agentic workflows, and LLM integration.

## Projects

| #   | Project                                        | Key Tech                                         | BCN JD Coverage                       |
| --- | ---------------------------------------------- | ------------------------------------------------ | ------------------------------------- |
| 01  | [Local RAG Pipeline](./01-local-rag-pipeline/) | FastAPI, PostgreSQL, pgvector, LangChain, Ollama | RAG, vector databases, Python/FastAPI |
| 02  | [Custom MCP Server](./02-mcp-server/)          | Python MCP SDK, Anthropic                        | MCP, LLM tool use                     |
| 03  | [Agentic QA Workflow](./03-agentic-qa/)        | LangGraph, Claude API, GitHub API                | Agentic workflows, tool use           |
| 04  | [Vibe Align + AI Matching](./04-vibe-align/)   | FastAPI, pgvector, ARCore, Kotlin Multiplatform  | Full-stack AI, embeddings             |

## Local Setup

See [SETUP.md](./SETUP.md) for full local AI environment installation (Ollama, PostgreSQL + pgvector, Python).

## Stack

- **Local models:** Qwen3:14b (code), Llama3.3:70b (reasoning) via Ollama
- **Embeddings:** nomic-embed-text via Ollama
- **Vector store:** PostgreSQL + pgvector
- **Orchestration:** LangChain / LangGraph
- **API:** FastAPI
- **Tests:** pytest

## Licence

MIT — model weights carry their own licences (see each project README).
