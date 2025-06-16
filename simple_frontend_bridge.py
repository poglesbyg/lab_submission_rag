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

class QueryRequest(BaseModel):
    """Request model for queries"""
    query: str
    session_id: Optional[str] = "default"

class QueryResponse(BaseModel):
    """Response model for queries"""
    answer: str

@app.post("/query", response_model=QueryResponse)
async def query_submission_information(request: QueryRequest):
    """Query the RAG system for information about submitted samples"""
    try:
        # For now, provide a helpful response about the lab management system
        # This is a simplified implementation without full RAG capabilities
        
        query_lower = request.query.lower()
        
        # Check if user is asking about lab processes
        if any(word in query_lower for word in ['submit', 'sample', 'lab', 'process', 'upload']):
            answer = """I can help you with laboratory sample management! Here are some key features:

• **Sample Submission**: Upload documents and I'll extract sample information using AI
• **Sample Management**: Create, edit, and track samples with barcodes
• **Storage System**: Manage sample locations and storage conditions
• **Sequencing Jobs**: Set up and track sequencing workflows
• **Templates**: Use Excel templates for batch sample uploads
• **Reports**: Generate custom reports and analytics

To submit samples, you can:
1. Use the RAG document processing feature to upload lab submission forms
2. Manually create samples using the sample creation form
3. Upload Excel templates with sample data

What specific aspect would you like to know more about?"""
        
        elif any(word in query_lower for word in ['storage', 'location', 'temperature']):
            answer = """For sample storage management:

• **Storage Locations**: Create and manage storage locations (freezers, refrigerators, etc.)
• **Temperature Control**: Track storage temperatures (-80°C, -20°C, 4°C, room temp)
• **Barcode Scanning**: Use barcodes to track sample movements
• **Capacity Management**: Monitor storage capacity and utilization
• **Sample Movement**: Log when samples are moved between locations

Storage best practices:
- DNA samples: -20°C or -80°C for long-term storage
- RNA samples: -80°C (very temperature sensitive)
- Protein samples: -80°C with appropriate buffers
- Cell cultures: Liquid nitrogen or -80°C

Would you like help with setting up storage locations or moving samples?"""
        
        elif any(word in query_lower for word in ['sequencing', 'dna', 'rna', 'library']):
            answer = """For sequencing workflows:

• **Sequencing Jobs**: Create jobs with specific protocols and parameters
• **Sample Sheets**: Generate sample sheets for sequencing instruments
• **Quality Control**: Track quality metrics (purity, concentration, integrity)
• **Library Preparation**: Manage library prep protocols and kits
• **Data Analysis**: Configure analysis pipelines and reference genomes

Supported platforms:
- Illumina (MiSeq, NextSeq, NovaSeq)
- Oxford Nanopore (MinION, GridION)
- PacBio (Sequel, Revio)

Quality requirements:
- DNA: A260/A280 ratio 1.8-2.0, concentration >10 ng/μL
- RNA: RIN score >7, concentration >100 ng/μL

Need help setting up a sequencing job or checking sample quality?"""
        
        else:
            # Default helpful response
            answer = f"""Thank you for your question: "{request.query}"

I'm your lab management assistant! I can help you with:

• **Sample Processing**: Submit and manage laboratory samples
• **Document Analysis**: Upload lab forms and extract information automatically  
• **Storage Management**: Track sample locations and conditions
• **Sequencing Workflows**: Set up and monitor sequencing jobs
• **Data Management**: Generate reports and analyze lab data
• **System Navigation**: Guide you through the lab manager interface

Some popular questions:
- "How do I submit a new sample?"
- "What are the storage requirements for DNA samples?"
- "How do I create a sequencing job?"
- "Can you help me generate a sample report?"

What would you like help with today?"""
        
        return QueryResponse(answer=answer)
        
    except Exception as e:
        # Return a helpful error message
        return QueryResponse(
            answer=f"I apologize, but I'm having trouble processing your question right now. This could be due to a temporary system issue. Please try again in a moment, or contact your lab administrator if the problem persists. Error details: {str(e)}"
        )

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
