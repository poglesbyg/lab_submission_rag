from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import shutil
from pathlib import Path
import json

# Note: Import paths might need adjustment based on actual structure
# from rag.rag_orchestrator import RAGOrchestrator
# from models.submission import LabSubmission

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

# Mock RAG orchestrator for now - replace with actual implementation
class MockRAGOrchestrator:
    def __init__(self):
        pass
    
    async def process_submission(self, file_path: str) -> Dict[str, Any]:
        """Mock processing that returns the expected format"""
        return {
            "success": True,
            "submission": {
                "administrative_info": {
                    "submitter_first_name": "Dr. Jane",
                    "submitter_last_name": "Smith",
                    "submitter_email": "jane.smith@lab.edu",
                    "submitter_phone": "555-0123",
                    "assigned_project": "PROJ-2024-001"
                },
                "source_material": {
                    "material_type": "Genomic DNA",
                    "extraction_method": "QIAamp DNA Mini Kit",
                    "storage_temperature": "-80C"
                },
                "pooling_info": {
                    "is_pooled": False,
                    "samples_in_pool": [],
                    "pooling_strategy": "None"
                },
                "sequence_generation": {
                    "sequencing_platform": "Illumina NovaSeq",
                    "read_length": "150bp paired-end",
                    "target_coverage": "30x"
                },
                "container_info": {
                    "container_type": "96-well plate",
                    "volume_ul": 50.0,
                    "concentration_ng_ul": 100.0
                },
                "informatics_info": {
                    "analysis_type": "WGS",
                    "reference_genome": "GRCh38",
                    "analysis_pipeline": "GATK"
                },
                "sample_details": {
                    "sample_id": f"SAMPLE-{hash(file_path) % 10000}",
                    "patient_id": "P001",
                    "priority": "High",
                    "quality_score": 8.5
                },
                "submission_id": f"SUB-{hash(file_path) % 10000}",
                "status": "processed",
                "extracted_confidence": 0.92
            },
            "confidence_score": 0.92,
            "missing_fields": [],
            "warnings": [],
            "processing_time": 2.5,
            "source_document": file_path
        }
    
    async def query_submission(self, query: str, submission_id: Optional[str] = None, k: int = 5) -> str:
        """Mock query that returns a reasonable answer"""
        if "sequencing" in query.lower():
            return "The sequencing platform being used is Illumina NovaSeq with 150bp paired-end reads targeting 30x coverage."
        elif "submitter" in query.lower():
            return "The submitter is Dr. Jane Smith from the laboratory."
        elif "storage" in query.lower():
            return "Samples require -80°C storage temperature."
        else:
            return f"Based on the processed documents, I found relevant information for your query: {query}"
    
    def get_system_info(self) -> Dict[str, Any]:
        """Mock system info"""
        return {
            "status": "operational",
            "vector_store": {
                "total_documents": 5,
                "total_chunks": 127,
                "embedding_model": "all-MiniLM-L6-v2"
            },
            "supported_categories": [
                "Administrative Information",
                "Source and Submitting Material", 
                "Pooling (Multiplexing)",
                "Sequence Generation",
                "Container and Diluent",
                "Informatics",
                "Sample Details"
            ]
        }

# Initialize RAG orchestrator
rag_orchestrator = MockRAGOrchestrator()

class QueryRequest(BaseModel):
    query: str
    submission_id: Optional[str] = None
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
        
        # Process the submission using RAG orchestrator
        result = await rag_orchestrator.process_submission(str(file_path))
        
        return RagExtractionResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def query_submission_information(request: QueryRequest):
    """Query the RAG system with a specific question - matches Rust endpoint expectation"""
    try:
        answer = await rag_orchestrator.query_submission(
            query=request.query,
            submission_id=request.submission_id,
            k=request.k or 5
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
        info = rag_orchestrator.get_system_info()
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Legacy endpoint for backward compatibility
@app.post("/process")
async def process_submission_legacy(file: UploadFile = File(...)):
    """Legacy endpoint - redirects to new format"""
    return await process_document_and_create_samples(file) 
