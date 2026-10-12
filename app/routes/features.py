from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.feature import FeatureCreate, FeatureRead
from app.services.feature_service import create_feature, get_features, get_feature_by_slug

router = APIRouter(prefix="/features", tags=["features"])

@router.post("/", response_model=FeatureRead, status_code=status.HTTP_201_CREATED)
def create_new_feature(feature_in: FeatureCreate, db: Annotated[Session, Depends(get_db)]):
    return create_feature(db, feature_in)

@router.get("/", response_model=list[FeatureRead])
def read_features(db: Annotated[Session, Depends(get_db)]):
    return get_features(db)


@router.get('/{slug}', response_model=FeatureRead)
def get_feature_by_slug_endpoint(slug: str, db: Annotated[Session, Depends(get_db)]):
    return get_feature_by_slug(db=db, slug=slug)