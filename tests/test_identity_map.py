"""
Test script to verify that the identity map is working correctly.
This will test that:
1. First get() call fetches from database and stores in identity map
2. Second get() call returns the same instance from identity map (no database query)
"""

import os
import sys
sys.path.append('orm')

from connection import Connection
from session import Session
from adapters.sqlite import SqlDialect
from model import BaseModel
from fields import IntegerField, TextField, BooleanField
from dotenv import load_dotenv

load_dotenv()

class User(BaseModel):
    __tablename__ = 'users'
    id = IntegerField(primary_key=True)
    name = TextField(nullable=False)
    email = TextField(unique=True, nullable=False)
    age = IntegerField(nullable=True)
    is_active = BooleanField(default=True)

def test_identity_map():
    db_path = os.getenv('DB_PATH')
    dialect = SqlDialect()
    conn = Connection(db_path, dialect)
    
    with Session(conn) as session:
        print("=== Testing Identity Map ===")
        print(f"Initial identity map: {session._identity_map}")
        
        # First get() call - should fetch from database
        print("\n1. First get() call for user with id=4:")
        user1 = session.query(User).get(4)
        print(f"   Retrieved user: {user1}")
        print(f"   User object id: {id(user1)}")
        print(f"   Identity map after first get: {session._identity_map}")
        
        # Second get() call - should return same instance from identity map
        print("\n2. Second get() call for same user (id=4):")
        user2 = session.query(User).get(4)
        print(f"   Retrieved user: {user2}")
        print(f"   User object id: {id(user2)}")
        print(f"   Identity map after second get: {session._identity_map}")
        
        # Verify they are the same instance
        print(f"\n3. Are they the same instance? {user1 is user2}")
        print(f"   Object equality: {user1 == user2}")
        
        # Test with different user
        print("\n4. Getting different user (id=1):")
        user3 = session.query(User).get(1)
        print(f"   Retrieved user: {user3}")
        print(f"   User object id: {id(user3)}")
        print(f"   Identity map after third get: {session._identity_map}")
        
        # Verify all users are different instances
        print(f"\n5. All users are different instances:")
        print(f"   user1 is user3: {user1 is user3}")
        print(f"   user2 is user3: {user2 is user3}")

if __name__ == "__main__":
    test_identity_map()