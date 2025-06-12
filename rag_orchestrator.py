"""
RAG Orchestrator for Laboratory Submission Information Extraction
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from rag.document_processor import DocumentProcessor
from rag.vector_store import VectorStore
from rag.llm_interface import LLMInterface
from rag.enhanced_llm_interface import enhanced_llm
from models.submission import LabSubmission, ExtractionResult, BatchExtractionResult
from config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LabSubmissionRAG:
    """
    Main RAG system for extracting laboratory submission information from documents.
    
    This system can:
    1. Process laboratory documents (PDF, DOCX, TXT)
    2. Extract information across 7 categories using LLM
    3. Answer questions about submissions
    4. Store and retrieve submission data
    """
    
    def __init__(self):
        """Initialize the RAG system components"""
        logger.info("Initializing Lab Submission RAG system...")
        
        # Initialize components
        self.document_processor = DocumentProcessor()
        self.vector_store = VectorStore()
        self.llm_interface = LLMInterface()
        
        # Initialize enhanced LLM for queries
        from rag.enhanced_llm_interface import enhanced_llm
        self.enhanced_llm = enhanced_llm
        
        # Create necessary directories
        self._ensure_directories()
        
        logger.info("Lab Submission RAG system initialized successfully")
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            settings.vector_store_path,
            settings.upload_dir,
            settings.export_dir,
            settings.log_dir
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    async def process_document(self, file_path: Union[str, Path]) -> ExtractionResult:
        """
        Process a single laboratory document and extract submission information.
        
        Args:
            file_path: Path to the document to process
            
        Returns:
            ExtractionResult containing extracted submission information
        """
        start_time = time.time()
        file_path = Path(file_path)
        
        logger.info(f"Processing document: {file_path}")
        
        try:
            # Step 1: Process document into chunks
            logger.info(f"Starting document processing for {file_path}")
            document_chunks = await self.document_processor.process_document(file_path)
            logger.info(f"Document processor returned {len(document_chunks)} chunks")
            
            if not document_chunks:
                logger.warning(f"No chunks extracted from {file_path}")
                return ExtractionResult(
                    success=False,
                    confidence_score=0.0,
                    missing_fields=[],
                    warnings=["No content could be extracted from document"],
                    processing_time=time.time() - start_time,
                    source_document=str(file_path)
                )
            
            # Log chunk details
            for i, chunk in enumerate(document_chunks):
                logger.debug(f"Chunk {i}: ID={chunk.chunk_id}, content_length={len(chunk.content)}")
            
            # Step 2: Add chunks to vector store
            logger.info(f"Adding {len(document_chunks)} chunks to vector store")
            await self.vector_store.add_chunks(document_chunks)
            
            # Step 3: Search for relevant chunks for each category
            logger.info("Getting relevant chunks for extraction")
            relevant_chunks = await self._get_relevant_chunks_for_extraction(str(file_path))
            logger.info(f"Found {len(relevant_chunks)} relevant chunks")
            
            # Step 4: Extract submission information using LLM
            logger.info("Starting LLM extraction")
            extraction_result = await self.llm_interface.extract_submission_info(
                relevant_chunks, str(file_path)
            )
            logger.info(f"LLM extraction completed. Success: {extraction_result.success}")
            
            # Update processing time
            extraction_result.processing_time = time.time() - start_time
            
            logger.info(f"Document processing completed. Success: {extraction_result.success}, "
                       f"Confidence: {extraction_result.confidence_score:.2f}")
            
            return extraction_result
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {str(e)}")
            return ExtractionResult(
                success=False,
                confidence_score=0.0,
                missing_fields=[],
                warnings=[f"Processing error: {str(e)}"],
                processing_time=time.time() - start_time,
                source_document=str(file_path)
            )
    
    async def process_documents_batch(self, file_paths: List[Union[str, Path]]) -> BatchExtractionResult:
        """
        Process multiple laboratory documents in batch.
        
        Args:
            file_paths: List of document paths to process
            
        Returns:
            BatchExtractionResult containing results for all documents
        """
        start_time = time.time()
        logger.info(f"Starting batch processing of {len(file_paths)} documents")
        
        results = []
        successful_extractions = 0
        
        # Process documents in batches to avoid overwhelming the system
        for i in range(0, len(file_paths), settings.batch_size):
            batch = file_paths[i:i + settings.batch_size]
            batch_tasks = [self.process_document(file_path) for file_path in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch processing error: {str(result)}")
                    results.append(ExtractionResult(
                        success=False,
                        confidence_score=0.0,
                        missing_fields=[],
                        warnings=[f"Batch processing error: {str(result)}"],
                        processing_time=0.0,
                        source_document="unknown"
                    ))
                else:
                    results.append(result)
                    if result.success:
                        successful_extractions += 1
        
        # Calculate overall confidence
        successful_results = [r for r in results if r.success]
        overall_confidence = (
            sum(r.confidence_score for r in successful_results) / len(successful_results)
            if successful_results else 0.0
        )
        
        processing_time = time.time() - start_time
        
        logger.info(f"Batch processing completed. {successful_extractions}/{len(file_paths)} successful")
        
        return BatchExtractionResult(
            total_documents=len(file_paths),
            successful_extractions=successful_extractions,
            failed_extractions=len(file_paths) - successful_extractions,
            results=results,
            overall_confidence=overall_confidence,
            processing_time=processing_time
        )
    
    async def query_submissions(self, query: str, filter_metadata: Optional[Dict[str, Any]] = None, session_id: str = "default") -> str:
        """
        Answer questions about laboratory submissions using enhanced RAG intelligence.
        
        Args:
            query: Natural language query about submissions
            filter_metadata: Optional metadata filters for search
            session_id: Session ID for conversation context
            
        Returns:
            Natural language answer based on stored submission data and enhanced intelligence
        """
        logger.info(f"Processing enhanced query: {query}")
        
        try:
            # Search for relevant chunks
            relevant_chunks = await self.vector_store.similarity_search(
                query, 
                k=settings.max_search_results if hasattr(settings, 'max_search_results') else 5,
                filter_metadata=filter_metadata
            )
            
            # Convert to format expected by enhanced LLM interface
            chunks_with_scores = [(chunk.content, score) for chunk, score in relevant_chunks]
            
            # Get enhanced answer from improved LLM interface
            answer = await self.enhanced_llm.answer_query(
                query, 
                chunks_with_scores, 
                session_id=session_id,
                submission_data=None  # Could add submission context here
            )
            
            logger.info("Enhanced query processed successfully")
            return answer
            
        except Exception as e:
            logger.error(f"Error processing enhanced query: {str(e)}")
            return f"I apologize, but I encountered an error while processing your query. Please try rephrasing your question or contact support if the issue persists."
    
    async def _get_relevant_chunks_for_extraction(self, source_document: str) -> List[tuple]:
        """Get relevant chunks for information extraction from a specific document"""
        # Define search queries for each category
        category_queries = [
            "submitter name email phone contact administrative information",
            "source material DNA RNA genomic biological sample type",
            "pooling multiplexing barcode index sequences",
            "sequencing platform read length coverage library preparation",
            "container tube volume concentration diluent storage",
            "informatics analysis pipeline reference genome computational",
            "sample details quality metrics priority patient identifier"
        ]
        
        all_relevant_chunks = []
        
        for query in category_queries:
            chunks = await self.vector_store.similarity_search(
                query,
                k=3,
                filter_metadata={"source_document": source_document}
            )
            
            # Add chunks with their similarity scores
            for chunk, score in chunks:
                if score >= settings.similarity_threshold:
                    all_relevant_chunks.append((chunk.content, score))
        
        # Remove duplicates and sort by relevance
        unique_chunks = {}
        for content, score in all_relevant_chunks:
            if content not in unique_chunks or score > unique_chunks[content]:
                unique_chunks[content] = score
        
        # Return top chunks sorted by score
        sorted_chunks = sorted(unique_chunks.items(), key=lambda x: x[1], reverse=True)
        return sorted_chunks[:10]  # Limit to top 10 most relevant chunks
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get status information about the RAG system"""
        try:
            vector_store_info = self.vector_store.get_store_info()
            
            return {
                "status": "operational",
                "vector_store": {
                    "total_documents": vector_store_info.total_documents,
                    "total_chunks": vector_store_info.total_chunks,
                    "embedding_model": vector_store_info.embedding_model,
                    "last_updated": vector_store_info.last_updated.isoformat()
                },
                "configuration": {
                    "chunk_size": settings.chunk_size,
                    "chunk_overlap": settings.chunk_overlap,
                    "similarity_threshold": settings.similarity_threshold,
                    "max_search_results": settings.max_search_results
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
            
        except Exception as e:
            logger.error(f"Error getting system status: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def export_submission_data(
        self, 
        submission: LabSubmission, 
        format: str = "json"
    ) -> str:
        """
        Export extracted submission data to file.
        
        Args:
            submission: The LabSubmission object to export
            format: Export format ('json', 'csv', 'xlsx')
            
        Returns:
            Path to the exported file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_dir = Path(settings.export_directory)
            
            if format == "json":
                export_path = export_dir / f"submission_{timestamp}.json"
                with open(export_path, 'w') as f:
                    f.write(submission.json(indent=2))
                    
            elif format == "csv":
                import pandas as pd
                export_path = export_dir / f"submission_{timestamp}.csv"
                
                # Flatten the submission data for CSV export
                flat_data = {}
                for category, data in submission.dict().items():
                    if isinstance(data, dict):
                        for key, value in data.items():
                            flat_data[f"{category}_{key}"] = value
                    else:
                        flat_data[category] = data
                
                df = pd.DataFrame([flat_data])
                df.to_csv(export_path, index=False)
                
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            logger.info(f"Submission data exported to {export_path}")
            return str(export_path)
            
        except Exception as e:
            logger.error(f"Error exporting submission data: {str(e)}")
            raise

# Create global RAG instance
rag_system = LabSubmissionRAG() 
 