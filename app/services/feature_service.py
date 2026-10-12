from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.feature import Feature
from app.schemas.feature import FeatureCreate


def create_feature(db: Session, feature_in: FeatureCreate):
    feature = Feature(**feature_in.model_dump())
    db.add(feature)

    try:
        db.commit()
        db.refresh(feature)
        return feature
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Feature with this name or slug already exists"
        )

def get_features(db: Session):
    query = select(Feature).order_by(Feature.name.asc())
    result = db.execute(query)
    return list(result.scalars().all())

def get_feature_by_slug(db: Session, slug: str):
    query = select(Feature).where(Feature.slug == slug)
    feature = db.execute(query).scalars().first()
    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature not found"
        )
    return feature