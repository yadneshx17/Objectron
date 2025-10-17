import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

# Global var holds connection object.
_conn = None

class Connection:
    def __init__(self, db_path: str, ):
        self.database = db_path
        self._conn = None

    def connect(self):
        """Establish a connection if not connected already."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.database)
            self._conn.row_factory = sqlite3.Row 
            print(f"[*] Connection to '{self.database[-5:]}' established.")            
        return self._conn

    def close(self):
        """Safely close connection."""
        if self._conn is not None:
            try:
                self._conn.close()
            finally:
                self._conn = None

    def get_cursor(self) -> sqlite3.Cursor:
        if self._conn is None:
            self.connect()
        return self._conn.cursor()

    def do_commit(self) -> None:
        """Manually commit transactions."""
        if self._conn is not None:
            self._conn.commit()

    def execute(self, sql: str, params: tuple = None, *, commit: bool = False, fetch: bool = False):
        """
        UNIVERSAL SQL Executer
        Parameter -> Prevents sql injection, instead of concatenation.
        """
        cursor = self.get_cursor()

        try:
            print(f"[SQL] {sql} | Params: {params}")
            cursor.execute(sql, params or ())
            if commit: 
                self._conn.commit()
            if fetch:
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error {e}")
        finally:
            cursor.close()

    # Context Manager
    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            print("[!] Rolling back due to error.")
            self._conn.rollback()
        else:
            self._conn.commit()
        self.close()
