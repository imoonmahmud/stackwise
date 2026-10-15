import getpass

from app.database import SessionLocal
from app.models.user import User
from app.core.security import hash_password

def create_admin():
    email = input("Enter admin email: ").strip().lower()
    password = getpass.getpass("Enter admin password: ")
    
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print("Error: User with this email already exists.")
            return
            
        admin_user = User(
            email=email,
            hashed_password=hash_password(password),
            role="admin",
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        print(f"Admin user '{email}' created successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()