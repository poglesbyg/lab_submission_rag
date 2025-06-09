from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import shutil
from pathlib import Path

from rag.rag_orchestrator import RAGOrchestrator
from models.submission import LabSubmission

app = FastAPI(
    title="Laboratory Submission RAG API",
    description="API for processing laboratory submissions using RAG",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG orchestrator
rag_orchestrator = RAGOrchestrator()

class QueryRequest(BaseModel):
    query: str
    submission_id: Optional[str] = None
    k: Optional[int] = 5

class ProcessResponse(BaseModel):
    submission_id: str
    status: str
    message: str
    success: bool
    confidence_score: float

@app.post("/process", response_model=ProcessResponse)
async def process_submission(file: UploadFile = File(...)):
    """Process a laboratory submission document."""
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        file_path = upload_dir / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process the submission using RAG orchestrator
        result = await rag_orchestrator.process_submission(str(file_path))
        
        return ProcessResponse(
            submission_id=result.submission_id or "unknown",
            status="success" if result.success else "failed",
            message="Submission processed successfully" if result.success else "Processing failed",
            success=result.success,
            confidence_score=result.confidence_score
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def query_submission(request: QueryRequest):
    """Query the RAG system with a specific question."""
    try:
        result = await rag_orchestrator.query_submission(
            query=request.query,
            submission_id=request.submission_id,
            k=request.k or 5
        )
        return {"answer": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.get("/system-info")
async def get_system_info():
    """Get information about the RAG system."""
    try:
        info = rag_orchestrator.get_system_info()
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
