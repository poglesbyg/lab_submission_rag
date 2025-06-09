from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import shutil
from pathlib import Path

from rag.rag_orchestrator import RAGOrchestrator
from models.submission import LaboratorySubmission

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
    context: Optional[dict] = None

class ProcessResponse(BaseModel):
    submission_id: str
    status: str
    message: str

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
        
        # Process the submission
        submission = LaboratorySubmission(
            source_file=str(file_path),
            metadata={"filename": file.filename}
        )
        
        result = await rag_orchestrator.process_submission(submission)
        
        return ProcessResponse(
            submission_id=str(result.id),
            status="success",
            message="Submission processed successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def query_submission(request: QueryRequest):
    """Query the RAG system with a specific question."""
    try:
        result = await rag_orchestrator.query(
            request.query,
            context=request.context
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"} 
