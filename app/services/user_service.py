from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate

DUMMY_HASH = hash_password("not-a-real-password-timing-mitigation")

def register_user(db: Session, user_in: UserCreate):
    user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        role="user",
        is_active=True
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists"
        )

def authenticate_user(db: Session, email: str, password: str):
    normalized_email = email.strip().lower()
    query = select(User).where(User.email == normalized_email)
    user = db.execute(query).scalars().first()
    
    if user is None:
        verify_password(password, DUMMY_HASH)
        return None
        
    if not verify_password(password, user.hashed_password):
        return None
        
    return user