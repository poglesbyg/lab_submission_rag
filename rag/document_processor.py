"""
Document processing component for the RAG system
"""

import asyncio
import aiofiles
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document
import json

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document as LangChainDocument

from models.rag_models import DocumentChunk, DocumentMetadata
from config import settings

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Processes various document types for RAG pipeline"""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
        )
        
    async def process_document(self, file_path: Union[str, Path]) -> List[DocumentChunk]:
        """Process a single document and return chunks"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"File {file_path} does not exist")
            return []

        if file_path.suffix == ".pdf":
            return await self._process_pdf(file_path)
        elif file_path.suffix == ".docx":
            return await self._process_docx(file_path)
        else:
            logger.error(f"Unsupported file type: {file_path.suffix}")
            return []

    async def _process_pdf(self, file_path: Path) -> List[DocumentChunk]:
        """Process a PDF document and return chunks"""
        chunks = []
        with PdfReader(str(file_path)) as pdf_reader:
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    chunks.append(self._create_chunk(text, file_path))
        return chunks

    async def _process_docx(self, file_path: Path) -> List[DocumentChunk]:
        """Process a DOCX document and return chunks"""
        chunks = []
        doc = Document(str(file_path))
        for paragraph in doc.paragraphs:
            text = paragraph.text
            if text:
                chunks.append(self._create_chunk(text, file_path))
        return chunks

    def _create_chunk(self, text: str, file_path: Path) -> DocumentChunk:
        """Create a DocumentChunk from a text and file path"""
        chunk_id = f"{file_path.stem}_{len(self.text_splitter.split_text(text))}"
        chunk_content = self.text_splitter.split_text(text)[0]
        metadata = {
            "file_path": str(file_path),
            "file_type": file_path.suffix[1:],
            "page_number": 1,
            "chunk_index": 0
        }
        return DocumentChunk(
            chunk_id=chunk_id,
            content=chunk_content,
            metadata=metadata,
            embedding=None,
            source_document=str(file_path),
            page_number=1,
            chunk_index=0
        ) 
