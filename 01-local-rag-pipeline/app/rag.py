import uuid
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_community.vectorstores.pgvector import PGVector
from langchain_core.documents import Document
import asyncio
from sqlalchemy import create_engine, Column, String, Integer, text
from sqlalchemy.orm import declarative_base, Session
from pgvector.sqlalchemy import Vector
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/ai_experiments")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

Base = declarative_base()

class DocumentMetadata(Base):
    __tablename__ = "documents"
    id = Column(String, primary_key=True)
    title = Column(String)
    chunk_count = Column(Integer, default=0)

class RAGEngine:
    def __init__(self):
        self.embeddings = None
        self.llm = None
        self.vector_store = None
        self.engine = None
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
        self.engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(self.engine)

        self.vector_store = PGVector(
            embedding_function=self.embeddings,
            collection_name="rag_documents",
            connection_string=DATABASE_URL,
            use_jsonb=True,
        )

    async def cleanup(self):
        """Cleanup resources."""
        if self.engine:
            self.engine.dispose()

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

        with Session(self.engine) as session:
            doc_meta = DocumentMetadata(
                id=doc_id,
                title=title,
                chunk_count=len(chunks)
            )
            session.add(doc_meta)
            session.commit()

        return doc_id

    async def query(self, query: str, top_k: int = 3) -> tuple[str, list]:
        """Query the RAG system."""
        # Retrieve relevant documents
        results = await asyncio.to_thread(
            self.vector_store.similarity_search,
            query,
            k=top_k
        )

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
        with Session(self.engine) as session:
            docs = session.query(DocumentMetadata).all()
            return [
                {
                    "id": doc.id,
                    "title": doc.title,
                    "chunks": doc.chunk_count
                }
                for doc in docs
            ]

    async def delete_document(self, doc_id: str):
        """Delete a document and its chunks."""
        with Session(self.engine) as session:
            session.query(DocumentMetadata).filter(
                DocumentMetadata.id == doc_id
            ).delete()
            session.commit()

        # Delete from vector store
        await asyncio.to_thread(
            self.vector_store.delete,
            filter={"doc_id": doc_id}
        )
