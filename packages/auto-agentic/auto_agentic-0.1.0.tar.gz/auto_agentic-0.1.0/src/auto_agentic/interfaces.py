"""
Abstract base classes for extensible components.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    def generate_sql(self, schema: str, question: str, history: List[Dict]) -> str:
        """Generate SQL query from natural language."""
        pass
    
    @abstractmethod
    def summarize_data(self, question: str, data: List[Dict], history: List[Dict]) -> str:
        """Summarize query results into natural language."""
        pass
    
    @abstractmethod
    def classify_intent(self, message: str, history: List[Dict]) -> str:
        """Classify user intent (greeting, task, recall, task+recall)."""
        pass


class DatabaseBackend(ABC):
    """Abstract base class for database backends."""
    
    @abstractmethod
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results."""
        pass
    
    @abstractmethod
    def get_schema(self) -> str:
        """Get database schema information."""
        pass
    
    @abstractmethod
    def is_safe_query(self, query: str) -> bool:
        """Check if query is safe (non-destructive)."""
        pass


class MemoryBackend(ABC):
    """Abstract base class for memory backends."""
    
    @abstractmethod
    def load_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Load conversation history for a session."""
        pass
    
    @abstractmethod
    def save_history(self, session_id: str, history: List[Dict[str, Any]]) -> None:
        """Save conversation history for a session."""
        pass
