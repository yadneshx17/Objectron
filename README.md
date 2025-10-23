<!-- Objectron a lightweight Python ORM 
features: 
    Connnction 
    Session
    database adapters/dialects for multi db support (database agnostics)
    Model ( class Model to table mapping )
    fields (field descriptors IntegerField, TextField etc) 
    QueryBuilder ( Builds dyanmic queries, various filters .get(), .filter(), .where(), .order_by() etc, method/filter chaning .get().first() ) -->

<!-- My Intenstional before starting this project : solely learning purpose but built this as a usable lib not that complex and advanced feature like professional ORM's but a Mini Version, will try to maintain and update this project  -->

# Objectron - a Custom Python ORM

A lightweight, **database-agnostic** Python ORM (Object-Relational Mapper) built entirely from scratch for learning, simplicity, and usability.

### Project Goal 
> To understand and implement ORM internals from first principles while keeping the codebase clean, minimal, and usable like a mini version of SQLAlchemy or Django ORM.

##  Features
Objectron provides the essential features you need from an ORM:

- **Model-to-table Mapping:** Define database tables using simple Python classes; Objectron automatically maps them to SQL tables.

- **Field Descriptors:** A set of field types like `IntegerField`, `TextField`, etc., with schema constraints such as `primary_key`, `nullable`, and `unique`.

- **Session Management (Unit of Work Pattern):** Tracks all database operations (`add`, `update`, `delete`) and commits them in a single transaction.

- **Connection Handling:** Manages the database connection lifecycle and query execution cleanly.

- **Database Agnostic (via Adapters):**  Easily extend support for multiple databases.
(Currently includes: `SQLiteDialect` adapter.)

- **Dynamic Query Builder:** A chainable (filters and query methods) API for building queries dynamically.
    - Get by primary key: `.get(1)`
    - Filter results: `.filter(age=25)`
    - Complex conditions: `.where(User.age > 20)`
    - Sorting: `.order_by('name')`
    - Chaining: `db.query(User).filter(age=30).first()` 
    - many more..

    examples: 
    ```python
    db.query(User).filter(age=25).order_by("name").all()
    db.query(User).get(1)
    db.query(User).where(User.age > 18).first()
    ```

- **Readable Object Representation:**  Results display clearly:
    ```python
    <User(id=1, name='Yadnesh', email='yadnesh@example.com', age=19)>
    ```

## Installation
For local development:

```bash
$ git clone https://github.com/yadneshx17/Objectron.git
$ cd Objectron
$ pip install -e .
```
For Use in Other Projects (e.g., FastAPI)

```bash
$ pip install objectron-0.1.0-py3-none-any.whl
```

## Quick Start Example
```python
from orm import Connection, Session, BaseModel
from orm.adapters import SqlDialect
from orm import IntegerField, TextField

# 1. Define your model
class User(BaseModel):
    __tablename__ = 'users'
    id = IntegerField(primary_key=True)
    name = TextField(nullable=False)
    email = TextField(unique=True, nullable=False)
    age = IntegerField(nullable=True)

# 2. Set up the connection (e.g., for SQLite)
dialect = SqlDialect()
conn = Connection("my_database.db", dialect)

# 3. Create the table (run this once)
User.create_table(conn) 

# 4. Use a Session to add data
with Session(conn) as db:
    new_user = User(name="Alice", email="alice@example.com", age=30)
    db.add(new_user)
    db.commit()

# 5. Query your data
with Session(conn) as db:
    # Get by ID
    user_1 = db.query(User).get(1)
    if user_1:
        print(f"User 1: {user_1.name}")

    # Filter
    alice = db.query(User).filter(name="Alice").first()
    if alice:
        print(f"Found: {alice.email}")

    # Get all users (assuming .all() method)
    all_users = db.query(User).all()
    for user in all_users:
        print(f"All Users: {user.name} ({user.age})")
```

## Example Integration with FastAPI

Seamlessly integrate Objectron with FastAPI and Pydantic for real-world APIs.

*(This example assumes you have fastapi, uvicorn, and pydantic installed.)*

```python
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel as PydanticModel
from typing import Optional, List
import os

from orm import Connection, Session, BaseModel
from orm.adapters import SqlDialect
from orm import IntegerField, TextField, FloatField

# --- 1. ORM Model Definition ---
class User(BaseModel):
    __tablename__ = 'users'
    id = IntegerField(primary_key=True)
    name = TextField(nullable=False)
    email = TextField(unique=True, nullable=False)
    age = IntegerField(nullable=True)

# --- 2. Pydantic Schemas (for API) ---

# Schema for creating a new user (request body)
class UserCreate(PydanticModel):
    name: str
    email: str
    age: Optional[int] = None

# Schema for reading a user (response body)
class UserRead(PydanticModel):
    id: int
    name: str
    email: str
    age: Optional[int] = None

    class Config:
        from_attributes = True  # Allows Pydantic to read ORM object attributes

# --- 3. Database Connection ---
dialect = SqlDialect()
db_path = os.getenv('DB_PATH', 'fastapi_example.db')
conn = Connection(db_path, dialect)

# --- 4. FastAPI App Setup ---
app = FastAPI()

# Create table on startup (using FastAPI's lifespan event is a clean way)
@app.on_event("startup")
def on_startup():
    print("[=] Starting up... creating tables if not exist.")
    User.create_table(conn)

# Dependency to get a DB session for each request
def get_db():
    with Session(conn) as db:
        yield db

# --- 5. API Endpoints ---

@app.post("/users/", response_model=UserRead)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user.
    """
    new_user = User(
        name=user.name,
        email=user.email,
        age=user.age
    )
    db.add(new_user)
    db.commit()
    return new_user  # Pydantic's UserRead will convert this ORM object

@app.get("/users/", response_model=List[UserRead])
def get_all_users(db: Session = Depends(get_db)):
    """
    Get a list of all users.
    """
    users = db.query(User).all()  # Assuming .all() returns a list
    return users

@app.get("/users/{user_id}", response_model=UserRead)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    """
    Get a single user by their ID.
    """
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/users/filter/age/{age}", response_model=List[UserRead])
def get_users_by_age(age: int, db: Session = Depends(get_db)):
    """
    Filter users by a specific age.
    """
    users = db.query(User).filter(age=age).all()
    return users
```

## Project Structure
```
orm/
 ├── __init__.py          # Exports core ORM interfaces
 ├── connection.py        # Connection management
 ├── session.py           # Session + Unit of Work pattern
 ├── model.py             # BaseModel and table mapping logic
 ├── fields.py            # Field descriptors
 ├── adapters/
 │    ├── sqlite.py       # SQLite dialect
 │    └── postgres.py     # (future)
 └── utils/
      └── query.py        # Query builder logic
```

## Future Plans
- Support for more dialects (PostgreSQL, MySQL)
- Async ORM support
- Relationship handling (OneToMany, ManyToMany)
- Query optimization layer
- Migrations and schema sync

## Note

*This project started as a **learning experiment** and evolved into a **usable**, **modular mini ORM**.<br>
I plan to continue maintaining Objectron — improving documentation, adding new features, and keeping it a **learning-friendly open-source ORM reference**.*

### 📝 License

Released under the **MIT License**.
Feel free to use, learn from, and improve Objectron contributions and feedback are always welcome!