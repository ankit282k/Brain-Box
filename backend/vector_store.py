from langchain_openai import AzureOpenAIEmbeddings
from langchain_chroma import Chroma
import os
from dotenv import load_dotenv

load_dotenv()

class VectorStore:
    def __init__(self, persist_directory="./chroma_db"):
        self.embeddings = AzureOpenAIEmbeddings(
            azure_deployment=os.getenv('EMBEDDING_DEPLOYMENT_NAME'),
            api_version=os.getenv("API_VERSION"),
            azure_endpoint=os.getenv("AZURE_ENDPOINT"),
            api_key=os.getenv('AZURE_API_KEY')
        )
        self.persist_directory = persist_directory
        self.vectorstore = None
    
    def create_vectorstore(self, documents):
        """Create and persist vector store"""
        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        # Note: ChromaDB automatically persists data in newer versions
        print(f"Vector store created with {len(documents)} documents")
        return self.vectorstore
    
    def load_vectorstore(self):
        """Load existing vector store"""
        self.vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings
        )
        return self.vectorstore
    
    def similarity_search(self, query, k=4):
        """Search for similar documents"""
        if not self.vectorstore:
            self.load_vectorstore()
        
        return self.vectorstore.similarity_search(query, k=k)