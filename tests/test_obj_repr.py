#!/usr/bin/env python3
"""
Test script to demonstrate and verify all the new QueryBuilder methods.
This will test the fluent interface design and identity map integration.
"""

# import os
# import sys
# sys.path.append('orm')

# from .connection import Connection
# from session import Session
# from adapters.sqlite import SqlDialect
# from model import BaseModel
# from fields import IntegerField, TextField, BooleanField
# from dotenv import load_dotenv

# load_dotenv()

import os
import sys
# Add root and orm folder to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # root
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'orm'))

from orm.connection import Connection
from orm.session import Session
from orm.adapters.sqlite import SqlDialect
from orm.model import BaseModel
from orm.fields import IntegerField, TextField, BooleanField
from dotenv import load_dotenv

load_dotenv()

class User(BaseModel):
    __tablename__ = 'users'
    id = IntegerField(primary_key=True)
    name = TextField(nullable=False)
    email = TextField(unique=True, nullable=False)
    age = IntegerField(nullable=True)
    is_active = BooleanField(default=True)

def test_query_builder_methods():
    db_path = os.getenv('DB_PATH')
    dialect = SqlDialect()
    conn = Connection(db_path, dialect)
    
    with Session(conn) as session:
        print()
        print("=== Testing QueryBuilder Methods ===")
        
        # Test basic queries
        print("\n1. Testing basic queries:")
        all_users = session.query(User).all()
        print()
        print(f"ALL USERS: {all_users}")
        print()
        # print(f"   All users count: {len(all_users)}")
        
        first_user = session.query(User).first()
        print()
        print(f"FIRST USERS: {first_user}")
        # print(f"   First user: {first_user.name} | {first_user.email} | {first_user.age}")
        
        # Test filtering
        print("\n2. Testing filter() method:")
        # active_users = session.query(User).filter(is_active=True).all()   # Boolean is added yet
        active_users = session.query(User).filter(is_active=1).all()
        print()
        print(f"Active users: {active_users}")
        # print(f"   Active users: {len(active_users)}")
        print()
        
        # Test chaining filters
        print("\n3. Testing method chaining:")
        young_active_users = (session.query(User)
                            .filter(age__lt=30)
                            .first())
        # print(f"   Young active users: {len(young_active_users)}")
        print(f"   Young active users: {young_active_users}")
        
        # Test ordering
        print("\n4. Testing order_by() method:")
        users_by_age = session.query(User).order_by('age', 'DESC').all()
        print()
        print(f"   Users ordered by age (DESC): {[u.age for u in users_by_age[:3]]}")
        print(f"   Users ordered by age (DESC): {users_by_age}")
        print()
        
        # Test limit and offset
        print("\n5. Testing limit() and offset() methods:")
        limited_users = session.query(User).limit(2).all()
        print()
        print(f"   Limited users (2): {len(limited_users)}")
        print(f"   Limited users (2): {limited_users}")
        print()
        
        offset_users = session.query(User).offset(1).limit(1).all()
        print(f"   Offset users (skip 1, take 1): {len(offset_users)}")
        print(f"   Offset users (skip 1, take 1): (offset_users)")
        print()
        
        # Test count
        print("\n6. Testing count() method:")
        total_count = session.query(User).count()
        active_count = session.query(User).filter(is_active=True).count()
        print()
        print(f"   Total users: {total_count}")
        print(f"   Active users: {active_count}")
        print()
        
        # Test exists
        print("\n7. Testing exists() method:")
        has_users = session.query(User).exists()
        has_inactive = session.query(User).filter(is_active=False).exists()
        print(f"   Has users: {has_users}")
        print(f"   Has inactive users: {has_inactive}")
        
        # Test pagination
        print("\n8. Testing paginate() method:")
        page1_users, total = session.query(User).paginate(1, 2)
        print()
        print(f"   Page 1 (2 per page): {len(page1_users)} items, {total} total")
        print(f"   Page 1 (2 per page): {page1_users} items, {total} total")
        print()
        
        # Test magic methods
        print("\n9. Testing magic methods:")
        query = session.query(User)
        print(f"   Query length: {len(query)}")
        print(f"   Query bool: {bool(query)}")
        
        # Test iteration
        print("\n10. Testing iteration:")
        for i, user in enumerate(session.query(User).limit(3)):
            print(f"   User {i+1}: {user.name}")
        
        # Test identity map integration
        print("\n11. Testing identity map integration:")
        user1 = session.query(User).get(1)
        user1_again = session.query(User).get(1)
        print(f"   Same instance from identity map: {user1 is user1_again}")
        
        # Test bulk operations (commented out to avoid modifying data)
        print("\n12. Testing bulk operations (dry run):")
        # Uncomment these to test actual updates/deletes
        # updated_count = session.query(User).filter(is_active=False).update(is_active=True)
        # print(f"   Updated inactive users: {updated_count}")
        
        # deleted_count = session.query(User).filter(age__lt=18).delete()
        # print(f"   Deleted users under 18: {deleted_count}")

def test_advanced_querying():
    """Test more advanced querying scenarios."""
    db_path = os.getenv('DB_PATH')
    dialect = SqlDialect()
    conn = Connection(db_path, dialect)
    
    with Session(conn) as session:
        print("\n=== Testing Advanced Querying ===")
        
        # Test complex filtering
        print("\n1. Complex filtering:")
        complex_query = (session.query(User)
                        .filter(is_active=True)
                        .filter(age__gte=25)
                        .order_by('name', 'ASC')
                        .limit(5))
        
        results = complex_query.all()
        print(f"   Complex query results: {len(results)}")
        
        # Test query building step by step
        print("\n2. Step-by-step query building:")
        query = session.query(User)
        print(f"   Initial query: {query}")
        
        query = query.filter(is_active=True)
        print(f"   After filter: {query}")
        
        query = query.order_by('age')
        print(f"   After order_by: {query}")
        
        query = query.limit(3)
        print(f"   After limit: {query}")
        
        results = query.all()
        print(f"   Final results: {len(results)}")

if __name__ == "__main__":
    test_query_builder_methods()
    test_advanced_querying()