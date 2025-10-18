from adapters.base import BaseDialect

class Connection: 
    def __init__(self, db_path: str, dialect: BaseDialect = None):
        self.database = db_path
        self._conn = None
        self.dialect = dialect

    def connect(self):
        if self._conn is None:
            self._conn = self.dialect.connect(self.database)
            print(f"[*] Connected to '{self.database[-8:]}'")
        return self._conn

    def get_cursor(self):
        if not self._conn:
            raise Exception("Database not connected. Call connect() first.")
        return self._conn.cursor()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def do_commit(self):
        if self._conn:
            self._conn.commit()


    def execute(self, sql: str, params: tuple = None):
        """
        UNIVERSAL SQL Executer
        Parameter -> Prevents sql injection, instead of concatenation.
        """
        if not self._conn:
            raise Exception("Cannot execute query: no active connection. Use a 'with' block.")

        try:
            print(f"[SQL] Executing: {sql} | Params: {params}")
            cursor = self.get_cursor()
            cursor.execute(sql, params or ())
        except sqlite3.Error as e:
            print(f"Error {e}")
        finally:
            cursor.close()

        return cursor

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