from .fields import Field
from .connection import Connection
from .adapters.sqlite import SqlDialect
import os
from dotenv import load_dotenv

load_dotenv()
db_path = os.getenv('DB_PATH')
dialect = SqlDialect()

conn = Connection(db_path, dialect)

class MetaClass(type):
	"""
		The metaclass foreman that builds our model classes.
		It inspects the class definition, finds all the Field objects,
		and stores them in a convenient `_fields` dictionary.
	"""
	
	def __new__(cls, name, bases, attrs):
		if name == 'BaseModel':
			return super().__new__(cls, name, bases, attrs) # new instance of the class

		# Find all the blueprints (Field objects)
		fields = {
			key: value for key, value in attrs.items() if isinstance(value, Field) 
		}

		# Store the stolen goods on the class itself
		attrs['__tablename__'] = attrs.get('__tablename__', name.lower() + "s")
		attrs['_fields'] = fields

		# Finding Primary Keys
		pk_name = None 
		for field_name, field_obj in fields.items():
			if field_obj.primary_key:
				print(f"FOUND ->  {field_obj} : {field_name}")
				pk_name = field_name
				break

		attrs['__primary_key__'] = pk_name

		cls = super().__new__(cls, name, bases, attrs)
		return cls

class BaseModel(metaclass=MetaClass):
	def __init__(self, **kwargs):
		for key, value in kwargs.items():
			setattr(self, key, value) # set the value of named attribute of an object.

	@classmethod
	def create_table(cls, conn):
		"""Generate and execute CREATE TABLE statement."""
		columns = [field.to_sql() for field in cls._fields.values()]
		sql = f"CREATE TABLE IF NOT EXISTS {cls.__tablename__} ({', '.join(columns)})"
		conn.execute(sql)

	def _insert(self, conn):
		"""Insert current object into the DB."""
		cols = [f.name for f in self._fields.values()]
		vals = [getattr(self, f.name) for f in self._fields.values()]
		placeholders = ", ".join(["?"] * len(vals))
		sql = f"INSERT INTO {self.__tablename__} ({', '.join(cols)}) VALUES ({placeholders})"
		conn.execute(sql, vals)

	def _update(self, conn):
		"""Update existing record."""
		pk = [f for f in self._fields.values() if f.primary_key][0]
		cols = [f"{f.name}=?" for f in self._fields.values() if not f.primary_key]
		vals = [getattr(self, f.name) for f in self._fields.values() if not f.primary_key]
		vals.append(getattr(self, pk.name))
		sql = f"UPDATE {self.__tablename__} SET {', '.join(cols)} WHERE {pk.name}=?"
		conn.execute(sql, vals)

	def _delete(self, conn):
		"""Delete record."""
		pk = [f for f in self._fields.values() if f.primary_key][0]
		sql = f"DELETE FROM {self.__tablename__} WHERE {pk.name}=?"
		conn.execute(sql, [getattr(self, pk.name)])

	@classmethod
	def from_row(cls, row):
		"""Convert a DB row into a model instance."""
		return cls(**row) 