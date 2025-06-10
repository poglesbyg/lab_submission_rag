from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import shutil
from pathlib import Path
import json

# Import the actual RAG system
from rag_orchestrator import rag_system
from models.submission import LabSubmission, ExtractionResult

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

# Use the actual RAG system
# rag_system is already initialized in rag_orchestrator.py

class QueryRequest(BaseModel):
    query: str
    submission_id: Optional[str] = None
    session_id: Optional[str] = "default"
    k: Optional[int] = 5

# Updated response models to match Rust expectations
class RagExtractionResult(BaseModel):
    success: bool
    submission: Optional[Dict[str, Any]] = None
    confidence_score: float
    missing_fields: List[str] = []
    warnings: List[str] = []
    processing_time: float
    source_document: str

class QueryResponse(BaseModel):
    answer: str

# Updated endpoints to match Rust expectations
@app.post("/process-document", response_model=RagExtractionResult)
async def process_document_and_create_samples(file: UploadFile = File(...)):
    """Process a laboratory submission document - matches Rust endpoint expectation"""
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        file_path = upload_dir / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process the submission using RAG system
        result = await rag_system.process_document(str(file_path))
        
        # Convert ExtractionResult to dictionary format expected by frontend
        response_dict = {
            "success": result.success,
            "confidence_score": result.confidence_score or 0.0,
            "missing_fields": result.missing_fields or [],
            "warnings": result.warnings or [],
            "processing_time": result.processing_time,
            "source_document": result.source_document
        }
        
        # Add submission data if extraction was successful
        if result.success and result.submission:
            response_dict["submission"] = result.submission.dict()
        
        return RagExtractionResult(**response_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def query_submission_information(request: QueryRequest):
    """Query the RAG system with a specific question - matches Rust endpoint expectation"""
    try:
        answer = await rag_system.query_submissions(
            query=request.query,
            filter_metadata={"submission_id": request.submission_id} if request.submission_id else None,
            session_id=request.session_id or "default"
        )
        return QueryResponse(answer=answer)
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
        info = await rag_system.get_system_status()
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Legacy endpoint for backward compatibility
@app.post("/process")
async def process_submission_legacy(file: UploadFile = File(...)):
    """Legacy endpoint - redirects to new format"""
    return await process_document_and_create_samples(file) 
