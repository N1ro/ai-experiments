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
            model="nomic-embed-text",
            base_url=OLLAMA_BASE_URL,
        )
        self.llm = OllamaLLM(
            model="qwen3:14b",
            base_url=OLLAMA_BASE_URL,
        )
        self.vector_store = Chroma(
            embedding_function=self.embeddings,
            collection_name="rag_documents",
            persist_directory=CHROMA_DB_PATH,
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

    async def query(self, query: str, top_k: int = 3) -> tuple[str, list]:
        """Query the RAG system."""
        # Retrieve relevant documents with scores
        results = await asyncio.to_thread(
            self.vector_store.similarity_search_with_score,
            query,
            k=top_k
        )

        if not results:
            return "No documents found in the knowledge base. Please ingest documents first.", []

        # Separate docs and scores, sort by score (higher is better)
        docs_with_scores = [(doc, score) for doc, score in results]
        docs_with_scores.sort(key=lambda x: x[1], reverse=True)
        results = [doc for doc, _ in docs_with_scores]

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

        # Recreate the collection
        self.vector_store = Chroma(
            embedding_function=self.embeddings,
            collection_name="rag_documents",
            persist_directory=CHROMA_DB_PATH,
        )

        # Clear metadata
        self.documents_meta.clear()
