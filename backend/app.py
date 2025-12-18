from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uvicorn
from datetime import datetime
import logging
import os
import shutil
from pathlib import Path
from main import setup_rag_bot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Brain Box API",
    description="Retrieval-Augmented Generation Chat Bot API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Global bot instance
bot = None
bot_loaded = False

# Data directory configuration
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.docx', '.doc', '.csv', '.xlsx', '.xls', '.json', '.md'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

class Question(BaseModel):
    question: str = Field(..., min_length=1, description="User's question")
    session_id: Optional[str] = Field(None, description="Session identifier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "What is the main topic of the document?",
                "session_id": "user123"
            }
        }

class Source(BaseModel):
    source: str = Field(..., description="Source reference")
    content: Optional[str] = Field(None, description="Source content snippet")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ChatResponse(BaseModel):
    answer: str = Field(..., description="Bot's answer")
    sources: List[str] = Field(default_factory=list, description="List of sources")
    timestamp: str = Field(..., description="Response timestamp")
    session_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "The main topic is...",
                "sources": ["document1.pdf", "document2.txt"],
                "timestamp": "2024-01-01T12:00:00",
                "session_id": "user123"
            }
        }

class HealthResponse(BaseModel):
    status: str
    bot_loaded: bool
    timestamp: str
    version: str

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: str

class UploadResponse(BaseModel):
    message: str
    filename: str
    file_size: int
    file_path: str
    timestamp: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "File uploaded successfully",
                "filename": "document.pdf",
                "file_size": 102400,
                "file_path": "data/document.pdf",
                "timestamp": "2024-01-01T12:00:00"
            }
        }

@app.on_event("startup")
async def startup_event():
    """Initialize the RAG bot on startup"""
    global bot, bot_loaded
    try:
        logger.info("🚀 Starting RAG Bot initialization...")
        bot = setup_rag_bot()
        bot_loaded = True
        logger.info("✅ RAG Bot initialized successfully!")
    except Exception as e:
        logger.error(f"❌ Failed to initialize RAG Bot: {str(e)}")
        bot_loaded = False

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("👋 Shutting down RAG Bot API...")

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "RAG Bot API is running",
        "version": "1.0.0",
        "status": "active",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if bot_loaded else "unhealthy",
        bot_loaded=bot_loaded,
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )

@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(question: Question, background_tasks: BackgroundTasks):
    """
    Main chat endpoint
    
    - **question**: User's question (required)
    - **session_id**: Optional session identifier for tracking
    """
    if not bot_loaded or bot is None:
        raise HTTPException(
            status_code=503,
            detail="Bot is not initialized. Please try again later."
        )
    
    if not question.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )
    
    try:
        logger.info(f"📝 Processing question: {question.question[:50]}...")
        
        # Get response from bot with session management
        result = bot.chat(question.question, session_id=question.session_id)
        
        # Extract sources
        sources = [
            doc.metadata.get('source', 'Unknown')
            for doc in result.get('sources', [])
        ]
        
        # Remove duplicates while preserving order
        sources = list(dict.fromkeys(sources))
        
        logger.info(f"✅ Generated answer with {len(sources)} sources")
        
        return ChatResponse(
            answer=result['answer'],
            sources=sources,
            timestamp=datetime.now().isoformat(),
            session_id=question.session_id
        )
        
    except Exception as e:
        logger.error(f"❌ Error processing question: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/chat/detailed", tags=["Chat"])
async def chat_detailed(question: Question):
    """
    Chat endpoint with detailed source information
    """
    if not bot_loaded or bot is None:
        raise HTTPException(
            status_code=503,
            detail="Bot is not initialized"
        )
    
    try:
        result = bot.chat(question.question)
        
        # Extract detailed sources
        sources = []
        for doc in result.get('sources', []):
            sources.append({
                "source": doc.metadata.get('source', 'Unknown'),
                "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                "metadata": doc.metadata
            })
        
        return {
            "answer": result['answer'],
            "sources": sources,
            "timestamp": datetime.now().isoformat(),
            "session_id": question.session_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats", tags=["Statistics"])
async def get_stats():
    """Get API statistics"""
    return {
        "bot_loaded": bot_loaded,
        "timestamp": datetime.now().isoformat(),
        "status": "operational"
    }

@app.post("/upload", response_model=UploadResponse, tags=["Upload"])
async def upload_document(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """
    Upload a document to the data folder and automatically reload the knowledge base
    
    - **file**: Document file to upload
    - Supported formats: PDF, TXT, DOCX, DOC, CSV, XLSX, XLS, JSON, MD
    - Max file size: 50 MB
    """
    global bot, bot_loaded
    
    try:
        # Validate file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not allowed. Supported types: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Validate file size
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size {file_size / 1024 / 1024:.2f} MB exceeds maximum allowed size of {MAX_FILE_SIZE / 1024 / 1024:.0f} MB"
            )
        
        if file_size == 0:
            raise HTTPException(
                status_code=400,
                detail="File is empty"
            )
        
        # Generate safe filename (avoid overwriting existing files)
        base_filename = Path(file.filename).stem
        file_extension = Path(file.filename).suffix
        counter = 1
        safe_filename = file.filename
        file_path = DATA_DIR / safe_filename
        
        # If file exists, add a counter
        while file_path.exists():
            safe_filename = f"{base_filename}_{counter}{file_extension}"
            file_path = DATA_DIR / safe_filename
            counter += 1
        
        # Save file to data directory
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        logger.info(f"✅ File uploaded successfully: {safe_filename} ({file_size / 1024:.2f} KB)")
        
        # Automatically reload documents to update the knowledge base
        logger.info("🔄 Auto-reloading documents to update knowledge base...")
        bot_loaded = False
        
        try:
            # Release old bot reference to close connections
            old_bot = bot
            bot = None
            del old_bot
            
            # Force garbage collection to close file handles
            import gc
            gc.collect()
            
            # Small delay to ensure cleanup
            import time
            time.sleep(1)
            
            # Now rebuild
            bot = setup_rag_bot(data_path="./data", rebuild_index=True)
            bot_loaded = True
            logger.info("✅ Knowledge base updated successfully")
        except Exception as reload_error:
            logger.error(f"⚠️ File uploaded but failed to reload: {str(reload_error)}")
            bot_loaded = False
        
        return UploadResponse(
            message=f"File uploaded and knowledge base updated successfully with {safe_filename}",
            filename=safe_filename,
            file_size=file_size,
            file_path=str(file_path),
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading file: {str(e)}"
        )

@app.post("/reload", tags=["Upload"])
async def reload_documents():
    """
    Reload all documents from data folder and rebuild the vector store
    
    This endpoint processes all documents in the data folder and updates the knowledge base.
    Use this after uploading new documents.
    """
    global bot, bot_loaded
    
    try:
        logger.info("🔄 Reloading documents and rebuilding vector store...")
        bot_loaded = False
        
        # Release old bot reference to close connections
        old_bot = bot
        bot = None
        del old_bot
        
        # Force garbage collection to close file handles
        import gc
        gc.collect()
        
        # Small delay to ensure cleanup
        import time
        time.sleep(1)
        
        # Rebuild the bot with all documents in data folder
        bot = setup_rag_bot(data_path="./data", rebuild_index=True)
        bot_loaded = True
        
        # Count files in data folder
        file_count = len(list(DATA_DIR.glob('*.*')))
        
        logger.info(f"✅ Successfully reloaded {file_count} documents")
        
        return {
            "message": f"Successfully reloaded and processed {file_count} documents",
            "timestamp": datetime.now().isoformat(),
            "bot_loaded": True
        }
        
    except Exception as e:
        logger.error(f"❌ Error reloading documents: {str(e)}")
        bot_loaded = False
        raise HTTPException(
            status_code=500,
            detail=f"Error reloading documents: {str(e)}"
        )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "timestamp": datetime.now().isoformat()
    }

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return {
        "error": "Internal server error",
        "detail": str(exc),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
