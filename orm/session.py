from .connection import Connection
from .adapters.base import BaseDialect
from typing import Any, Set, Dict
from .utils.query import QueryBuilder
import logging

logger = logging.getLogger(__name__)

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
            logger.error("Cannot add object to a committed session: %s", instance)
            raise SessionStateError("Cannot add objects to committed session")

        if not hasattr(instance, '__tablename__'):
            logger.error("Cannot add object without __tablename__: %s", instance)
            raise TypeError("Instance must be a model with __tablename__ attribute")

        logger.debug("Adding new object to session: %s", instance)
        self._new.add(instance)

    def update(self, instance):
        if self._committed: 
            logger.error("Cannot update object in a committed session: %s", instance)
            raise SessionStateError("Cannot add objects to committed session")

        if not hasattr(instance, '__tablename__'):
            logger.error("Cannot update object without __tablename__: %s", instance)
            raise TypeError("Instance must be a model with __tablename__ attribute")

        # Remove from new if it was added as new
        if instance in self._new:
            self._new.discard(instance)
        self._dirty.add(instance)

    def delete(self, instance):
        if self._committed:
            logger.error("Cannot delete object in a committed session: %s", instance)
            raise SessionStateError("Cannot delete objects in committed session")
            
        if not hasattr(instance, '__tablename__'):
            logger.error("Cannot delete object without __tablename__: %s", instance)
            raise TypeError("Instance must be a model with __tablename__ attribute")

        logger.debug("Marking object for deletion: %s", instance)

        # Remove from other sets
        self._new.discard(instance)
        self._dirty.discard(instance)
        self._deleted.add(instance)

    def commit(self):

        # Don't do anything if there are no changes
        if not self._new and not self._dirty and not self._deleted:
            logger.info("No changes to commit.")
            return

        logger.info(
            "Committing transaction: %d new, %d dirty, %d deleted.",
            len(self._new), len(self._dirty), len(self._deleted)
        )

        try: 
            for obj in self._new:
                logger.debug("Inserting: %s", obj)
                obj._insert(self._conn)
            for obj in self._dirty:
                logger.debug("Updating: %s", obj)
                obj._update(self._conn)
            for obj in self._deleted:
                logger.debug("Deleting: %s", obj)
                obj._delete(self._conn)

            # final db-level commit
            self._conn.do_commit()

            logger.info("Commit successful.")


        except Exception as e:
            logger.error(
                "Commit FAILED. Initiating rollback. Error: %s", e, exc_info=True
            )

            try:
                self.rollback()
            except Exception as e:
                logger.critical(
                    "Rollback FAILED during commit failure. Session state "
                    "may be inconsistent. Rollback error: %s", rb_e, exc_info=True
                )

            raise TransactionError("Commit failed") from e

        finally:
            # Clear after commit
            self._new.clear()
            self._dirty.clear()
            self._deleted.clear()
            self._commited = True

    # def close(self):
    #     self._conn.close()

    def rollback(self):
        """Rollback the current transaction and clear session state."""
        logger.info("Rollback initiated.")

        try:
            self._conn.rollback()
            logger.info("Rollback successful.")
        except Exception as e:
            # ERROR: We tried to roll back but failed.
            logger.error("Rollback FAILED. Error: %s", e, exc_info=True)
            raise TransactionError("Rollback failed") from e
        finally:
            # Clear session state after rollback
            logger.debug("Clearing session state after rollback.")
            self._new.clear()
            self._dirty.clear()
            self._deleted.clear()

    def query(self, model):
        logger.debug("Creating QueryBuilder for model: %s", model.__name__)
        return QueryBuilder(model, self)

    def __enter__(self):
        """Called when entering a 'with' statement."""
        # Lifecycle event
        logger.info("Session context entered, connection opened.")
        self._conn.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Called when exiting a 'with' statement."""
        try:
            if exc_type:
                logger.error(
                    "Exception occurred in session context. Initiating rollback. "
                    "Error: %s", exc_val, exc_info=(exc_type, exc_val, exc_tb)
                )
                self.rollback()
        else:
            logger.info("Session context exited cleanly. Committing.")
            self.commit()

        finally:
            # Lifecycle event
            logger.info("Session closed, connection released.")
            self._conn.close()