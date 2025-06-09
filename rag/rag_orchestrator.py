"""
RAG orchestrator for coordinating document processing, vector storage, and LLM interactions
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import uuid

from .document_processor import DocumentProcessor
from .vector_store import VectorStore
from .llm_interface import LLMInterface
from models.rag_models import DocumentChunk, ExtractionResult
from models.submission import LabSubmission
from config import settings

logger = logging.getLogger(__name__)

class RAGOrchestrator:
    """Orchestrates the RAG pipeline components"""
    
    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.vector_store = VectorStore()
        self.llm_interface = LLMInterface()
    
    async def process_submission(self, file_path: str) -> ExtractionResult:
        """Process a laboratory submission document"""
        try:
            # Generate unique submission ID
            submission_id = str(uuid.uuid4())
            logger.info(f"Processing submission {submission_id} from {file_path}")
            
            # Process document into chunks
            chunks = await self.document_processor.process_document(file_path)
            if not chunks:
                raise ValueError(f"No valid chunks extracted from {file_path}")
            
            # Add chunks to vector store
            success = await self.vector_store.add_chunks(chunks)
            if not success:
                raise ValueError("Failed to add chunks to vector store")
            
            # Extract submission information using LLM
            extraction_result = await self.llm_interface.extract_submission_info(
                document_chunks=[(chunk.content, 1.0) for chunk in chunks],
                source_document=file_path
            )
            
            # Add submission ID to result
            extraction_result.submission_id = submission_id
            
            logger.info(f"Successfully processed submission {submission_id}")
            return extraction_result
            
        except Exception as e:
            logger.error(f"Error processing submission: {str(e)}")
            return ExtractionResult(
                success=False,
                confidence_score=0.0,
                missing_fields=[],
                warnings=[f"Processing failed: {str(e)}"],
                processing_time=0.0,
                source_document=file_path,
                submission_id=submission_id if 'submission_id' in locals() else None
            )
    
    async def query_submission(
        self, 
        query: str, 
        submission_id: Optional[str] = None,
        k: int = 5
    ) -> str:
        """Query the RAG system about a submission"""
        try:
            # Prepare filter metadata if submission_id is provided
            filter_metadata = {"submission_id": submission_id} if submission_id else None
            
            # Search for relevant chunks
            relevant_chunks = await self.vector_store.similarity_search(
                query=query,
                k=k,
                filter_metadata=filter_metadata
            )
            
            if not relevant_chunks:
                return "No relevant information found."
            
            # Get answer from LLM
            answer = await self.llm_interface.answer_query(
                query=query,
                relevant_chunks=[(chunk.content, score) for chunk, score in relevant_chunks]
            )
            
            return answer
            
        except Exception as e:
            logger.error(f"Error querying submission: {str(e)}")
            return f"Error processing query: {str(e)}"
    
    async def delete_submission(self, submission_id: str) -> bool:
        """Delete a submission from the system"""
        try:
            # Delete from vector store
            success = await self.vector_store.delete_by_source(submission_id)
            if not success:
                raise ValueError(f"Failed to delete submission {submission_id}")
            
            logger.info(f"Successfully deleted submission {submission_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting submission: {str(e)}")
            return False
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get information about the RAG system"""
        try:
            vector_store_info = self.vector_store.get_store_info()
            
            return {
                "vector_store": vector_store_info.dict(),
                "llm_provider": self.llm_interface.client_type,
                "embedding_model": settings.embedding_model,
                "chunk_size": settings.chunk_size,
                "chunk_overlap": settings.chunk_overlap
            }
            
        except Exception as e:
            logger.error(f"Error getting system info: {str(e)}")
            return {
                "error": str(e)
            } 
