"""
Database Cleanup Script
Use this to clear test data between test runs
"""

import sys
import os

# Add your project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Update this with your database URL
DATABASE_URL = "postgresql://postgres:shashank7@localhost:5432/mydb"  # Change to your actual database URL

def cleanup_test_data():
    """Remove all test users and related data"""
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("🧹 Cleaning up test data...")
        
        # Delete in correct order due to foreign key constraints
        
        # 1. Delete connections
        result = db.execute(text("DELETE FROM connections"))
        db.commit()
        print(f"   ✓ Deleted {result.rowcount} connections")
        
        # 2. Delete portfolio items
        result = db.execute(text("DELETE FROM user_portfolio"))
        db.commit()
        print(f"   ✓ Deleted {result.rowcount} portfolio items")
        
        # 3. Delete user skills
        result = db.execute(text("DELETE FROM user_skills"))
        db.commit()
        print(f"   ✓ Deleted {result.rowcount} user skills")
        
        # 4. Delete users (optional - comment out if you want to keep users)
        result = db.execute(text("DELETE FROM users WHERE email LIKE '%@example.com'"))
        db.commit()
        print(f"   ✓ Deleted {result.rowcount} test users")
        
        # 5. Optionally delete skills (uncomment if you want fresh skills each time)
        # result = db.execute(text("DELETE FROM skills"))
        # db.commit()
        # print(f"   ✓ Deleted {result.rowcount} skills")
        
        print("\n✅ Cleanup completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Cleanup failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def cleanup_everything():
    """Nuclear option - delete ALL data"""
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("☢️  NUCLEAR CLEANUP - Deleting ALL data...")
        response = input("Are you sure? This will delete EVERYTHING! (yes/no): ")
        
        if response.lower() != 'yes':
            print("Cancelled.")
            return False
        
        # Delete in reverse dependency order
        tables = [
            "connections",
            "user_portfolio", 
            "user_skills",
            "skills",
            "users"
        ]
        
        for table in tables:
            try:
                result = db.execute(text(f"DELETE FROM {table}"))
                db.commit()
                print(f"   ✓ Cleared {table}: {result.rowcount} rows deleted")
            except Exception as e:
                print(f"   ⚠ Could not clear {table}: {e}")
        
        print("\n✅ Complete cleanup finished!")
        return True
        
    except Exception as e:
        print(f"\n❌ Cleanup failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def show_current_data():
    """Display current database state"""
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("\n📊 Current Database State:")
        print("=" * 60)
        
        tables = {
            "users": "SELECT COUNT(*) FROM users",
            "skills": "SELECT COUNT(*) FROM skills",
            "user_skills": "SELECT COUNT(*) FROM user_skills",
            "user_portfolio": "SELECT COUNT(*) FROM user_portfolio",
            "connections": "SELECT COUNT(*) FROM connections"
        }
        
        for table, query in tables.items():
            try:
                result = db.execute(text(query))
                count = result.scalar()
                print(f"   {table:.<20} {count} records")
            except Exception as e:
                print(f"   {table:.<20} Error: {e}")
        
        print("=" * 60)
        
        # Show superuser status
        print("\n👤 Superuser Status:")
        try:
            result = db.execute(text(
                "SELECT id, email, name, is_superuser FROM users WHERE email = 'superuser@example.com'"
            ))
            user = result.fetchone()
            
            if user:
                print(f"   Email: {user[1]}")
                print(f"   Name: {user[2]}")
                print(f"   Is Superuser: {user[3]}")
            else:
                print("   Superuser not found")
        except Exception as e:
            print(f"   Error checking superuser: {e}")
        
        print()
        
    except Exception as e:
        print(f"❌ Error displaying data: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Database Cleanup Utility")
    print("=" * 60)
    
    print("\nOptions:")
    print("1. Show current database state")
    print("2. Clean test data only (keeps skills)")
    print("3. NUCLEAR - Delete everything")
    print("4. Exit")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "1":
        show_current_data()
    elif choice == "2":
        show_current_data()
        cleanup_test_data()
        show_current_data()
    elif choice == "3":
        show_current_data()
        cleanup_everything()
        show_current_data()
    elif choice == "4":
        print("Exiting...")
    else:
        print("Invalid option")
    
    print("\n" + "=" * 60)