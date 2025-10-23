"""
Configuration management for auto-agentic.
"""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv


class Config:
    """Configuration manager for auto-agentic."""
    
    def __init__(self, 
                 openai_api_key: Optional[str] = None,
                 llm_provider: Optional[str] = None,
                 database_type: Optional[str] = None,
                 db_path: Optional[str] = None,
                 memory_type: Optional[str] = None,
                 persist_memory: Optional[bool] = None,
                 model: Optional[str] = None,
                 env_file: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            openai_api_key: OpenAI API key
            llm_provider: LLM provider (default: openai)
            database_type: Database type (default: sqlite)
            db_path: Database file path
            memory_type: Memory backend type (default: sqlite)
            persist_memory: Whether to persist memory (default: True)
            model: LLM model name (default: gpt-4o-mini)
            env_file: Path to .env file (default: .env)
        """
        # Load environment variables
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
        
        # Set configuration with env defaults and parameter overrides
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY", "")
        self.llm_provider = llm_provider or os.getenv("LLM_PROVIDER", "openai")
        self.database_type = database_type or os.getenv("DATABASE_TYPE", "sqlite")
        self.db_path = db_path or os.getenv("DB_PATH", "system.db")
        self.memory_type = memory_type or os.getenv("MEMORY_TYPE", "sqlite")
        self.persist_memory = persist_memory if persist_memory is not None else self._parse_bool(os.getenv("PERSIST_MEMORY", "True"))
        self.model = model or os.getenv("MODEL", "gpt-4o-mini")
        
        # Validate configuration
        self._validate()
    
    def _parse_bool(self, value: str) -> bool:
        """Parse boolean from string."""
        return value.lower() in ("true", "1", "yes", "on")
    
    def _validate(self) -> None:
        """Validate configuration."""
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required")
        
        if self.llm_provider not in ["openai"]:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
        
        if self.database_type not in ["sqlite"]:
            raise ValueError(f"Unsupported database type: {self.database_type}")
        
        if self.memory_type not in ["sqlite", "in_memory"]:
            raise ValueError(f"Unsupported memory type: {self.memory_type}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "openai_api_key": self.openai_api_key,
            "llm_provider": self.llm_provider,
            "database_type": self.database_type,
            "db_path": self.db_path,
            "memory_type": self.memory_type,
            "persist_memory": self.persist_memory,
            "model": self.model
        }
