"""Unit tests for the RAG MCP server tool handlers.

All HTTP calls to the RAG API are mocked so these tests run without
needing Ollama, ChromaDB, or the RAG API running.
"""

import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from rag_mcp_server import (
    query_knowledge_base,
    ingest_document,
    list_documents,
    delete_document,
)


# ============= query_knowledge_base =============

@pytest.mark.asyncio
async def test_query_missing_query_field():
    result = await query_knowledge_base({})
    assert result.isError is True
    assert "Query is required" in result.content[0].text


@pytest.mark.asyncio
async def test_query_success():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "answer": "Python is a programming language.",
        "sources": [
            {"doc_id": "abc-123", "title": "python.txt", "content": "Python is great."}
        ],
    }

    with patch("rag_mcp_server.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        result = await query_knowledge_base({"query": "What is Python?"})

    assert result.isError is False
    text = result.content[0].text
    assert "Answer:" in text
    assert "Python is a programming language." in text
    assert "python.txt" in text
    assert "abc-123" in text


@pytest.mark.asyncio
async def test_query_uses_top_k():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"answer": "ok", "sources": []}

    with patch("rag_mcp_server.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        await query_knowledge_base({"query": "test", "top_k": 5})
        call_kwargs = mock_client.post.call_args
        assert call_kwargs.kwargs["json"]["top_k"] == 5


@pytest.mark.asyncio
async def test_query_rag_api_error():
    with patch("rag_mcp_server.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(side_effect=Exception("Connection refused"))
        mock_client_cls.return_value = mock_client

        result = await query_knowledge_base({"query": "test"})

    assert result.isError is True
    assert "Error querying RAG" in result.content[0].text


# ============= ingest_document =============

@pytest.mark.asyncio
async def test_ingest_missing_content_and_url():
    result = await ingest_document({"title": "doc.txt"})
    assert result.isError is True
    assert "URL or content is required" in result.content[0].text


@pytest.mark.asyncio
async def test_ingest_with_content():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "documents": [{"doc_id": "uuid-999", "status": "success"}]
    }

    with patch("rag_mcp_server.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        result = await ingest_document({
            "title": "test.txt",
            "content": "This is test content."
        })

    assert result.isError is False
    assert "test.txt" in result.content[0].text
    assert "uuid-999" in result.content[0].text


@pytest.mark.asyncio
async def test_ingest_with_url_fetch_failure():
    with patch("rag_mcp_server.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=Exception("URL not reachable"))
        mock_client_cls.return_value = mock_client

        result = await ingest_document({
            "title": "remote.txt",
            "url": "http://example.invalid/doc.txt"
        })

    assert result.isError is True
    assert "Error fetching URL" in result.content[0].text


@pytest.mark.asyncio
async def test_ingest_api_error():
    with patch("rag_mcp_server.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(side_effect=Exception("RAG API down"))
        mock_client_cls.return_value = mock_client

        result = await ingest_document({"title": "doc.txt", "content": "content"})

    assert result.isError is True
    assert "Error ingesting document" in result.content[0].text


# ============= list_documents =============

@pytest.mark.asyncio
async def test_list_documents_empty():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = []

    with patch("rag_mcp_server.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        result = await list_documents({})

    assert result.isError is False
    assert "No documents indexed yet" in result.content[0].text


@pytest.mark.asyncio
async def test_list_documents_with_results():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = [
        {"id": "abc-1", "title": "doc1.txt", "chunks": 3},
        {"id": "abc-2", "title": "doc2.txt", "chunks": 5},
    ]

    with patch("rag_mcp_server.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        result = await list_documents({})

    assert result.isError is False
    text = result.content[0].text
    assert "doc1.txt" in text
    assert "doc2.txt" in text
    assert "abc-1" in text
    assert "chunks: 3" in text


@pytest.mark.asyncio
async def test_list_documents_api_error():
    with patch("rag_mcp_server.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))
        mock_client_cls.return_value = mock_client

        result = await list_documents({})

    assert result.isError is True
    assert "Error listing documents" in result.content[0].text


# ============= delete_document =============

@pytest.mark.asyncio
async def test_delete_missing_doc_id():
    result = await delete_document({})
    assert result.isError is True
    assert "doc_id is required" in result.content[0].text


@pytest.mark.asyncio
async def test_delete_success():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    with patch("rag_mcp_server.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.delete = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        result = await delete_document({"doc_id": "abc-123"})

    assert result.isError is False
    assert "abc-123" in result.content[0].text


@pytest.mark.asyncio
async def test_delete_api_error():
    with patch("rag_mcp_server.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.delete = AsyncMock(side_effect=Exception("Not found"))
        mock_client_cls.return_value = mock_client

        result = await delete_document({"doc_id": "bad-id"})

    assert result.isError is True
    assert "Error deleting document" in result.content[0].text
