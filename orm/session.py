from connection import Connection
from adapters.base import BaseDialect
from typing import Any, Set, Dict
from utils.query import QueryBuilder

# Custom Exceptions
class SessionError(Exception):
    """Base exception for session-related errors."""
    pass

class SessionStateError(SessionError):
    """Raised when session is in an invalid state for the operation."""
    pass

class TransactionError(SessionError):
    """Raised when transaction operations fail."""
    pass

class Session:
    """
    Jargon
    """
    
    def __init__(self, conn):
        self._conn = conn
        self._new: Set[Any] = set()  # New objects to insert
        self._dirty: Set[Any] = set()  # Modified objects to update
        self._deleted: Set[Any] = set()  # Objects to delete
        self._committed = False

        # session's memory
        # Identity Map: {(model_class, primary_key): instance}
        # e.g., {(User, 1): <User object at 0x17>}
        self._identity_map: Dict[tuple, Any] = {}

    def add(self, instance):
        if self._committed: 
            raise SessionStateError("Cannot add objects to committed session")

        if not hasattr(instance, '__tablename__'):
            raise TypeError("Instance must be a model with __tablename__ attribute")

        self._new.add(instance)

    def update(self, instance):
        if self._committed: 
            raise SessionStateError("Cannot add objects to committed session")

        if not hasattr(instance, '__tablename__'):
            raise TypeError("Instance must be a model with __tablename__ attribute")

        # Remove from new if it was added as new
        self._new.discard(instance)
        self._dirty.add(instance)

    def delete(self, instance):
        if self._committed:
            raise SessionStateError("Cannot delete objects in committed session")
            
        if not hasattr(instance, '__tablename__'):
            raise TypeError("Instance must be a model with __tablename__ attribute")

        # Remove from other sets
        self._new.discard(instance)
        self._dirty.discard(instance)
        self._deleted.add(instance)

    def commit(self):
        for obj in self._new:
            obj._insert(self._conn)
        for obj in self._dirty:
            obj._update(self._conn)
        for obj in self._deleted:
            obj._delete(self._conn)

        self._conn.do_commit()

        # Clear after commit
        self._new.clear()
        self._dirty.clear()
        self._deleted.clear()

    def rollback(self):
        """Rollback the current transaction and clear session state."""
        self._conn.rollback()

        # Clear session state after rollback
        self._new.clear()
        self._dirty.clear()
        self._deleted.clear()

    def query(self, model):
        return QueryBuilder(model, self)

    def __enter__(self):
        self._conn.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self._conn.close()