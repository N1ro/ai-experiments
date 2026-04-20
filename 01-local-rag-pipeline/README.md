# Local RAG Pipeline 🚀

**Build a personal AI search engine that runs 100% on your machine.**

Retrieval-Augmented Generation (RAG) lets you chat with your own documents using local AI models. No API keys needed. No data sent to the cloud. Just you, your docs, and powerful AI.

---

## Table of Contents

- [What This Does](#what-this-does)
- [The Magic: How It Works](#the-magic-how-it-works)
- [Quick Start](#quick-start)
- [Try It Out](#try-it-out)
- [API Endpoints](#api-endpoints)
- [Under the Hood](#under-the-hood)
- [Troubleshooting](#troubleshooting)
- [Tech Stack](#tech-stack)
- [Next Steps](#next-steps)
- [Performance Tips](#performance-tips)
- [Questions?](#questions)

---

## What This Does

You upload documents → RAG indexes them → You ask questions → AI finds relevant sections and generates answers.

```
Your Documents (PDFs, TXT, etc.)
    ↓
🔍 [Indexed with embeddings]
    ↓
💾 [Stored locally in ChromaDB]
    ↓
User: "Tell me about Python"
    ↓
🧠 [Find similar documents]
    ↓
🤖 [Generate answer with context]
    ↓
Answer: "Python is a high-level language..."
```

---

## The Magic: How It Works

### Three Models Working Together

**1. Ollama** — Your Local AI Server
- Runs AI models on your machine (no cloud, no costs)
- Exposes a simple HTTP API at `localhost:11434`
- Think of it like Docker, but for AI models

**2. nomic-embed-text** — Text-to-Vector Converter
- Converts text into 768 numbers that capture its meaning
- Example:
  ```
  Input:  "Python is a programming language"
  Output: [0.25, -0.18, 0.92, 0.15, ..., -0.44]
  ```
- Used to **find relevant documents** (similar texts have similar vectors)
- **Speed:** ~1ms per document chunk

**3. Qwen3:14b** — Answer Generator
- A 14-billion parameter language model (like ChatGPT, but open-source)
- Reads document context + your question → generates smart answers
- **Speed:** 2-5 seconds per answer
- Only runs when you ask a question (not for every document)

### The RAG Pipeline Flow

```
STEP 1: INGEST YOUR DOCUMENTS
Your Files (doc1.txt, doc2.txt, ...)
    ↓
[Split into 500-char chunks]
    ↓
[nomic-embed-text converts each chunk → 768-dim vector]
    ↓
[ChromaDB stores vectors + original text]

STEP 2: USER ASKS A QUESTION
Question: "Tell me about Python"
    ↓
[nomic-embed-text converts query → 768-dim vector]
    ↓
[ChromaDB finds most similar chunks via cosine similarity]
    ↓
Top Matches:
  - doc3.txt (similarity: 0.98) ✅
  - doc1.txt (similarity: 0.45)
  - doc2.txt (similarity: 0.12)

STEP 3: GENERATE ANSWER
Top 3 matching chunks + Question
    ↓
[Qwen3:14b reads context + question]
    ↓
[Generates answer based on retrieved docs]
    ↓
Answer: "Python is a high-level programming language..."
```

### Why This Is Fast & Smart

- **nomic-embed-text** searches thousands of documents in milliseconds
- **Qwen3:14b** only generates answers for the top 3-5 matches (not every document)
- Result: **Smart + Fast** ⚡

---

## Quick Start

### Prerequisites

Make sure you have:
- Ollama running with these models loaded:
  ```bash
  ollama pull qwen3:14b
  ollama pull nomic-embed-text
  ```
  (You've probably done this already!)
- Python 3.12+
- ~2 GB free disk space (for ChromaDB)

### Setup (5 minutes)

```bash
# Navigate to project
cd /Users/niro/projects/ai-experiments/01-local-rag-pipeline

# Install dependencies (one time)
pip install -r requirements.txt

# Copy environment config
cp .env.example .env

# Start the API
uvicorn app.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

## Try It Out

### In a new terminal:

#### 1. Create some test documents

```bash
cat > /tmp/doc1.txt << 'EOF'
Machine Learning enables computers to learn from data without explicit programming. 
It powers recommendation systems, image recognition, and predictive analytics.
Key techniques: supervised learning, unsupervised learning, reinforcement learning.
EOF

cat > /tmp/doc2.txt << 'EOF'
Deep Learning uses neural networks with multiple layers for AI breakthroughs.
Powers natural language processing, computer vision, and autonomous systems.
Popular frameworks: TensorFlow, PyTorch, Keras.
EOF

cat > /tmp/doc3.txt << 'EOF'
Python is a high-level programming language prized for simplicity and readability.
Go-to language for data science, web development, automation, and AI.
Rich ecosystem: NumPy, Pandas, scikit-learn, TensorFlow.
EOF
```

#### 2. Upload them to RAG

```bash
curl -X POST "http://localhost:8000/ingest" \
  -F "files=@/tmp/doc1.txt" \
  -F "files=@/tmp/doc2.txt" \
  -F "files=@/tmp/doc3.txt"
```

Response:
```json
{
  "documents": [
    {"filename": "doc1.txt", "doc_id": "uuid-123", "status": "success"},
    {"filename": "doc2.txt", "doc_id": "uuid-456", "status": "success"},
    {"filename": "doc3.txt", "doc_id": "uuid-789", "status": "success"}
  ]
}
```

#### 3. Ask a question

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?", "top_k": 3}'
```

**First query takes 5-10 seconds** (loading models into memory). **Subsequent queries are 2-3 seconds.**

Response:
```json
{
  "answer": "Machine Learning is a subset of AI that enables computers to learn from data...",
  "sources": [
    {
      "doc_id": "uuid-123",
      "title": "doc1.txt",
      "content": "Machine Learning enables computers to learn from data..."
    }
  ]
}
```

#### 4. Try more queries

```bash
# Query 2
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Tell me about Python for AI", "top_k": 2}'

# List your documents
curl "http://localhost:8000/documents"

# Delete a document
curl -X DELETE "http://localhost:8000/documents/uuid-123"
```

---

## API Endpoints

### POST `/ingest`
Upload documents to index them

```bash
curl -X POST "http://localhost:8000/ingest" \
  -F "files=@document1.txt" \
  -F "files=@document2.pdf"
```

### POST `/query`
Search and get AI-generated answers

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Your question here",
    "top_k": 3
  }'
```

**Parameters:**
- `query` (string, required): Your question
- `top_k` (int, optional): Number of document chunks to retrieve (default: 3)

### GET `/documents`
List all indexed documents

```bash
curl "http://localhost:8000/documents"
```

### DELETE `/documents/{doc_id}`
Remove a specific document from the index

```bash
curl -X DELETE "http://localhost:8000/documents/doc-uuid-here"
```

### DELETE `/documents`
Remove **all documents** from the index at once

```bash
curl -X DELETE "http://localhost:8000/documents"
```

**Warning:** This deletes everything. Use only when you want a clean slate.

### GET `/health`
Check if the API is running

```bash
curl "http://localhost:8000/health"
```

---

## Under the Hood

| Component | Purpose | Speed |
|-----------|---------|-------|
| **nomic-embed-text** | Converts text → vectors for search | ~1ms per chunk |
| **ChromaDB** | Stores vectors, searches by similarity | ~10ms per search |
| **Qwen3:14b** | Generates answers from context | 2-5 sec per answer |

**Key insight:** Search is fast (embedding), generation is slower (LLM). RAG only generates for the **most relevant documents**, not every document.

---

## Troubleshooting

### "Error: embedding_function is None"
**Problem:** Ollama not running
```bash
brew services start ollama
```

### "Error: connection refused"
**Problem:** Can't connect to Ollama
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not, start it
brew services start ollama
```

### "Error: model not found"
**Problem:** Models not downloaded
```bash
ollama pull qwen3:14b
ollama pull nomic-embed-text
```

### First query is very slow (30+ seconds)
**Expected behavior!** First query loads models into memory. Subsequent queries are 2-3 seconds.

### Want to clear the index?

**Option 1: Via API (recommended)**
```bash
curl -X DELETE "http://localhost:8000/documents"
```

**Option 2: Delete the database file**
```bash
rm -rf ./chroma_db
```

Option 1 clears documents while keeping the API running. Option 2 requires restarting the API.

---

## Tech Stack

- **FastAPI** — Web framework
- **Ollama** — Local AI runtime (Qwen3:14b, nomic-embed-text)
- **ChromaDB** — Vector database
- **LangChain** — RAG orchestration
- **Python 3.12**

---

## Next Steps

1. **Try with your own documents** — Upload PDFs, markdown, or text files
2. **Experiment with queries** — See how the AI finds relevant sections
3. **Extend it** — Add authentication, web UI, persistence
4. **Use for real tasks** — Build a chatbot for your documentation, knowledge base, etc.

---

## Performance Tips

- **First query slower?** Normal — Qwen3:14b loads into memory on first use
- **Searching 1000 documents?** Still fast — nomic-embed-text is optimized for this
- **Running out of RAM?** Reduce `top_k` or use smaller model (Llama3.3 requires more RAM)
- **Want faster answers?** Use Llama3.3:70b (more accurate, slower) or Qwen3:14b (faster, good)

---

## Licence

MIT

---

## Questions?

- **How does RAG work?** → See "How It Works" section above
- **Can I use different models?** → Yes! Change `qwen3:14b` in `app/rag.py` to any Ollama model
- **Can I add web UI?** → Yes! Build a simple frontend that calls these REST endpoints
- **How do I deploy this?** → Docker Compose file included; also works on cloud with Ollama
