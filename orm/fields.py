from typing import Any, Optional

class Field:
    """Base Field descriptor and metadata container"""
    def __init__(self, *, primary_key: bool = False, nullable: bool = False, default: Any = None, unique: bool = False):
        self.name: Optional[str] = None   # set by __set_name__
        # self.column_type = column_type
        self.primary_key = primary_key
        self.nullable = nullable
        self.default = default
        self.unique = unique
        # note: descriptor stores instance values in instance.__dict__[self.name]

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            # accessed as MyModel.field -> return field object for introspection
            return self
        return instance.__dict__.get(self.name, self.default if self.default is not None else None)

    def __set__(self, instance, value):
        # basic validation/coercion
        value = self.to_python(value)
        # enforce not-null
        if value is None and not self.nullable and not self.primary_key:
            raise ValueError(f"Field '{self.name}' cannot be NULL")
        instance.__dict__[self.name] = value

    # conversion hooks (override in subclasses)
    def to_python(self, value):
        """Convert DB/raw value -> Python value (default noop)."""
        return value

    def to_db(self, value):
        """Convert Python value -> DB-ready value (default noop)."""
        return value

    def get_sql_type(self):
        """Return SQL column type for CREATE TABLE (override in subclasses)."""
        raise NotImplementedError

    def column_definition(self):
        """Return SQL fragment for CREATE TABLE for this column."""
        parts = [f"{self.name} {self.get_sql_type()}"]
        if self.primary_key:
            parts.append("PRIMARY KEY")
        if not self.nullable:
            parts.append("NOT NULL")
        if self.unique:
            parts.append("UNIQUE")
        if self.default is not None and not self.primary_key:
            # naive default printing; for strings we add quotes
            default = self.default
            if isinstance(default, str):
                default = f"'{default}'"
            parts.append(f"DEFAULT {default}")
        return " ".join(parts)

    def to_sql(self):
        """Alias for column_definition for compatibility with model.py"""
        return self.column_definition()


class IntegerField(Field):
    def get_sql_type(self):
        return "INTEGER"

    def to_python(self, value):
        if value is None:
            return None
        return int(value)


class FloatField(Field):
    def get_sql_type(self):
        return "REAL"

    def to_python(self, value):
        if value is None:
            return None
        return float(value)

class TextField(Field):
    def get_sql_type(self):
        return "TEXT"

    def to_python(self, value):
        return None if value is None else str(value)

class BooleanField(Field):
    def get_sql_type(self):
        """proper Booleans are yet to be implemented"""
        pass
        # SQLite has no true boolean; use INTEGER for MVP
        # return "INTEGER"

    def to_python(self, value):
        if value is None:
            return None
        # SQLite stores 0/1
        return bool(value)

    def to_db(self, value):
        return None if value is None else (1 if value else 0)

class ForeignKey(Field):
    def __init__(self, to, *, nullable: bool = True, on_delete: str = None):
        # `to` is the referenced Model class (or string)
        super().__init__(primary_key=False, nullable=nullable)
        self.to = to
        self.on_delete = on_delete

    def get_sql_type(self):
        # store FK as INTEGER (assuming referenced PK is integer) for MVP
        return "INTEGER"

    def column_definition(self):
        base = super().column_definition()
        # We will not auto-generate actual FOREIGN KEY constraint in MVP,
        # but you could append: , FOREIGN KEY (col) REFERENCES other(id)
        return base
