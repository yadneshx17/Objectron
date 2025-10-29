from .fields import Field
from .connection import Connection # Use our Connection class
from .session import Session # Forward-declare for type hints
from typing import Optional

"""
	To Do: Dialect Support 

		- Placeholder: Dialect-aware by using connection's dialect.
"""

class ModelError(Exception):
	"""Base exception for model-related errors."""
	pass

class MetaClass(type):
	"""
		The metaclass foreman that builds our model classes.
		It inspects the class definition, finds all the Field objects,
		and stores them in a convenient `_fields` dictionary.
	"""
	
	def __new__(cls, name, bases, attrs):
		"""
		Create a new class.

		Args:
			name (str): The name of the class.
			bases (tuple): The base classes.
			attrs (dict): The attributes of the class.
		"""
		try:
			if name == 'BaseModel':
				cls = super().__new__(cls, name, bases, attrs) # new instance of the class
				return cls # return the new instance of the class
		except Exception as e:
			raise ModelError(f"[!] Failed to create new class: {e}")

		# Find all the blueprints (Field objects)
		fields = {
			key: value for key, value in attrs.items() if isinstance(value, Field) 
		}
		if not fields:
			raise ModelError("[!] No fields found in class.")
	
		# Store the stolen goods on the class itself
		try:
			attrs['__tablename__'] = attrs.get('__tablename__', name.lower() + "s")
			attrs['_fields'] = fields
		except Exception as e:
			raise ModelError(f"[!] Failed to store attributes: {e}")

		# Finding Primary Key
		# We must thorugh *all* fields first, *then* check if we found one.
		pk_name = None
		for field_name, field_obj in fields.items():
			if field_obj.primary_key:
				if pk_name is not None:
					# print(f"FOUND ->  {field_obj} : {field_name}")
					raise ModelError(f"[!] Model {name} has multiple primary keys defined.")
				else:
					pk_name = field_name

		if pk_name is None:
			# The loop finished and we *never* found a PK.
			raise ModelError(f"Model {name} does not have a primary key defined.")

		attrs['__primary_key__'] = pk_name

		# Create the class with our new attributes
		return super().__new__(cls, name, bases, attrs) 

class BaseModel(metaclass=MetaClass):
	"""Base class for all models."""	
	def __init__(self, **kwargs):
		"""
		Initialize the model.
		
		Args:
			**kwargs: The keyword arguments to initialize the model.
		"""
		try: 
			for key, value in kwargs.items():
				setattr(self, key, value) # set the value of named attribute of an object.
		except Exception as e:
			raise ModelError(f"[!] Failed to initialize model: {e}")
		finally:
			print("[*] Model initialized successfully.")

	def __repr__(self) -> str:
		"""
		Human-readable representation: <Class(field1=value1, field2=value2)>

		Returns:
			str: The human-readable representation of the model.
		"""
		try:
			field_values = ", ".join(
				f"{field}={getattr(self, field)!r}" for field in self._fields
			)
			return f"<{self.__class__.__name__}({field_values})>"
		except Exception as e:
			raise ModelError(f"[!] Failed to represent model: {e}")

	@classmethod
	def create_table(cls, conn) -> None:
		"""
		Generate and execute CREATE TABLE statement.

		Args:
			conn (Connection): The connection to the database.
		"""
		try:
			columns = [field.to_sql() for field in cls._fields.values()]
			sql = f"CREATE TABLE IF NOT EXISTS {cls.__tablename__} ({', '.join(columns)})"
			conn.execute(sql)
		except Exception as e:
			raise ModelError(f"[!] Failed to Create a table: {e}")

	@classmethod
	def from_row(cls, row, session: Optional["Session"] = None) -> "BaseModel":
		"""
		Convert a raw database row into a model instance.
	
		If a session is provided, this method will check the identity map
		to avoid creating duplicate instances.

		Args:
			row (Any): A database row object (e.g., `sqlite3.Row`) containing column data.
			session (Session): The current session instance for identity tracking.
		
		Returns:
			BaseModel: A model instance populated with data from the database row.
		"""

		key = (cls, row[cls.__primary_key__])

		# Return existing instance from identity_map if available
		if session and key in session._identity_map:
			return session._identity_map[key]

		# create a new instance from row data
		instance = cls(**{col: row[col] for col in row.keys()})

		# Register in identity map for session tracking
		if session:
			session._identity_map[key] = instance

		return instance

	def _insert(self, conn):
		"""
		Insert current object into the DB.
		
		Args: 
			conn (Connection): The connection to the database.

		To Do:
			Placeholder: Dialect-aware by using connection's dialect.
		"""
		cols = [f.name for f in self._fields.values()]
		vals = [getattr(self, f.name) for f in self._fields.values()]

		placeholders = ", ".join(["?"] * len(vals))
		sql = f"INSERT INTO {self.__tablename__} ({', '.join(cols)}) VALUES ({placeholders})"
		
		# Main Sql Executer
		conn.execute(sql, vals)

	def _update(self, conn) -> None:
		"""
		Update existing record.
		
		Args: 
			conn (Connection): The connection to the database.
		"""
		# Get columns and values.
		cols = [f"{f.name}=?" for f in self._fields.values() if not f.primary_key]
		vals = [getattr(self, f.name) for f in self._fields.values() if not f.primary_key]
		
		pk_val = getattr(self, self.__primary_key__)
		vals.append(getattr(self, pk_val))
		
		sql = f"UPDATE {self.__tablename__} SET {', '.join(cols)} WHERE {pk_val}=?"
		conn.execute(sql, vals)

	def _delete(self, conn) -> None:
		"""
		Delete record.
		
		Args: 
			conn (Connection): The connection to the database.
		"""
		
		pk_val = getattr(self, self.__primary_key__)
		sql = f"DELETE FROM {self.__tablename__} WHERE {pk_val}=?"
		conn.execute(sql, [getattr(self, pk_val)]) # passes params as a list.