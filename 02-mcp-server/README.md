# RAG MCP Server 🔌

Expose your local RAG system to Claude via the Model Context Protocol.

## What This Does

Imagine Claude with direct access to your personal knowledge base. With this MCP server, you can ask Claude questions and have it search your indexed documents using the RAG API (Project 1). Claude becomes aware of your documents and can answer questions using only your data—no internet searches needed.

```
You:     "What did the report say about Q3 revenue?"
    ↓
Claude (with MCP tools)
    ↓
Searches your documents via RAG
    ↓
Answer: "According to doc_revenue_q3.txt, revenue was..."
```

## Understanding MCP

**MCP (Model Context Protocol)** is a simple standard that lets Claude use tools in a structured way. Think of it like:

- Traditional APIs let your code call services
- MCP lets LLMs call tools securely

When you run an MCP server:

1. Claude Desktop connects to your MCP server
2. Your MCP server declares what tools it has
3. Claude can request to use those tools
4. Results flow back to Claude for analysis

In this case, our tools are RAG operations: query, ingest, list, delete documents.

## Overview

This MCP server wraps the RAG API (Project 1) and exposes it as Claude-callable tools. You can now have conversations with Claude while it searches your knowledge base in real-time.

## Setup

### Option A: Automated Setup (Recommended)

From the repository root:

```bash
# One-time setup (installs dependencies for projects 01 and 02)
make setup

# Start the RAG API (required dependency for this MCP server)
make dev
```

This starts the RAG API on `http://localhost:8000`.

> **Note:** The MCP server does **not** need to be started manually. Claude Desktop launches it automatically as a subprocess when you send a message. You only need to configure the path (see below) and restart Claude Desktop once.

### Option B: Manual Setup

**Prerequisites:** Ollama running (`brew services start ollama`)

#### 1. Set up Python environment

```bash
cd 02-mcp-server

# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Start RAG API in one terminal

```bash
cd ../01-local-rag-pipeline

# If not already set up:
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start the API
uvicorn app.main:app --reload
# API will be running on http://localhost:8000
```

#### 3. MCP server (no manual start needed)

The MCP server is launched automatically by Claude Desktop. You don't run it yourself — just configure the path below and restart Claude Desktop.

### Configure Claude Desktop

Find your Claude Desktop config file:
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
  ```bash
  # Note: path has a space — always quote it
  open "/Users/niro/Library/Application Support/Claude/claude_desktop_config.json"
  ```
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

> **Note:** `~/.claude` is the Claude **Code CLI** directory — that is not the same as Claude Desktop's config.

Add the MCP server config. You need two absolute paths — the venv python and the server script:

```json
{
    "mcpServers": {
        "rag-local": {
            "command": "/full/path/to/02-mcp-server/.venv/bin/python",
            "args": ["/full/path/to/02-mcp-server/src/rag_mcp_server.py"]
        }
    }
}
```

**Example for macOS:**
```json
{
    "mcpServers": {
        "rag-local": {
            "command": "/Users/niro/projects/ai-experiments/02-mcp-server/.venv/bin/python",
            "args": ["/Users/niro/projects/ai-experiments/02-mcp-server/src/rag_mcp_server.py"]
        }
    }
}
```

Get your absolute path by running:
```bash
cd 02-mcp-server && pwd
# e.g. /Users/niro/projects/ai-experiments/02-mcp-server
```

Replace `/full/path/to` with that output. Use the **venv python** (`.venv/bin/python`), not the system `python`, to ensure the `mcp` package installed via `pip install -r requirements.txt` is used.

### Restart Claude Desktop

1. Close Claude Desktop completely
2. Wait 5 seconds
3. Reopen Claude Desktop
4. Check that the server connects: ⚙️ → Developer Console → look for "rag-local" server status

## Tools Exposed

### query_knowledge_base

Search your knowledge base with natural language.

**What it does:**

- Takes your question as natural language
- Converts it to embeddings (via nomic-embed-text)
- Finds similar document chunks using cosine similarity
- Generates an answer using Qwen3:14b with retrieved context
- Returns answer + source documents

**Example:** "What are the main challenges in distributed systems?"
→ Searches your documents → Returns relevant sections + synthesized answer

### ingest_document

Add new documents to your knowledge base.

**What it does:**

- Takes document content (file or text)
- Splits into 500-character chunks with 50-char overlap
- Converts each chunk to embeddings
- Stores in ChromaDB with metadata
- Returns document ID for future reference

**Example:** "Add this architecture guide to my knowledge base"
→ Document ingested, chunked, embedded, indexed

### list_documents

View all indexed documents.

**What it does:**

- Returns all documents currently in your knowledge base
- Shows document title, ID, and chunk count
- Useful for managing your document collection

### delete_document

Remove a single document and its embeddings by ID.

**What it does:**

- Takes a document ID (get it from `list_documents`)
- Deletes all its chunks from ChromaDB
- Removes metadata from the system

### delete_all_documents

Wipe the entire knowledge base in one step.

**What it does:**

- Deletes all documents and their embeddings from ChromaDB
- Useful after a test session where you've added throwaway documents
- Equivalent to `make reset` (which also re-ingests sample docs)

**Example:** "Delete all documents from my knowledge base"
→ Knowledge base wiped clean

## Usage Example

### In Claude Desktop

You can now have conversations like:

**Query example:**

```
You: "Search my knowledge base for machine learning techniques"
Claude: [Uses query_knowledge_base tool]
Claude: "Based on your indexed documents, machine learning
involves supervised learning, unsupervised learning, and
reinforcement learning. Your doc_ml_basics.txt covers..."
```

**Ingest example:**

```
You: "Add this document to my knowledge base: <content or file>"
Claude: [Uses ingest_document tool]
Claude: "Document ingested successfully (ID: uuid-xxx).
It was split into 12 chunks and is now searchable."
```

**Management example:**

```
You: "What documents do I have indexed?"
Claude: [Uses list_documents tool]
Claude: "You have 5 documents indexed:
- doc_ml_basics.txt (8 chunks)
- doc_nlp_guide.txt (15 chunks)
..."
```

### Why This Matters

This demonstrates **integration across the AI stack**:

- ✅ Local LLM integration (Claude Desktop ↔ MCP)
- ✅ REST API integration (MCP Server ↔ RAG API)
- ✅ Vector database integration (RAG ↔ ChromaDB)
- ✅ Embedding model integration (ChromaDB ↔ Ollama)

## Testing

### Prerequisites for all testing:
- ✅ Ollama running: `brew services start ollama`
- ✅ Models installed: `ollama list` shows `qwen3:14b` and `nomic-embed-text`
- ✅ Dependencies installed: `make setup` (from repo root)

### Quick Start Testing (Recommended)

```bash
# From repo root, start both services
make dev
```

This starts the RAG API on `http://localhost:8000`. The MCP server is launched automatically by Claude Desktop — no separate startup needed.

In another terminal, test the RAG API:
```bash
# Check health
curl http://localhost:8000/health
# Expected: {"status":"ok"}

# Create a test document, then ingest it
echo "Python is a high-level language used for data science and AI." > /tmp/test.txt
curl -X POST "http://localhost:8000/ingest" \
  -F "files=@/tmp/test.txt"
# Expected: {"documents":[{"filename":"test.txt","doc_id":"...","status":"success"}]}

# Query it
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Python?", "top_k": 1}'
# Expected: {"answer":"Python is a high-level...","sources":[...]}
```

### Manual Testing (if not using make dev)

1. **Terminal 1: Start RAG API**
   ```bash
   cd 01-local-rag-pipeline
   source .venv/bin/activate
   uvicorn app.main:app --reload
   ```

2. **Terminal 2: Verify RAG API is up**
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status":"ok"}
   ```

> The MCP server is started by Claude Desktop automatically — you do not run it in a terminal.

### Testing in Claude Desktop

Once the MCP server is running and configured:

1. Open Claude Desktop
2. Create a new conversation
3. Use these tools:

   **List documents:**
   ```
   You: "What documents do I have indexed?"
   → Claude uses list_documents tool
   ```

   **Search documents:**
   ```
   You: "Search my knowledge base for Python"
   → Claude uses query_knowledge_base tool
   → Returns relevant sections + AI-synthesized answer
   ```

   **Add a document:**
   ```
   You: "Add this to my knowledge base: <paste text>"
   → Claude uses ingest_document tool
   → Document is indexed and searchable
   ```

### Automated Testing (Unit Tests)

No services needed — all HTTP calls are mocked:
```bash
cd 02-mcp-server
source .venv/bin/activate
pytest tests/ -v
```

Covers all five tool handlers (16 tests): `query_knowledge_base`, `ingest_document`, `list_documents`, `delete_document`, `delete_all_documents` — including validation and error cases.

## Troubleshooting

### "Connection refused" to RAG API

**Problem:** RAG API not running on localhost:8000

If using `make dev`:
```bash
# Services should start automatically. If they don't, check Ollama is running
brew services start ollama
# Then try again
make dev
```

If manual setup:
```bash
cd ../01-local-rag-pipeline
.venv/bin/uvicorn app.main:app --reload
```

### "MCP server not found" in Claude Desktop

**Problem:** Path in config is incorrect, server not running, or Claude not restarted

**Step 1: Get the absolute path**
```bash
cd 02-mcp-server
pwd
# Copy the output, e.g. /Users/niro/projects/ai-experiments/02-mcp-server
```

**Step 2: Update the config**

Find your config file (macOS path has a space — always quote it):
- **macOS:** `"/Users/niro/Library/Application Support/Claude/claude_desktop_config.json"`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

Edit it to add (use the venv python, not system python):
```json
{
    "mcpServers": {
        "rag-local": {
            "command": "/Users/niro/projects/ai-experiments/02-mcp-server/.venv/bin/python",
            "args": ["/Users/niro/projects/ai-experiments/02-mcp-server/src/rag_mcp_server.py"]
        }
    }
}
```

Replace `/Users/niro/...` with the path you copied above.

**Step 3: Restart Claude Desktop**
- Close Claude completely (not just the window)
- Wait 5 seconds
- Reopen Claude
- Check status in ⚙️ → Developer Console

### Claude can't find the tools

**Problem:** Claude Desktop needs restart after config change

- Close Claude Desktop completely
- Wait 5 seconds
- Reopen Claude Desktop
- Check that the server connects in dev tools (⚙️ → Developer Console)
- Look for "rag-local" server status

### Tool executions are slow

**Normal:** First query loads Ollama models (~5-10 sec). Subsequent queries are 2-3 seconds.

- First RAG query: ~8 seconds (model loading)
- Subsequent queries: ~2-3 seconds each

This is expected—Ollama caches models in memory after first use.

### Ollama not running

**Problem:** Models can't be loaded

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not, start it
brew services start ollama

# Verify models are installed
ollama list
ollama pull qwen3:14b
ollama pull nomic-embed-text
```

## Architecture

```
Claude Desktop
    ↓
MCP Protocol (structured tool calls)
    ↓
rag_mcp_server.py
    ↓
HTTP REST API (localhost:8000)
    ↓
Project 1: RAG API
    ↓
ChromaDB + Ollama (local, no cloud)
```

**Flow Example:**

User asks Claude: "Search for machine learning content"
↓
Claude calls `query_knowledge_base` via MCP
↓
rag_mcp_server.py makes HTTP request to RAG API
↓
RAG API: embeddings → similarity search → LLM generation
↓
Results returned to Claude
↓
Claude presents answer in conversation

## Licence

MIT
