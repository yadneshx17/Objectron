from connection import Connection
from adapters.sqlite import SqlDialect
import os
from dotenv import load_dotenv
from model import BaseModel
from fields import IntegerField, TextField, BooleanField

load_dotenv()
db_path = os.getenv('DB_PATH')
dialect = SqlDialect()

class User(BaseModel):
    __tablename__ = 'users'
    
    id = IntegerField(primary_key=True)
    name = TextField(nullable=False)
    email = TextField(unique=True, nullable=False)
    age = IntegerField(nullable=True)
    is_active = BooleanField(default=True)


# AI GENERATED TESTS
# Demo usage of the User model
if __name__ == "__main__":
    with Connection(db_path, dialect) as db:
        # Create the users table
        print("Creating users table...")
        User.create_table(db)
        
        # Create some user instances
        print("Creating user instances...")
        user1 = User(name="Alice Johnson", email="alice@example.com", age=28)
        user2 = User(name="Bob Smith", email="bob@example.com", age=35)
        user3 = User(name="Charlie Brown", email="charlie@example.com")  # age will be None
        
        # Insert users into database
        print("Inserting users into database...")
        user1._insert(db)
        user2._insert(db)
        user3._insert(db)
        
        # Query and display users
        print("Querying users from database...")
        cursor = db.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        
        print(f"\nFound {len(rows)} users:")
        for row in rows:
            print(f"ID: {row['id']}, Name: {row['name']}, Email: {row['email']}, Age: {row['age']}, Active: {bool(row['is_active'])}")
        
        # Update a user
        print("\nUpdating user...")
        user1.age = 29
        user1._update(db)
        
        # Query again to see the update
        cursor = db.execute("SELECT * FROM users WHERE id = ?", (user1.id,))
        updated_user = cursor.fetchone()

        # ERROR
        # print(f"Updated user: ID: {updated_user['id']}, Name: {updated_user['name']}, Age: {updated_user['age']}")
        
        # print("\nDemo completed successfully!")   
