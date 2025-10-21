class QueryBuilder():
    def __init__(self, model, session):
        self._model = model
        self._session = session
        self._filters = {}
        self._where_conditions = []
        self._order_by_clause = None
        self._limit_value = None
        self._offset_value = None

    def get(self, primary_key):

        """
        column_name = [descriptor[0] for descriptor in cursor.description ]
        print(column_name)
        for r in row:
            print(f"{r} | ", end='')
        print()
        """

        key = (self._model, primary_key)
        if key in self._session._identity_map:
            return self._session._identity_map[key]
            
        print(f"PRIMARY KEY : {self._model.__primary_key__}")    

        sql = f"SELECT * FROM {self._model.__tablename__} WHERE {self._model.__primary_key__}={primary_key}"
        cursor = self._session._conn.execute(sql)
        row = cursor.fetchone()
        
        if row is None:
            return None

        column_name = [descriptor[0] for descriptor in cursor.description ]
        print(column_name)
        for r in row:
            print(f"{r} | ", end='')
        print()

        # Create model instance from database row
        instance = self._model.from_row(row)
        
        # # Store in identity map for future lookups
        self._session._identity_map[key] = instance
        print(f"IDENTITY MAP: {self._session._identity_map}")
        return instance

    def all(self):
        # sql = f"SELECT * FROM {self._model.__tablename__};"
        """Get all records matching the query."""
        sql = self._build_select_sql()
        cursor = self._session._conn.execute(sql)
        rows = cursor.fetchall()
        
        if not rows:
            return []

        # column_name = [descriptor[0] for descriptor in cursor.description ]
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

    def first(self):
        """Get the first record from the query results."""
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
    
    def filter(self, **kwargs):
        """Add WHERE conditions to the query. Returns self for method chaining."""
        for field, value in kwargs.items():
            if hasattr(self._model, field):
                self._where_conditions.append((field, '=', value))
            # else:
                # raise AttributeError(f"Field '{field}' does not exist on {self._model.__name__}")
        return self
    
    def where(self, condition):
        """Add a custom WHERE condition. Returns self for method chaining."""
        self._where_conditions.append(condition)
        return self
    
    def limit(self, count):
        """Add LIMIT clause to the query. Returns self for method chaining."""
        self._limit_value = count
        return self

    def order_by(self, field, direction='ASC'):
        """Add ORDER BY clause to the query. Returns self for method chaining."""
        if hasattr(self._model, field):
            self._order_by_clause = f"{field} {direction.upper()}"
        else:
            raise AttributeError(f"Field '{field}' does not exist on {self._model.__name__}")
        return self

    def offset(self, count):
        """Add OFFSET clause to the query. Returns self for method chaining."""
        self._offset_value = count
        return self

    def count(self):
        """Count the number of records matching the query."""
        sql = f"SELECT COUNT(*) FROM {self._model.__tablename__}"
        
        if self._where_conditions:
            where_clause = self._build_where_clause()
            sql += f" WHERE {where_clause}"
        
        cursor = self._session._conn.execute(sql)
        result = cursor.fetchone()
        return result[0] if result else 0
    
    def exists(self):
        """Check if any records exist matching the query."""
        sql = f"SELECT 1 FROM {self._model.__tablename__}"
        
        if self._where_conditions:
            where_clause = self._build_where_clause()
            sql += f" WHERE {where_clause}"
        
        sql += " LIMIT 1"
        
        cursor = self._session._conn.execute(sql)
        return cursor.fetchone() is not None
    
    def delete(self):
        """Delete all records matching the query."""
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
    
    def update(self, **kwargs):
        """Update all records matching the query."""
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
        """Build the SELECT SQL query with all conditions."""
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
        """Build the WHERE clause from conditions."""
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
            # For now, we'll implement this as a simple distinct on all fields
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