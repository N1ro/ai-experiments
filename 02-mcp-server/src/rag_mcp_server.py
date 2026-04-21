#!/usr/bin/env python3
"""MCP server that wraps the RAG pipeline."""

import asyncio
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, CallToolResult
import sys

RAG_API_URL = "http://localhost:8000"

server = Server("rag-mcp-server")

@server.call_tool()
async def handle_tool_call(name: str, arguments: dict) -> CallToolResult:
    """Handle tool calls from Claude."""
    if name == "query_knowledge_base":
        return await query_knowledge_base(arguments)
    elif name == "ingest_document":
        return await ingest_document(arguments)
    elif name == "list_documents":
        return await list_documents(arguments)
    elif name == "delete_document":
        return await delete_document(arguments)
    else:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Unknown tool: {name}")],
            isError=True,
        )

async def query_knowledge_base(arguments: dict) -> CallToolResult:
    """Query the RAG knowledge base."""
    query = arguments.get("query")
    top_k = arguments.get("top_k", 3)

    if not query:
        return CallToolResult(
            content=[TextContent(type="text", text="Query is required")],
            isError=True,
        )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{RAG_API_URL}/query",
                json={"query": query, "top_k": top_k},
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()

            answer = data.get("answer", "No answer generated")
            sources = data.get("sources", [])

            # Format response
            result = f"Answer:\n{answer}\n\nSources:\n"
            for i, source in enumerate(sources, 1):
                result += f"{i}. {source['title']} (ID: {source['doc_id']})\n"
                result += f"   {source['content'][:100]}...\n"

            return CallToolResult(
                content=[TextContent(type="text", text=result)],
                isError=False,
            )
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error querying RAG: {str(e)}")],
            isError=True,
        )

async def ingest_document(arguments: dict) -> CallToolResult:
    """Ingest a document from URL or text."""
    url = arguments.get("url")
    title = arguments.get("title", "untitled")
    content = arguments.get("content")

    if url:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()
                content = response.text
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error fetching URL: {str(e)}")],
                isError=True,
            )
    elif not content:
        return CallToolResult(
            content=[TextContent(type="text", text="Either URL or content is required")],
            isError=True,
        )

    try:
        async with httpx.AsyncClient() as client:
            # Create temporary file and upload
            files = {"files": (title, content.encode())}
            response = await client.post(
                f"{RAG_API_URL}/ingest",
                files=files,
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()

            result_text = f"Ingested '{title}'\n"
            for doc in data.get("documents", []):
                result_text += f"Doc ID: {doc.get('doc_id')}\n"

            return CallToolResult(
                content=[TextContent(type="text", text=result_text)],
                isError=False,
            )
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error ingesting document: {str(e)}")],
            isError=True,
        )

async def list_documents(arguments: dict) -> CallToolResult:
    """List all documents in the knowledge base."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{RAG_API_URL}/documents", timeout=10.0)
            response.raise_for_status()
            docs = response.json()

            if not docs:
                return CallToolResult(
                    content=[TextContent(type="text", text="No documents indexed yet")],
                    isError=False,
                )

            result = "Indexed Documents:\n"
            for doc in docs:
                result += f"- {doc['title']} (ID: {doc['id']}, chunks: {doc['chunks']})\n"

            return CallToolResult(
                content=[TextContent(type="text", text=result)],
                isError=False,
            )
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error listing documents: {str(e)}")],
            isError=True,
        )

async def delete_document(arguments: dict) -> CallToolResult:
    """Delete a document from the knowledge base."""
    doc_id = arguments.get("doc_id")

    if not doc_id:
        return CallToolResult(
            content=[TextContent(type="text", text="doc_id is required")],
            isError=True,
        )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{RAG_API_URL}/documents/{doc_id}", timeout=10.0)
            response.raise_for_status()
            return CallToolResult(
                content=[TextContent(type="text", text=f"Deleted document {doc_id}")],
                isError=False,
            )
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error deleting document: {str(e)}")],
            isError=True,
        )

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="query_knowledge_base",
            description="Query the local RAG knowledge base with semantic search",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"},
                    "top_k": {"type": "integer", "description": "Number of top results (default: 3)", "default": 3},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="ingest_document",
            description="Add a document to the knowledge base",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Document title"},
                    "content": {"type": "string", "description": "Document content (alternative to URL)"},
                    "url": {"type": "string", "description": "URL to fetch document from"},
                },
                "required": ["title"],
            },
        ),
        Tool(
            name="list_documents",
            description="List all documents in the knowledge base",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="delete_document",
            description="Delete a document from the knowledge base",
            inputSchema={
                "type": "object",
                "properties": {
                    "doc_id": {"type": "string", "description": "Document ID to delete"},
                },
                "required": ["doc_id"],
            },
        ),
    ]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        print("RAG MCP Server running on stdio", file=sys.stderr)
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
