"""
Auto-Agentic: A modular conversational AI assistant for database querying.

This package provides a scalable framework for creating AI assistants that can:
- Interpret natural language queries
- Generate SQL queries via LLM
- Execute queries on configured databases
- Return insights in natural language
- Maintain conversation history

Main entry point:
    from auto_agentic import Agent
    
    agent = Agent()
    response = agent.invoke("Show top 5 customers by revenue")
"""

from .agent import Agent
from .config import Config

__version__ = "0.1.0"
__all__ = ["Agent", "Config"]
