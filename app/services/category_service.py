from fastapi import HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.category import Category
from app.schemas.category import CategoryCreate

def get_categories(db: Session):
    query = select(Category).order_by(Category.name.asc())
    result = db.execute(query)
    return list(result.scalars().all())



def create_category(db: Session, category_in: CategoryCreate):
    existing = db.execute(
        select(Category).where(
            or_(Category.name == category_in.name, Category.slug == category_in.slug)
        )
    ).scalars().first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category with this name or slugh already exists"
        )

    db_category = Category(**category_in.model_dump())
    db.add(db_category)
    try:
        db.commit()
        db.refresh(db_category)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category with this name or slug already exists."
        )
    return db_category


