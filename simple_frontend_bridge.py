#!/usr/bin/env python3
"""
Simple Frontend API Bridge for RAG Submissions
Provides basic API endpoints that the lab_manager frontend needs
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import asyncpg
import uuid
from datetime import datetime

app = FastAPI(
    title="Simple RAG Submissions API Bridge",
    description="Basic API bridge for lab_manager frontend to access RAG submissions",
    version="1.0.0"
)

# Enable CORS for lab_manager frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
DB_CONFIG = {
    'host': 'postgres',
    'port': 5432,
    'database': 'lab_manager',
    'user': 'postgres',
    'password': 'postgres'
}

class RagSubmissionResponse(BaseModel):
    """Response model for RAG submissions"""
    id: str
    submission_id: str
    submitter_name: Optional[str]
    submitter_email: Optional[str]
    sample_type: Optional[str]
    sample_name: Optional[str]
    confidence_score: float
    created_at: str
    status: str = "completed"

async def get_db_connection():
    """Get database connection"""
    return await asyncpg.connect(**DB_CONFIG)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Simple RAG Submissions API Bridge", "status": "operational"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        conn = await get_db_connection()
        await conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {e}")

@app.get("/api/rag/submissions", response_model=List[RagSubmissionResponse])
async def get_rag_submissions(limit: int = 50, offset: int = 0):
    """Get RAG submissions for the frontend"""
    try:
        conn = await get_db_connection()
        
        # Query RAG submissions from database
        submissions = await conn.fetch("""
            SELECT 
                submission_id,
                submitter_name,
                submitter_email,
                sample_type,
                document_name,
                confidence_score,
                created_at
            FROM rag_submissions 
            ORDER BY created_at DESC 
            LIMIT $1 OFFSET $2
        """, limit, offset)
        
        await conn.close()
        
        # Convert to response format
        result = []
        for row in submissions:
            result.append(RagSubmissionResponse(
                id=str(uuid.uuid4())[:8],  # Short ID for display
                submission_id=row['submission_id'],
                submitter_name=row['submitter_name'],
                submitter_email=row['submitter_email'],
                sample_type=row['sample_type'] or "Unknown",
                sample_name=row['document_name'],
                confidence_score=row['confidence_score'] or 0.0,
                created_at=row['created_at'].isoformat() if row['created_at'] else "",
                status="completed"
            ))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch submissions: {e}")

@app.get("/api/rag/stats")
async def get_rag_statistics():
    """Get RAG system statistics"""
    try:
        conn = await get_db_connection()
        
        # Get submission counts
        total_submissions = await conn.fetchval("SELECT COUNT(*) FROM rag_submissions")
        
        # Get recent activity
        recent_count = await conn.fetchval("""
            SELECT COUNT(*) FROM rag_submissions 
            WHERE created_at >= NOW() - INTERVAL '7 days'
        """)
        
        # Get average confidence
        avg_confidence = await conn.fetchval("""
            SELECT AVG(confidence_score) FROM rag_submissions 
            WHERE confidence_score > 0
        """)
        
        await conn.close()
        
        return {
            "total_submissions": total_submissions or 0,
            "recent_submissions": recent_count or 0,
            "average_confidence": float(avg_confidence or 0.0),
            "status": "operational"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {e}")

@app.post("/api/rag/process")
async def process_document():
    """Placeholder for document processing"""
    return {
        "success": False,
        "message": "Document processing not implemented in simple bridge",
        "processing_time": 0.0
    }

# Startup event to test database connection
@app.on_event("startup")
async def startup_event():
    """Test database connection on startup"""
    try:
        conn = await get_db_connection()
        await conn.close()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Simple RAG Submissions API Bridge")
    print("📡 Providing basic RAG data access for frontend")
    print("🌐 CORS enabled for all origins")
    
    uvicorn.run(app, host="0.0.0.0", port=8000) 
