from sqlalchemy import create_engine
from database import Base, User, SessionLocal
from auth import get_password_hash

def create_ops_user():
    """Create a default operations user for testing"""
    db = SessionLocal()
    
    # Check if ops user already exists
    existing_user = db.query(User).filter(User.username == "ops_admin").first()
    if existing_user:
        print("Operations user already exists")
        return
    
    # Create ops user
    ops_user = User(
        username="ops_admin",
        email="ops@example.com",
        hashed_password=get_password_hash("ops123456"),
        user_type="ops",
        is_verified=True
    )
    
    db.add(ops_user)
    db.commit()
    db.refresh(ops_user)
    
    print(f"Operations user created: {ops_user.username}")
    print(f"Password: ops123456")
    db.close()

if __name__ == "__main__":
    create_ops_user()
