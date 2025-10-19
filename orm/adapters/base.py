# BaseDialect

"""
    TO DO
    - placeholders

"""
class BaseDialect():
    """
    The "contract" or "interface" that all database adapters must follow.
    This is an abstract base class; it's not meant to be used directly.
    """
    def connect(self, db_path: str):
        """Connects to the database and returns a connection object."""
        raise NotImplementedError("Subclass must implement the 'connect' method.")