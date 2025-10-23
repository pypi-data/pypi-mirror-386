"""
Main Agent class for auto-agentic.
"""

import uuid
import logging
from typing import Optional

from .config import Config
from .interfaces import LLMProvider, DatabaseBackend, MemoryBackend
from .llm_providers import OpenAIProvider
from .database_backends import SQLiteBackend
from .memory_backends import InMemoryMemory, SQLiteMemory

logger = logging.getLogger(__name__)


class Agent:
    """
    Main Agent class for auto-agentic conversational AI assistant.
    
    This is the primary entry point for the package. It orchestrates
    LLM providers, database backends, and memory systems to provide
    natural language database querying capabilities.
    """
    
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
        Initialize the Agent.
        
        Args:
            openai_api_key: OpenAI API key (overrides .env)
            llm_provider: LLM provider (overrides .env)
            database_type: Database type (overrides .env)
            db_path: Database file path (overrides .env)
            memory_type: Memory backend type (overrides .env)
            persist_memory: Whether to persist memory (overrides .env)
            model: LLM model name (overrides .env)
            env_file: Path to .env file (default: .env)
        """
        # Load configuration
        self.config = Config(
            openai_api_key=openai_api_key,
            llm_provider=llm_provider,
            database_type=database_type,
            db_path=db_path,
            memory_type=memory_type,
            persist_memory=persist_memory,
            model=model,
            env_file=env_file
        )
        
        # Initialize components
        self._init_llm_provider()
        self._init_database_backend()
        self._init_memory_backend()
        
        logger.info(f"Agent initialized with config: {self.config.to_dict()}")
    
    def _init_llm_provider(self):
        """Initialize LLM provider based on configuration."""
        if self.config.llm_provider == "openai":
            self.llm_provider: LLMProvider = OpenAIProvider(
                api_key=self.config.openai_api_key,
                model=self.config.model
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.config.llm_provider}")
    
    def _init_database_backend(self):
        """Initialize database backend based on configuration."""
        if self.config.database_type == "sqlite":
            self.db_backend: DatabaseBackend = SQLiteBackend(self.config.db_path)
        else:
            raise ValueError(f"Unsupported database type: {self.config.database_type}")
    
    def _init_memory_backend(self):
        """Initialize memory backend based on configuration."""
        if self.config.memory_type == "sqlite":
            self.memory_backend: MemoryBackend = SQLiteMemory(self.config.db_path)
        elif self.config.memory_type == "in_memory":
            self.memory_backend: MemoryBackend = InMemoryMemory()
        else:
            raise ValueError(f"Unsupported memory type: {self.config.memory_type}")
    
    def invoke(self, prompt: str, session_id: Optional[str] = None) -> str:
        """
        Process a user prompt and return a natural language response.
        
        Args:
            prompt: User's natural language query
            session_id: Optional session ID for conversation history
            
        Returns:
            Natural language response
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        logger.info(f"Processing prompt for session {session_id}: {prompt}")
        
        try:
            # Load conversation history
            history = self.memory_backend.load_history(session_id)
            
            # Get database schema
            schema = self.db_backend.get_schema()
            
            # Classify user intent
            intent = self.llm_provider.classify_intent(prompt, history)
            logger.info(f"Intent classified as: {intent}")
            
            # Process based on intent
            if intent == "recall":
                response = self._handle_recall(prompt, history)
            elif intent == "greeting":
                response = self._handle_greeting(prompt, history)
            elif intent == "task+recall":
                response = self._handle_task_recall(prompt, history, schema)
            else:  # task
                response = self._handle_task(prompt, history, schema)
            
            # Save conversation history
            self._save_conversation_entry(session_id, history, prompt, intent, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing prompt: {e}")
            raise
    
    def _handle_recall(self, prompt: str, history: list) -> str:
        """Handle recall/follow-up queries."""
        response = self.llm_provider.recall_response(prompt, history)
        return response
    
    def _handle_greeting(self, prompt: str, history: list) -> str:
        """Handle greeting/small talk."""
        response = self.llm_provider.chat_response(prompt, history)
        return response
    
    def _handle_task_recall(self, prompt: str, history: list, schema: str) -> str:
        """Handle combined task and recall queries."""
        # Generate and execute SQL
        sql_query = self.llm_provider.generate_sql(schema, prompt, history)
        logger.info(f"Generated SQL: {sql_query}")
        
        try:
            result_data = self.db_backend.execute_query(sql_query)
            logger.info(f"Query executed successfully, {len(result_data)} rows returned")
        except Exception as e:
            result_data = {"error": str(e)}
            logger.error(f"SQL execution error: {e}")
        
        # Use recall logic with new data
        response = self.llm_provider.recall_response(prompt, history, result_data)
        return response
    
    def _handle_task(self, prompt: str, history: list, schema: str) -> str:
        """Handle data query tasks."""
        # Generate SQL query
        sql_query = self.llm_provider.generate_sql(schema, prompt, history)
        logger.info(f"Generated SQL: {sql_query}")
        
        try:
            # Execute query
            result_data = self.db_backend.execute_query(sql_query)
            logger.info(f"Query executed successfully, {len(result_data)} rows returned")
            
            # Summarize results
            response = self.llm_provider.summarize_data(prompt, result_data, history)
            
        except Exception as e:
            logger.error(f"SQL execution error: {e}")
            response = f"I encountered an error while processing your query: {str(e)}"
            result_data = {"error": str(e)}
        
        return response
    
    def _save_conversation_entry(self, session_id: str, history: list, 
                                prompt: str, intent: str, response: str):
        """Save conversation entry to history."""
        entry = {
            "step": len(history) + 1,
            "user_input": prompt,
            "intent": intent,
            "response": response,
            "timestamp": str(uuid.uuid4())  # Simple timestamp
        }
        
        history.append(entry)
        self.memory_backend.save_history(session_id, history)
