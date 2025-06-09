"""
RAG-specific models and data structures
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class DocumentChunk(BaseModel):
    """Represents a chunk of processed document"""
    chunk_id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None
    source_document: str
    page_number: Optional[int] = None
    chunk_index: int

class QueryResult(BaseModel):
    """Result of a RAG query"""
    query: str
    relevant_chunks: List[DocumentChunk]
    confidence_scores: List[float]
    generated_response: str
    processing_time: float

class DocumentMetadata(BaseModel):
    """Metadata for processed documents"""
    document_id: str
    filename: str
    file_type: str
    file_size: int
    upload_time: datetime
    processing_time: float
    total_chunks: int
    extraction_status: str
    
class VectorStoreInfo(BaseModel):
    """Information about the vector store"""
    total_documents: int
    total_chunks: int
    embedding_model: str
    last_updated: datetime
    storage_size: int 
