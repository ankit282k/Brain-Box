import os
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    DirectoryLoader,
    WebBaseLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter

def load_documents(data_path):
    """Load documents from various sources"""
    
    # Load PDFs
    pdf_loader = DirectoryLoader(
        data_path, 
        glob="**/*.pdf", 
        loader_cls=PyPDFLoader
    )
    
    # Load text files
    text_loader = DirectoryLoader(
        data_path, 
        glob="**/*.txt", 
        loader_cls=TextLoader
    )
    
    documents = pdf_loader.load() + text_loader.load()
    
    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"Loaded {len(documents)} documents, split into {len(chunks)} chunks")
    
    return chunks

# Load web pages
def load_from_urls(urls):
    """Load content from URLs"""
    loader = WebBaseLoader(urls)
    documents = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    
    return text_splitter.split_documents(documents)