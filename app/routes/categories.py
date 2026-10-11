from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.category import CategoryCreate, CategoryRead
from app.services.category_service import create_category, get_categories

router = APIRouter(prefix="/categories", tags=["categories"])

@router.get('/', response_model=list[CategoryRead])
def list_categories_endpoint(db: Annotated[Session, Depends(get_db)]):
    return get_categories(db)

@router.post('/', response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category_endpoint(
    category_in: CategoryCreate, db: Annotated[Session, Depends(get_db)]
):
    return create_category(db, category_in)