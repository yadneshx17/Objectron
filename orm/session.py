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
    """Raised when a session is in an invalid state for the requested operation."""

    pass


class TransactionError(SessionError):
    """Raised when a transaction operation fails, such as a commit or rollback."""

    pass


class Session:
    """
    Manages the persistence operations for ORM objects.

    The Session acts as a gateway to the database, providing a workspace for
    grouping related database operations. It maintains a state of objects
    (new, modified, deleted) and handles transaction management (commit, rollback)
    to ensure data integrity.

    It also implements an Identity Map pattern to ensure that for any given
    database record, only one object instance exists within the session.

    Attributes:
        _conn (Connection): The database connection object.
        _new (Set[Any]): A set of new objects to be inserted into the database.
        _dirty (Set[Any]): A set of objects that have been modified and need to be updated.
        _deleted (Set[Any]): A set of objects marked for deletion.
        _identity_map (Dict[tuple, Any]): A map to track objects loaded into the session.
    """

    def __init__(self, conn: Connection):
        """
        Initializes a new Session.

        Args:
            conn (Connection): An active database connection wrapper.
        """
        self._conn = conn
        self._new: Set[Any] = set()  # New objects to insert
        self._dirty: Set[Any] = set()  # Modified objects to update
        self._deleted: Set[Any] = set()  # Objects to delete
        self._committed = False

        # session's memory
        # Identity Map: {(model_class, primary_key): instance}
        # e.g., {(User, 1): <User object at 0x17>}
        self._identity_map: Dict[tuple, Any] = {}

    def add(self, instance: Any):
        """
        Adds a new model instance to the session, marking it for insertion.

        Args:
            instance (Any): The model instance to be added.

        Raises:
            SessionStateError: If the session has already been committed.
            TypeError: If the instance is not a valid model with a `__tablename__`.
        """

        if self._committed:
            logger.error("Cannot add object to a committed session: %s", instance)
            raise SessionStateError("Cannot add objects to committed session")

        if not hasattr(instance, "__tablename__"):
            logger.error("Cannot add object without __tablename__: %s", instance)
            raise TypeError("Instance must be a model with __tablename__ attribute")

        logger.debug("Adding new object to session: %s", instance)
        self._new.add(instance)

    def update(self, instance: Any):
        """
        Marks a model instance as modified (dirty).

        If the instance was previously marked as new, it is removed from the
        `_new` set and added to the `_dirty` set.

        Args:
            instance (Any): The model instance to be updated.

        Raises:
            SessionStateError: If the session has already been committed.
            TypeError: If the instance is not a valid model with a `__tablename__`.
        """
        if self._committed:
            logger.error("Cannot update object in a committed session: %s", instance)
            raise SessionStateError("Cannot add objects to committed session")

        if not hasattr(instance, "__tablename__"):
            logger.error("Cannot update object without __tablename__: %s", instance)
            raise TypeError("Instance must be a model with __tablename__ attribute")

        # Remove from new if it was added as new
        if instance in self._new:
            self._new.discard(instance)
        # add to the (modified set) dirty.
        self._dirty.add(instance)

    def delete(self, instance: Any):
        """
        Marks a model instance for deletion.

        The instance is removed from the `_new` and `_dirty` sets if present
        and added to the `_deleted` set.

        Args:
            instance (Any): The model instance to be deleted.

        Raises:
            SessionStateError: If the session has already been committed.
            TypeError: If the instance is not a valid model with a `__tablename__`.
        """
        if self._committed:
            logger.error("Cannot delete object in a committed session: %s", instance)
            raise SessionStateError("Cannot delete objects in committed session")

        if not hasattr(instance, "__tablename__"):
            logger.error("Cannot delete object without __tablename__: %s", instance)
            raise TypeError("Instance must be a model with __tablename__ attribute")

        logger.debug("Marking object for deletion: %s", instance)

        # Remove from other sets
        self._new.discard(instance)
        self._dirty.discard(instance)

        self._deleted.add(instance)

    def commit(self):
        """
        Flushes all pending changes (inserts, updates, deletes) to the database.

        The operations are performed in a specific order: inserts, then updates,
        then deletes. If any operation fails, the entire transaction is rolled back.

        Raises:
            TransactionError: If the commit fails and the subsequent rollback also fails.
        """

        # Don't do anything if there are no changes
        if not self._new and not self._dirty and not self._deleted:
            logger.info("No changes to commit.")
            return

        logger.info(
            "Committing transaction: %d new, %d dirty, %d deleted.",
            len(self._new),
            len(self._dirty),
            len(self._deleted),
        )

        # Operations in DB.
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
            except Exception as rb_e:
                logger.critical(
                    "Rollback FAILED during commit failure. Session state "
                    "may be inconsistent. Rollback error: %s",
                    rb_e,
                    exc_info=True,
                )

            raise TransactionError("Commit failed") from e

        finally:
            # Clear after commit
            self._new.clear()
            self._dirty.clear()
            self._deleted.clear()
            self._committed = True

    # def close(self):
    #     self._conn.close()

    def rollback(self):
        """
        Rolls back the current transaction and clears the session's state (inserts, updates and deletes).

        This reverts the database to its state before the transaction began and
        clears all objects from the `_new`, `_dirty`, and `_deleted` sets.

        Raises:
            TransactionError: If the database rollback command fails.
        """
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

    def query(self, model: Any) -> QueryBuilder:
        """
        Creates a new QueryBuilder for a given model.

        Args:
            model (Any): The model class to be queried.

        Returns:
            QueryBuilder: A new query builder instance for the specified model.
        """
        logger.debug("Creating QueryBuilder for model: %s", model.__name__)
        return QueryBuilder(model, self)

    def __enter__(self):
        """
        Enters a context manager, connecting to the database.

        Returns:
            Session: The current session instance.
        """
        # Lifecycle event
        logger.info("Session context entered, connection opened.")
        
        self._conn.connect()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exits the context manager.

        Commits the transaction if no exceptions occurred, otherwise rolls it back.
        Ensures the database connection is closed.

        Args:
            exc_type: The exception type if an exception occurred.
            exc_val: The exception value if an exception occurred.
            exc_tb: The traceback if an exception occurred.
        """
        try:
            if exc_type:
                logger.error(
                    "Exception occurred in session context. Initiating rollback. "
                    "Error: %s",
                    exc_val,
                    exc_info=(exc_type, exc_val, exc_tb),
                )
                self.rollback()
            else:
                logger.info("Session context exited cleanly. Committing.")
                self.commit()
        finally:
            # Lifecycle event
            logger.info("Session closed, connection released.")
            self._conn.close()
