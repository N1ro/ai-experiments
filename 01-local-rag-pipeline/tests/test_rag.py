import pytest
import asyncio
from app.rag import RAGEngine

@pytest.fixture
async def rag():
    engine = RAGEngine()
    await engine.init()
    yield engine
    await engine.cleanup()

@pytest.mark.asyncio
async def test_ingest_document(rag):
    """Test document ingestion."""
    content = "This is a test document about machine learning."
    doc_id = await rag.ingest("test.txt", content)
    assert doc_id
    assert len(doc_id) > 0

@pytest.mark.asyncio
async def test_list_documents(rag):
    """Test listing documents."""
    content = "Another test document."
    await rag.ingest("test2.txt", content)
    docs = await rag.list_documents()
    assert len(docs) > 0

@pytest.mark.asyncio
async def test_query(rag):
    """Test querying the RAG system."""
    content = "Python is a programming language used for AI and data science."
    await rag.ingest("python.txt", content)

    answer, sources = await rag.query("What is Python?")
    assert answer
    assert len(sources) > 0
    assert sources[0]["doc_id"]
