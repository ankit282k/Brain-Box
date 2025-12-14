from langchain_postgres import PGVector
from app.llm import embeddings
import os
from langchain_community.vectorstores import PGVector
from langchain_core.documents import Document

DB_URL = os.environ.get("PGVECTOR_CONNECTION_STRING")

docs = [
    Document(page_content="pgvector enables vector similarity search in PostgreSQL"),
    Document(page_content="LangChain helps build LLM applications"),
    Document(page_content="FastAPI is a modern Python web framework"),
]

vectorstore = PGVector.from_documents(
    documents=docs,
    embedding=embeddings,
    collection_name="docs",
    connection=DB_URL,
)