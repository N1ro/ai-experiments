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
# One-time setup (installs dependencies for all projects)
make setup

# Start both RAG API and MCP server
make dev
```

This starts:
1. RAG API on `http://localhost:8000`
2. MCP server ready for Claude Desktop

Then proceed to step 2 below.

### Option B: Manual Setup

#### 1. Install dependencies

```bash
pip install -r requirements.txt
```

#### 2. Ensure RAG API is running

The RAG API (Project 1) must be running on `http://localhost:8000`:

```bash
cd ../01-local-rag-pipeline
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### 3. Start the MCP server

In another terminal:

```bash
python src/rag_mcp_server.py
```

### Configure Claude Desktop

Add to `~/.config/claude/claude_desktop_config.json`:

```json
{
    "mcpServers": {
        "rag-local": {
            "command": "python",
            "args": ["/full/path/to/02-mcp-server/src/rag_mcp_server.py"]
        }
    }
}
```

Replace `/full/path/to` with the absolute path to the `02-mcp-server` directory.

### Restart Claude Desktop

Close and reopen Claude Desktop to load the new MCP server. Check the developer tools to verify the connection.

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

Remove a document and its embeddings.

**What it does:**

- Takes a document ID
- Deletes all its chunks from ChromaDB
- Removes metadata from the system

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

### Automated Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_rag_mcp_server.py -v

# Run with coverage
python -m pytest tests/ --cov=src
```

### Manual Testing

1. **Start both services** (from repo root):
   ```bash
   make dev
   ```
   Services running:
   - RAG API: http://localhost:8000/health
   - MCP server: ready for Claude Desktop

2. **Test RAG API directly**:
   ```bash
   # Ingest a test document
   curl -X POST "http://localhost:8000/ingest" \
     -F "files=@document.txt"
   
   # Query it
   curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "Your question", "top_k": 3}'
   
   # Check health
   curl "http://localhost:8000/health"
   ```

3. **Test MCP server tools** (via Claude Desktop):
   - Use `query_knowledge_base` to search your documents
   - Use `ingest_document` to add new content
   - Use `list_documents` to see indexed documents
   - Use `delete_document` to remove specific documents

**Requirements before testing:**
- Ollama running with required models (`ollama list` should show `qwen3:14b` and `nomic-embed-text`)
- RAG API must be accessible on `localhost:8000`
- Python dependencies installed via `make setup`

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

**Problem:** Path in config is incorrect or server not running

```bash
# Verify the config has the FULL absolute path
cat ~/.config/claude/claude_desktop_config.json

# Get the full path to this directory
pwd  # in 02-mcp-server directory

# Test server directly
python src/rag_mcp_server.py
```

Paths must be absolute, not relative. Example:
```json
{
    "mcpServers": {
        "rag-local": {
            "command": "python",
            "args": ["/Users/niro/projects/ai-experiments/02-mcp-server/src/rag_mcp_server.py"]
        }
    }
}
```

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
