import psycopg
from psycopg.rows import dict_row
from .base import BaseDialect


class PostgresDialect(BaseDialect):
    """The adapter for PostgreSQL databases"""

    def connect(self, db_path: str):
        """
        Implements connection logic specifically for PostgreSQL.
        
        Args:
            db_path: Connection string for PostgreSQL
                    Format examples:
                    - "dbname=mydb user=myuser password=mypass host=localhost port=5432"
                    - "postgresql://myuser:mypass@localhost:5432/mydb"
                    - "host=localhost dbname=mydb user=myuser password=mypass"
        
        Returns:
            Connection object with dict row factory (similar to sqlite3.Row)
        """
        connection = psycopg.connect(db_path)
        connection.row_factory = dict_row  # returns rows as a Dict allowing access with column names
        return connection