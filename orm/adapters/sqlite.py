import sqlite3
from .base import BaseDialect

class SqlDialect(BaseDialect):
    """The adapter for SQLite databases"""

    def connect(self, db_path: str):
        """Implements connection logic specifically for sqlite3."""
    
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row # returns rows as a Dict allowing access with column names.
        return connection  