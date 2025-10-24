"""
connection.py
--------------

Handles database connections for Objectron ORM.

Provides the Connection class which abstracts connection to 
different databses via adapters/dialects, executing queries,
and managing transactoin.
"""

from orm.adapters import BaseDialect
from typing import Any

# custom errors
class ConnectionError(Exception):
    """Base exception for connection-related errors."""
    pass

class QueryError(ConnectionError):
    """Raised when a query fails."""
    pass

class Connection: 
    """
    Manges a database connetion.

    Attributes: 
        db_path (str): Path or URL of the database.
        dialect (Sqldialect): Database adapter for generating SQL queries.
        connection (Any): The low-level database connection object.
    """
    def __init__(self, db_path: str, dialect: BaseDialect) -> None:
        """
        Initialize a Connection object.

        Args:
            db_path (str): Path or connection string for the database.
            dialect (SqlDialect): The SQL dialect/adapter.
        """
        self.database = db_path
        self._conn = None
        self.dialect = dialect

    # Context Manager
    def __enter__(self):
        """
        Enter the context manager.

        Returns:
            self: The Connection object.
        """
        try: 
            if self._conn is None:
                self.connect()
            except Exception as e:
                raise ConnectionError("Failed to connect to database.")
        return self

    def connect(self) -> Any:
        """
        Create a low-level connction to the database.

        Returns:
            Any: The database connection object.
        """ 
        try:
            if self._conn is None:
                self._conn = self.dialect.connect(self.database)
                # print(f"[*] Connected to '{self.database[-10:]}'") # log
            return self._conn
        except Exception as e:
            raise ConnectionError(f"Failed to connect to database: {e}")

    def get_cursor(self):
        """
        Creates a database cursor object for executing sql queries.

        Returns:
            sqlite3.Cursor: The database cursor object associated with the current database connection.

        Raises: 
            ConnectionError: If the database connection is not established.
        """

        if self._conn:
            try:
                cursor = self._conn.cursor()
                return cursor
            except Exception as e:
                raise ConnectionError(f"Failed to get cursor: {e}")
        else:
            raise ConnectionError("Database not connected. Call connect() first.")

    def close(self) -> None:
        """
        Close the database connection.

        """
        if self._conn:
            try:
                self._conn.close()
                self._conn = None
            except Exception as e:
                raise ConnectionError(f"Failed to close connection: {e}")
        else:
            raise ConnectionError("Database not connected. Call connect() first.")

    def do_commit(self) -> None:
        """
        Commit the current transaction to the database.

        Returns:
            None
        """
        if self._conn:
            try:
                self._conn.commit()
            except Exception as e:
                raise ConnectionError(f"Failed to commit transaction: {e}")
        else:
            raise ConnectionError("Database not connected. Call connect() first.")

    def rollback(self) -> None:
        """
        Rollback the current transaction to the database.

        Returns:
            None
        """
        if self._conn:
            try:
                self._conn.rollback()
                print("[*] Transaction rolled back successfully.")
            except Exception as e:
                print("[!] Transaction rollback failed.")
                raise ConnectionError(f"Failed to rollback transaction: {e}")
        else: 
            raise ConnectionError("Database not connected. Call connect() first.")

    def execute(self, sql: str, params: tuple = (None)) -> Any:
        """
        Execute a SQL query on the database. Universal Sql Executer.

        Parameter -> Prevents sql injection, instead of concatenation.
        
        Args:
            sql (str): Sql statement to execute.
            params (tuple, optional): Query parameters.

        Returns: 
            Any: cursor object.
        """
        if not self._conn:
            raise ConnectionError("Cannot execute query: no active connection. Use a 'with' block.")

        try:
            print(f"[SQL] Executing: {sql} | Params: {params}")
            cursor = self.get_cursor()
            cursor.execute(sql, params or ())
            return cursor
        except Exception as e:
            print(f"[!] Error: {e}")
            raise QueryError(f"Query execution failed: {e}")
        finally:
            if cursor:
                cursor.close()

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exit the context manager.

        Args:
            exc_type (type): The type of the exception.
            exc_value (Exception): The exception object.
            traceback (traceback): The traceback object.
        """
        try:
            if exc_type:
                print("[!] Rolling back due to error.")
                self._conn.rollback()
            else:
                print("[*] Committing Transaction.") 
                self._conn.commit()
        except Exception as e:
            raise ConnectionError(f"Failed to exit context manager: {e}")
        finally:
            self.close()
            print("[=] Connection Closed")