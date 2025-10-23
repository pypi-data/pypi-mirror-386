"""
SQLite database backend implementation.
"""

import sqlite3
import logging
import re
from typing import List, Dict, Any

from .interfaces import DatabaseBackend

logger = logging.getLogger(__name__)


class SQLiteBackend(DatabaseBackend):
    """SQLite database backend implementation."""
    
    def __init__(self, db_path: str):
        """
        Initialize SQLite backend.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database connection and create conversation_history table if needed."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create conversation_history table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            history_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        conn.commit()
        conn.close()
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results."""
        if not self.is_safe_query(query):
            raise ValueError("Query contains potentially destructive operations")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute(query)
            
            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            
            conn.close()
            
            # Convert to list of dictionaries
            return [dict(zip(columns, row)) for row in rows]
        
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    def get_schema(self) -> str:
        """Get database schema information."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all tables except conversation_history
            tables = cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name != 'conversation_history';"
            ).fetchall()

            schema_info = []
            for (table_name,) in tables:
                columns = cursor.execute(f"PRAGMA table_info({table_name});").fetchall()
                column_defs = [f"{col[1]} {col[2]}" for col in columns]
                schema_info.append(f"TABLE {table_name} ({', '.join(column_defs)})")
            
            conn.close()
            
            return "\n".join(schema_info) if schema_info else "No user tables found in database."
        
        except Exception as e:
            logger.error(f"Error getting schema: {e}")
            raise
    
    def is_safe_query(self, query: str) -> bool:
        """
        Check if query is safe (non-destructive).
        
        Args:
            query: SQL query to check
            
        Returns:
            True if query is safe, False otherwise
        """
        # Convert to lowercase for checking
        query_lower = query.lower().strip()
        
        # List of potentially destructive SQL keywords
        destructive_keywords = [
            'drop', 'delete', 'update', 'insert', 'alter', 'create', 'truncate',
            'replace', 'merge', 'grant', 'revoke', 'commit', 'rollback'
        ]
        
        # Check for destructive keywords
        for keyword in destructive_keywords:
            if keyword in query_lower:
                logger.warning(f"Query contains destructive keyword: {keyword}")
                return False
        
        # Additional safety checks
        # Check for semicolon injection attempts
        if ';' in query and query.count(';') > 1:
            logger.warning("Query contains multiple semicolons")
            return False
        
        # Check for comment injection attempts
        if '--' in query or '/*' in query:
            logger.warning("Query contains comment characters")
            return False
        
        return True
