import pytest
import pytest_asyncio
import asyncio
import os
import tempfile
import shutil
from app.rag import RAGEngine


@pytest_asyncio.fixture(scope="function")
async def rag():
    """Create a RAG engine with temporary ChromaDB for testing."""
    import uuid
    # Use unique directory for each test to avoid cross-contamination
    tmpdir = tempfile.mkdtemp(prefix=f"chroma_test_{uuid.uuid4().hex}_")
    os.environ["CHROMA_DB_PATH"] = tmpdir
    engine = RAGEngine()
    await engine.init()
    yield engine
    await engine.cleanup()
    shutil.rmtree(tmpdir, ignore_errors=True)


# ============= Ingestion Tests =============

@pytest.mark.asyncio
async def test_ingest_single_document(rag):
    """Test ingesting a single document."""
    content = "Python is a programming language used for data science."
    doc_id = await rag.ingest("test.txt", content)

    assert doc_id is not None
    assert len(doc_id) > 0
    assert doc_id in rag.documents_meta
    assert rag.documents_meta[doc_id]["title"] == "test.txt"


@pytest.mark.asyncio
async def test_ingest_multiple_documents(rag):
    """Test ingesting multiple documents."""
    docs = [
        ("doc1.txt", "Machine Learning enables computers to learn from data."),
        ("doc2.txt", "Deep Learning uses neural networks."),
        ("doc3.txt", "Python is a programming language."),
    ]

    doc_ids = []
    for title, content in docs:
        doc_id = await rag.ingest(title, content)
        doc_ids.append(doc_id)

    assert len(doc_ids) == 3
    assert len(rag.documents_meta) == 3
    assert all(doc_id in rag.documents_meta for doc_id in doc_ids)


@pytest.mark.asyncio
async def test_ingest_long_document_chunking(rag):
    """Test that long documents are properly chunked."""
    long_content = "This is a sentence. " * 50  # Create a document > 500 chars
    doc_id = await rag.ingest("long.txt", long_content)

    chunk_count = rag.documents_meta[doc_id]["chunk_count"]
    assert chunk_count > 1  # Should be split into multiple chunks


# ============= Query Tests =============

@pytest.mark.asyncio
async def test_query_with_documents(rag):
    """Test querying when documents are indexed."""
    await rag.ingest("python.txt", "Python is a high-level programming language.")
    await rag.ingest("ml.txt", "Machine Learning is subset of AI.")

    answer, sources = await rag.query("What is Python?")

    assert answer is not None
    assert len(answer) > 0
    assert len(sources) > 0
    assert all("doc_id" in s and "title" in s and "content" in s for s in sources)


@pytest.mark.asyncio
async def test_query_with_no_documents(rag):
    """Test querying when no documents are indexed."""
    answer, sources = await rag.query("test query")

    # When truly no documents exist, should get this message
    assert answer in [
        "No documents found in the knowledge base. Please ingest documents first.",
        "No documents found matching your query. Please try a different search or check the knowledge base."
    ]
    assert sources == []


@pytest.mark.asyncio
async def test_query_below_threshold(rag):
    """Test querying when matches are below threshold."""
    await rag.ingest("python.txt", "Python programming.")

    # Use high threshold so even good matches don't pass
    answer, sources = await rag.query("python", similarity_threshold=0.9)

    assert "No documents found matching" in answer
    assert sources == []


@pytest.mark.asyncio
async def test_query_respects_top_k(rag):
    """Test that top_k parameter limits results."""
    for i in range(5):
        await rag.ingest(f"doc{i}.txt", f"Document {i} about programming.")

    answer, sources = await rag.query("programming", top_k=2)

    assert len(sources) <= 2


@pytest.mark.asyncio
async def test_query_semantic_relevance(rag):
    """Test that semantic search returns relevant documents."""
    await rag.ingest("python.txt", "Python programming language.")
    await rag.ingest("biology.txt", "Photosynthesis in plants.")

    answer, sources = await rag.query("code", top_k=2)

    # Should find Python doc as more relevant
    assert any("python" in s["title"].lower() for s in sources)


@pytest.mark.asyncio
async def test_query_sources_format(rag):
    """Test that query sources have correct format."""
    doc_id = await rag.ingest("test.txt", "Python and machine learning together.")

    answer, sources = await rag.query("Python machine learning")

    assert len(sources) > 0
    source = sources[0]
    assert "doc_id" in source
    assert "title" in source
    assert "content" in source
    assert source["title"] == "test.txt"
    assert len(source["content"]) > 0
    assert len(source["content"]) <= 200  # Truncated to 200 chars


# ============= List Documents Tests =============

@pytest.mark.asyncio
async def test_list_documents_empty(rag):
    """Test listing documents when none exist."""
    docs = await rag.list_documents()
    assert docs == []


@pytest.mark.asyncio
async def test_list_documents_with_content(rag):
    """Test listing documents after ingestion."""
    await rag.ingest("doc1.txt", "Content 1.")
    await rag.ingest("doc2.txt", "Content 2.")

    docs = await rag.list_documents()

    assert len(docs) == 2
    assert any(d["title"] == "doc1.txt" for d in docs)
    assert any(d["title"] == "doc2.txt" for d in docs)
    assert all("id" in d and "title" in d and "chunks" in d for d in docs)


# ============= Delete Tests =============

@pytest.mark.asyncio
async def test_delete_single_document(rag):
    """Test deleting a single document."""
    doc_id = await rag.ingest("doc1.txt", "Content here.")

    # Verify it exists
    docs = await rag.list_documents()
    assert len(docs) == 1

    # Delete it
    await rag.delete_document(doc_id)

    # Verify it's gone
    docs = await rag.list_documents()
    assert len(docs) == 0


@pytest.mark.asyncio
async def test_delete_all_documents(rag):
    """Test deleting all documents at once."""
    for i in range(3):
        await rag.ingest(f"doc{i}.txt", f"Content {i}.")

    # Verify multiple docs exist
    docs = await rag.list_documents()
    assert len(docs) == 3

    # Delete all
    await rag.delete_all_documents()

    # Verify all are gone
    docs = await rag.list_documents()
    assert len(docs) == 0

    # Query should also return no results
    answer, sources = await rag.query("test")
    assert sources == []


@pytest.mark.asyncio
async def test_delete_nonexistent_document(rag):
    """Test deleting a document that doesn't exist (should not error)."""
    # Should not raise an exception
    await rag.delete_document("nonexistent-id")
    docs = await rag.list_documents()
    assert len(docs) == 0


# ============= Integration Tests =============

@pytest.mark.asyncio
async def test_ingest_delete_query_cycle(rag):
    """Test a full cycle of ingest, query, delete."""
    # Ingest
    doc_id = await rag.ingest("test.txt", "Python is great.")

    # Query should find it
    answer, sources = await rag.query("Python")
    assert len(sources) > 0

    # Delete
    await rag.delete_document(doc_id)

    # Query should not find anything
    answer, sources = await rag.query("Python")
    assert sources == []


@pytest.mark.asyncio
async def test_multiple_ingest_same_title(rag):
    """Test ingesting multiple documents with same title (should get different IDs)."""
    doc_id1 = await rag.ingest("test.txt", "Content 1.")
    doc_id2 = await rag.ingest("test.txt", "Content 2.")

    # Should have different IDs
    assert doc_id1 != doc_id2

    # Both should be listed
    docs = await rag.list_documents()
    assert len(docs) == 2


# ============= Similarity Threshold Tests =============

@pytest.mark.asyncio
async def test_similarity_threshold_high_match(rag):
    """Test that high-similarity documents pass threshold."""
    await rag.ingest("python.txt", "Python is a high-level programming language.")

    answer, sources = await rag.query("Python", top_k=1, similarity_threshold=0.5)

    assert len(sources) > 0
    assert sources[0]["title"] == "python.txt"


@pytest.mark.asyncio
async def test_similarity_threshold_low_match(rag):
    """Test that low-similarity documents are filtered out."""
    await rag.ingest("python.txt", "Python is a high-level programming language.")

    # Query with unrelated term and high threshold
    answer, sources = await rag.query("niroshan", top_k=2, similarity_threshold=0.6)

    # Should return no results because similarity is too low
    assert len(sources) == 0
    assert "No documents found matching" in answer


@pytest.mark.asyncio
async def test_similarity_threshold_no_results(rag):
    """Test behavior when query matches nothing above threshold."""
    await rag.ingest("doc1.txt", "Machine Learning")
    await rag.ingest("doc2.txt", "Deep Learning")

    answer, sources = await rag.query("xyz123nonsense", similarity_threshold=0.7)

    assert len(sources) == 0
    assert "No documents found matching" in answer


@pytest.mark.asyncio
async def test_similarity_threshold_partial_filter(rag):
    """Test threshold filters some but not all results."""
    await rag.ingest("python.txt", "Python is a programming language.")
    await rag.ingest("ml.txt", "Machine Learning techniques.")
    await rag.ingest("biology.txt", "Photosynthesis in plants.")

    # Query should match Python strongly, ML weakly, biology poorly
    answer, sources = await rag.query("python", top_k=3, similarity_threshold=0.5)

    # Should include python and maybe ml, but not biology
    assert any(s["title"] == "python.txt" for s in sources)
    assert not any(s["title"] == "biology.txt" for s in sources)


@pytest.mark.asyncio
async def test_similarity_threshold_respects_top_k(rag):
    """Test that top_k is still enforced even with threshold."""
    await rag.ingest("python.txt", "Python programming language.")
    await rag.ingest("data.txt", "Data science with Python.")
    await rag.ingest("web.txt", "Web development with Python.")

    # Even if 3 docs match threshold, top_k=1 should limit to 1
    answer, sources = await rag.query("Python", top_k=1, similarity_threshold=0.3)

    assert len(sources) <= 1


@pytest.mark.asyncio
async def test_similarity_threshold_default(rag):
    """Test that default threshold is 0.5."""
    await rag.ingest("python.txt", "Python is great.")

    # Should use default threshold of 0.5
    answer, sources = await rag.query("Python")

    assert len(sources) > 0
