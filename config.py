"""
Configuration settings for the RAG system
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings"""
    
    # API Keys (optional when using Ollama)
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic API key")
    
    # LLM Settings
    llm_provider: str = Field(
        default="openai",
        description="LLM provider to use (openai, anthropic, ollama)"
    )
    model_name: str = Field(
        default="gpt-3.5-turbo",
        description="Name of the LLM model to use"
    )
    
    # Ollama Settings
    use_ollama: bool = Field(
        default=False,
        description="Whether to use Ollama for local LLM inference"
    )
    ollama_model: str = Field(
        default="llama2:7b",
        description="Ollama model to use"
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Base URL for Ollama API"
    )
    
    # Embedding Settings
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Model to use for embeddings"
    )
    
    # Document Processing
    chunk_size: int = Field(
        default=1000,
        description="Size of document chunks in characters"
    )
    chunk_overlap: int = Field(
        default=200,
        description="Overlap between chunks in characters"
    )
    
    # Vector Store
    vector_store_path: Path = Field(
        default=Path("data/vector_store"),
        description="Path to vector store files"
    )
    
    # File Storage
    upload_dir: Path = Field(
        default=Path("uploads"),
        description="Directory for uploaded files"
    )
    export_dir: Path = Field(
        default=Path("exports"),
        description="Directory for exported files"
    )
    
    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    log_dir: Path = Field(
        default=Path("logs"),
        description="Directory for log files"
    )
    
    def validate_api_keys(self) -> None:
        """Validate that required API keys are present based on provider"""
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError("OpenAI API key is required when using OpenAI provider")
        if self.llm_provider == "anthropic" and not self.anthropic_api_key:
            raise ValueError("Anthropic API key is required when using Anthropic provider")
        if self.llm_provider == "ollama" and not self.use_ollama:
            raise ValueError("use_ollama must be True when using Ollama provider")
    
    class Config:
        """Pydantic settings configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Validate API keys
settings.validate_api_keys()

# Create necessary directories
for directory in [settings.upload_dir, settings.export_dir, settings.log_dir, settings.vector_store_path]:
    directory.mkdir(parents=True, exist_ok=True) 
