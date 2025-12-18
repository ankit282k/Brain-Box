# main.py
from dotenv import load_dotenv
from document_loader import load_documents, load_from_urls
from vector_store import VectorStore
from rag_chain import RAGBot, ConversationalRAGBot
import os

load_dotenv()

def setup_rag_bot(data_path="./data", rebuild_index=False):
    """Setup RAG bot"""
    
    if rebuild_index:
        print("🔄 Rebuilding vector store from scratch...")
        # Delete existing vector store to ensure fresh rebuild
        import shutil
        import time
        
        if os.path.exists("./chroma_db"):
            try:
                # Give time for any connections to close
                time.sleep(0.5)
                shutil.rmtree("./chroma_db")
                print("✅ Cleared old vector store")
                # Wait a bit to ensure folder is fully deleted
                time.sleep(0.5)
            except Exception as e:
                print(f"⚠️ Warning: Could not delete old vector store: {e}")
                print("📝 Proceeding to create new vector store anyway...")
        
        # Create new vector store instance
        vector_store = VectorStore(persist_directory="./chroma_db")
        
        # Load documents from data folder
        documents = load_documents(data_path)
        # Create vector store
        vectorstore = vector_store.create_vectorstore(documents)
    elif not os.path.exists("./chroma_db"):
        print("🆕 Creating new vector store...")
        vector_store = VectorStore(persist_directory="./chroma_db")
        documents = load_documents(data_path)
        vectorstore = vector_store.create_vectorstore(documents)
    else:
        print("📂 Loading existing vector store...")
        vector_store = VectorStore(persist_directory="./chroma_db")
        vectorstore = vector_store.load_vectorstore()
    
    # Create RAG bot
    bot = ConversationalRAGBot(vectorstore)
    
    return bot

def main():
    # Setup bot
    bot = setup_rag_bot(rebuild_index=False)
    
    print("RAG Bot is ready! Type 'quit' to exit.\n")
    
    while True:
        question = input("You: ")
        
        if question.lower() in ['quit', 'exit', 'q']:
            break
        
        result = bot.chat(question)
        
        print(f"\nBot: {result['answer']}\n")
        
        # Optionally show sources
        if result['sources']:
            print("Sources:")
            for i, doc in enumerate(result['sources'][:2], 1):
                print(f"{i}. {doc.metadata.get('source', 'Unknown')}")
            print()

if __name__ == "__main__":
    main()