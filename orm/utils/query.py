"""
query.py
--------

Provides the QueryBuilder for constructing and executing database queries.

This module contains the `QueryBuilder` class, which offers a fluent, chainable
interface for building SQL queries, including filtering, ordering, limiting,
and more.
"""

import logging
from typing import Any, List, Optional, Tuple, Type

# Forward declare types to avoid circular import issues
if False:
    from ..model import BaseModel
    from ..session import Session

logger = logging.getLogger(__name__)

class QueryBuilder():
    """
    A interface for building and executing SQL queries for a model.

    This class should not be instantiated directly. Instead, it should be accessed
    via the `Session.query(Model)` method. It allows for method chaining to
    construct complex queries piece by piece.
    """

    def __init__(self, model: Type["BaseModel"], session: "Session"): 
        """
        Initializes the QueryBuilder.

        Args:
            model (Type[BaseModel]): The model class to query against.
            session (Session): The session instance used for the query.
        """
        self._model = model
        self._session = session
        self._filters = {}
        self._where_conditions = []
        self._order_by_clause = None
        self._limit_value = None
        self._offset_value = None
        logger.debug(f"QueryBuilder initialized for model '{self._model.__name__}'")


    def get(self, primary_key: Any) -> Optional["BaseModel"]:
        """
        Retrieves a single object by its primary key.

        This method first checks the session's identity map. If the object is not
        found there, it queries the database.        

        Args:
            primary_key (Any): The primary key value of the object to retrieve.

        Returns:
            Optional[BaseModel]: The model instance if found, otherwise None.
        """

        # column_name = [descriptor[0] for descriptor in cursor.description ]
        # print(column_name)
        # for r in row:
        #     print(f"{r} | ", end='')
        # print()

        key = (self._model, primary_key)
        if key in self._session._identity_map:
            return self._session._identity_map[key]
            
        print(f"PRIMARY KEY : {self._model.__primary_key__}")    

        sql = f"SELECT * FROM {self._model.__tablename__} WHERE {self._model.__primary_key__}={primary_key}"
        cursor = self._session._conn.execute(sql)
        row = cursor.fetchone()
        
        if row is None:
            return None

        # column_name = [descriptor[0] for descriptor in cursor.description ]
        # print(column_name)
        # for r in row:
        #     print(f"{r} | ", end='')
        # print()

        # Create model instance from database row
        instance = self._model.from_row(row)
        # instance = self._model.from_row(row, session=self._session)
        
        # # Store in identity map for future lookups
        self._session._identity_map[key] = instance
        # print(f"IDENTITY MAP: {self._session._identity_map}")
        return instance

    def all(self) -> List["BaseModel"]:
        # sql = f"SELECT * FROM {self._model.__tablename__};"

        """
        Executes the query and returns all matching results as a list.

        Returns:
            List[BaseModel]: A list of model instances, or an empty list if none are found.
        """
        sql = self._build_select_sql()
        cursor = self._session._conn.execute(sql)
        rows = cursor.fetchall()
        
        if not rows:
            return []

        column_names = [descriptor[0] for descriptor in cursor.description ]
        # print(column_name)
        # for r in rows:
        #     print(dict(r))

        # Create model instances from database rows
        instances = []  
        for row in rows:
            instance = self._model.from_row(row)
            instances.append(instance)
            
            # Store in identity map for future lookups
            # key = (self._model, getattr(instance, self._model.__primary_key__))
            key = (self._model, instance)
            self._session._identity_map[key] = instance
        
        return instances

    def first(self) -> Optional["BaseModel"]:
        """
        Executes the query and returns the first matching result.

        Returns:
            Optional[BaseModel]: The first model instance found, or None if no match is found.
        """

        sql = self._build_select_sql()
        sql += " LIMIT 1"
        
        cursor = self._session._conn.execute(sql)
        row = cursor.fetchone()
        
        if row is None:
            return None
            
        # Create model instance from database row
        instance = self._model.from_row(row)
        
        # Store in identity map for future lookups
        # key = (self._model, getattr(instance, self._model.__primary_key__))
        key = (self._model, instance)
        self._session._identity_map[key] = instance
        
        return instance
    
    def filter(self, **kwargs) -> "QueryBuilder":
        """
        Adds one or more `equals` filters to the query using keyword arguments.

        Args:
            **kwargs: Field names and the values to filter by (e.g., `name="John"`).

        Returns:
            self (QueryBuilder): The current QueryBuilder instance for method chaining.
        """
        for field, value in kwargs.items():
            if not hasattr(self._model, field):
                raise AttributeError(
                    f"Field '{field}' does not exist on {self._model.__name__}"
                )
            self._where_conditions.append((field, "=", value))
        logger.debug(f"Added filter condition: {kwargs}")
        return self
    
    # def where(self, condition):
    #     """Add a custom WHERE condition. Returns self for method chaining."""
    #     self._where_conditions.append(condition)
    #     return self
    
    def limit(self, count) -> "QueryBuilder":
        """
        Adds a LIMIT clause to the query to restrict the number of results.

        Args:
            count (int): The maximum number of records to return.

        Returns:
            sellf (QueryBuilder): The current QueryBuilder instance for method chaining.
        """
        self._limit_value = count
        return self

    def order_by(self, field: str, direction: str = 'ASC') -> "QueryBuilder":
        """
        Adds an ORDER BY clause to the query to sort the results.

        Args:
            field (str): The name of the field to order by.
            direction (str): The sort direction ('ASC' or 'DESC').

        Returns:
            QueryBuilder: The current QueryBuilder instance for method chaining.
        """
        
        if not hasattr(self._model, field):
            raise AttributeError(
                f"Field '{field}' does not exist on {self._model.__name__}"
            )
        self._order_by_clause = f"{field} {direction.upper()}"
        return self

    def offset(self, count) -> "QueryBuilder":
        """
        Adds an OFFSET clause to the query to skip a number of results.

        Args:
            count (int): The number of records to skip from the beginning.

        Returns:
            QueryBuilder: The current QueryBuilder instance for method chaining.
        """
        self._offset_value = count
        return self

    def count(self) -> int:
        """
        Returns the total number of records matching the query's filters.

        Note:
            This ignores any `limit`, `offset`, or `order_by` clauses.

        Returns:
            int: The total count of matching records.
        """
        sql = f"SELECT COUNT(*) FROM {self._model.__tablename__}"
        
        if self._where_conditions:
            where_clause = self._build_where_clause()
            sql += f" WHERE {where_clause}"
        
        cursor = self._session._conn.execute(sql)
        result = cursor.fetchone()
        return result[0] if result else 0
    
    def exists(self) -> bool:
        """
        Check if any records exist matching the query.

        Returns:
            bool: Exists or not (T/F)
        """
        sql = f"SELECT 1 FROM {self._model.__tablename__}"
        
        if self._where_conditions:
            where_clause = self._build_where_clause()
            sql += f" WHERE {where_clause}"
        
        sql += " LIMIT 1"
        
        cursor = self._session._conn.execute(sql)
        return cursor.fetchone() is not None
    
    def delete(self):
        """
        Deletes all records matching the query's filters from the database.

        Returns:
            int: The number of rows deleted.
        """
        sql = f"DELETE FROM {self._model.__tablename__}"
        if self._where_conditions:
            where_clause = self._build_where_clause()
            sql += f" WHERE {where_clause}"
        
        cursor = self._session._conn.execute(sql)
        
        # Remove deleted records from identity map
        deleted_keys = []
        for key in self._session._identity_map:
            if key[0] == self._model:
                deleted_keys.append(key)
        
        for key in deleted_keys:
            del self._session._identity_map[key]
        
        return cursor.rowcount
    
    def update(self, **kwargs: Any) -> int:
        """
        Updates all records matching the query's filters with new values.

        Args:
            **kwargs: Field names and the new values to set.

        Returns:
            int: The number of rows updated.
        """
        if not kwargs:
            raise ValueError("At least one field must be provided for update")
        
        # Validate fields exist on model
        for field in kwargs.keys():
            if not hasattr(self._model, field):
                raise AttributeError(f"Field '{field}' does not exist on {self._model.__name__}")
        
        set_clauses = []
        values = []
        
        for field, value in kwargs.items():
            set_clauses.append(f"{field} = ?")
            values.append(value)
        
        sql = f"UPDATE {self._model.__tablename__} SET {', '.join(set_clauses)}"
        
        if self._where_conditions:
            where_clause = self._build_where_clause()
            sql += f" WHERE {where_clause}"
        
        cursor = self._session._conn.execute(sql, values)
        
        # Clear identity map for updated records since they may have changed
        updated_keys = []
        for key in self._session._identity_map:
            if key[0] == self._model:
                updated_keys.append(key)
        
        for key in updated_keys:
            del self._session._identity_map[key]
        
        return cursor.rowcount
    
    # HELPERS

    def _build_select_sql(self):
        """Constructs the full SELECT SQL query from the builder's state."""

        sql = f"SELECT * FROM {self._model.__tablename__}"
        
        if self._where_conditions:
            where_clause = self._build_where_clause()
            sql += f" WHERE {where_clause}"
        
        if self._order_by_clause:
            sql += f" ORDER BY {self._order_by_clause}"
        
        if self._limit_value is not None:
            sql += f" LIMIT {self._limit_value}"
        
        if self._offset_value is not None:
            sql += f" OFFSET {self._offset_value}"
        
        return sql
    
    def _build_where_clause(self):
        """Constructs the WHERE clause and parameters from stored conditions."""

        conditions = []
        
        for condition in self._where_conditions:
            if isinstance(condition, tuple) and len(condition) == 3:
                field, operator, value = condition
                if operator == '=':
                    conditions.append(f"{field} = '{value}'")
                elif operator == '!=':
                    conditions.append(f"{field} != '{value}'")
                elif operator == '>':
                    conditions.append(f"{field} > {value}")
                elif operator == '<':
                    conditions.append(f"{field} < {value}")
                elif operator == '>=':
                    conditions.append(f"{field} >= {value}")
                elif operator == '<=':
                    conditions.append(f"{field} <= {value}")
                elif operator == 'LIKE':
                    conditions.append(f"{field} LIKE '{value}'")
                elif operator == 'IN':
                    if isinstance(value, (list, tuple)):
                        placeholders = "', '".join(str(v) for v in value)
                        conditions.append(f"{field} IN ('{placeholders}')")
                    else:
                        conditions.append(f"{field} IN ('{value}')")
                else:
                    conditions.append(f"{field} {operator} '{value}'")
            else:
                # Assume it's a raw SQL condition
                conditions.append(str(condition))
        
        return " AND ".join(conditions)


    # Magic Methods
    
    def __iter__(self):
        """Allow iteration over query results."""
        return iter(self.all())
    
    def __len__(self):
        """Return the count of records matching the query."""
        return self.count()
    
    def __bool__(self):
        """Return True if any records exist matching the query."""
        return self.exists()
    
    def paginate(self, page, per_page):
        """Paginate query results. Returns (items, total_count)."""
        total_count = self.count()
        offset = (page - 1) * per_page
        
        items = self.offset(offset).limit(per_page).all()
        return items, total_count
    
    def distinct(self, field=None):
        """Add DISTINCT clause to the query."""
        if field and hasattr(self._model, field):
            # For now, wei'll implement this as a simple distinct on all fields
            # In a more advanced implementation, you'd modify the SELECT clause
            pass
        return self
    
    def group_by(self, field):
        """Add GROUP BY clause to the query."""
        if hasattr(self._model, field):
            # This would require modifying the SQL building logic
            # For now, we'll just store it for future implementation
            pass
        return self
    
    def having(self, condition):
        """Add HAVING clause to the query (used with GROUP BY)."""
        # This would require modifying the SQL building logic
        # For now, we'll just store it for future implementation
        return self