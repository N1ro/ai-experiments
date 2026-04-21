import uuid
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
import asyncio
import os
import shutil

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")

class RAGEngine:
    def __init__(self):
        self.embeddings = None
        self.llm = None
        self.vector_store = None
        self.documents_meta = {}
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
        )

    async def init(self):
        """Initialize RAG components."""
        self.embeddings = OllamaEmbeddings(
            model="mxbai-embed-large",
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )
        self.llm = OllamaLLM(
            model="qwen3:14b",
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )
        self.vector_store = Chroma(
            embedding_function=self.embeddings,
            collection_name=os.getenv("CHROMA_COLLECTION_NAME", "rag_documents"),
            persist_directory=os.getenv("CHROMA_DB_PATH", "./chroma_db"),
        )

    async def cleanup(self):
        """Cleanup resources."""
        if self.vector_store:
            self.vector_store.persist()

    async def ingest(self, title: str, content: str) -> str:
        """Ingest a document."""
        doc_id = str(uuid.uuid4())

        chunks = self.text_splitter.split_text(content)
        documents = [
            Document(
                page_content=chunk,
                metadata={"doc_id": doc_id, "title": title, "chunk_index": i}
            )
            for i, chunk in enumerate(chunks)
        ]

        await asyncio.to_thread(
            self.vector_store.add_documents,
            documents
        )

        # Store metadata in memory
        self.documents_meta[doc_id] = {
            "title": title,
            "chunk_count": len(chunks)
        }

        return doc_id

    async def query(self, query: str, top_k: int = 3, similarity_threshold: float = 0.5) -> tuple[str, list]:
        """Query the RAG system.

        Args:
            query: The search query
            top_k: Maximum number of documents to retrieve
            similarity_threshold: Minimum similarity score to include a document (0-1)
        """
        # Retrieve more results than needed to re-rank
        results = await asyncio.to_thread(
            self.vector_store.similarity_search,
            query,
            k=top_k * 2
        )

        if not results:
            return "No documents found in the knowledge base. Please ingest documents first.", []

        # Re-rank by manually computing cosine similarity
        import numpy as np

        query_embedding = await asyncio.to_thread(
            self.embeddings.embed_query,
            query
        )

        # Compute similarities for each result
        scored_results = []
        for doc in results:
            doc_embedding = await asyncio.to_thread(
                self.embeddings.embed_query,
                doc.page_content
            )
            # Cosine similarity
            similarity = np.dot(query_embedding, doc_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
            )
            scored_results.append((doc, similarity))

        # Sort by similarity (highest first)
        scored_results.sort(key=lambda x: x[1], reverse=True)

        # DEBUG: Show scores
        print(f"\n[DEBUG] Query: '{query}' - Similarity scores (threshold: {similarity_threshold}):")
        for doc, score in scored_results:
            status = "✓" if score >= similarity_threshold else "✗"
            print(f"  {doc.metadata.get('title')}: {score:.4f} {status}")

        # Filter by similarity threshold and limit to top_k
        results = [doc for doc, score in scored_results if score >= similarity_threshold][:top_k]

        if not results:
            return f"No documents found matching your query. Please try a different search or check the knowledge base.", []

        context = "\n\n".join([doc.page_content for doc in results])

        # Generate answer
        prompt = f"""Based on the following context, answer the question.

Context:
{context}

Question: {query}

Answer:"""

        answer = await asyncio.to_thread(self.llm.invoke, prompt)

        sources = [
            {
                "doc_id": doc.metadata.get("doc_id"),
                "title": doc.metadata.get("title"),
                "content": doc.page_content[:200]  # First 200 chars
            }
            for doc in results
        ]

        return answer, sources

    async def list_documents(self) -> list[dict]:
        """List all documents."""
        return [
            {
                "id": doc_id,
                "title": data["title"],
                "chunks": data["chunk_count"]
            }
            for doc_id, data in self.documents_meta.items()
        ]

    async def delete_document(self, doc_id: str):
        """Delete a document and its chunks."""
        # Delete from vector store
        collection = self.vector_store._collection
        await asyncio.to_thread(
            collection.delete,
            where={"doc_id": {"$eq": doc_id}}
        )

        # Remove from metadata
        if doc_id in self.documents_meta:
            del self.documents_meta[doc_id]

    async def delete_all_documents(self):
        """Delete all documents from the index."""
        # Delete the entire collection and recreate it
        await asyncio.to_thread(
            self.vector_store.delete_collection
        )

        # Recreate the collection using the same runtime settings
        self.vector_store = Chroma(
            embedding_function=self.embeddings,
            collection_name=os.getenv("CHROMA_COLLECTION_NAME", "rag_documents"),
            persist_directory=os.getenv("CHROMA_DB_PATH", "./chroma_db"),
        )

        # Clear metadata
        self.documents_meta.clear()
