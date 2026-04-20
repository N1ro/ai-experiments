from fastapi import FastAPI, HTTPException, UploadFile, File
from contextlib import asynccontextmanager
from app.rag import RAGEngine
from pydantic import BaseModel
import os

rag = RAGEngine()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await rag.init()
    yield
    await rag.cleanup()

app = FastAPI(title="Local RAG Pipeline", lifespan=lifespan)

class QueryRequest(BaseModel):
    query: str
    top_k: int = 3

class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]

class DocumentInfo(BaseModel):
    id: str
    title: str
    chunks: int

@app.post("/ingest")
async def ingest_documents(files: list[UploadFile] = File(...)):
    """Upload and ingest documents."""
    results = []
    for file in files:
        try:
            content = await file.read()
            doc_id = await rag.ingest(file.filename, content.decode("utf-8"))
            results.append({"filename": file.filename, "doc_id": doc_id, "status": "success"})
        except Exception as e:
            results.append({"filename": file.filename, "error": str(e)})
    return {"documents": results}

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Query the RAG system."""
    try:
        answer, sources = await rag.query(request.query, top_k=request.top_k)
        return QueryResponse(answer=answer, sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents", response_model=list[DocumentInfo])
async def list_documents():
    """List all indexed documents."""
    try:
        docs = await rag.list_documents()
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document from the index."""
    try:
        await rag.delete_document(doc_id)
        return {"status": "deleted", "doc_id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
