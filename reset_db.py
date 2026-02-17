import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config.database import Base, engine
import src.models  # Register all models

def reset_database():
    print("🗑️  Dropping all tables...")
    # Reflect existing tables to ensure we drop them even if models changed (though drop_all relies on metadata)
    # Actually drop_all only drops tables known to metadata.
    # If there are tables NOT in metadata, they won't be dropped.
    # But since we want to sync metadata with DB, this is usually fine unless we renamed tables.
    Base.metadata.drop_all(bind=engine)
    
    print("✨ Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database reset successfully!")

if __name__ == "__main__":
    confirm = input("This will DELETE ALL DATA. Type 'yes' to proceed: ")
    if confirm.lower() == "yes":
        reset_database()
    else:
        print("Cancelled.")
