"""
Configuration settings for the Lab Submission RAG system
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # API Configuration
    api_title: str = "Lab Submission RAG API"
    api_version: str = "1.0.0"
    api_description: str = "RAG system for extracting laboratory submission information"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # Document Processing Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_file_size_mb: int = 50
    supported_file_types: list = [".pdf", ".docx", ".txt"]
    
    # Vector Store Configuration
    vector_db_path: str = "./data/vector_store"
    embedding_model: str = "all-MiniLM-L6-v2"
    similarity_threshold: float = 0.7
    max_search_results: int = 10
    
    # LLM Configuration
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    default_llm_model: str = "gpt-4"
    llm_temperature: float = 0.1
    max_tokens: int = 2000
    
    # Laboratory Domain Configuration
    required_administrative_fields: list = [
        "submitter_first_name", 
        "submitter_last_name", 
        "submitter_email"
    ]
    default_analysis_types: list = ["wgs", "wes", "rna_seq", "targeted_panel"]
    default_sample_types: list = ["blood", "saliva", "tissue", "dna", "rna"]
    
    # Processing Configuration
    batch_size: int = 10
    processing_timeout: int = 300  # seconds
    retry_attempts: int = 3
    
    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "./logs/rag_system.log"
    
    # Storage Configuration  
    data_directory: str = "./data"
    upload_directory: str = "./uploads"
    export_directory: str = "./exports"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Create global settings instance
settings = Settings() 
