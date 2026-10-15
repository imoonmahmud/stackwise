from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.comparison import ComparisonCreate, ComparisonListItem, ComparisonRead
from app.core.dependencies import require_role
from app.services.comparison_service import (
    create_comparison,
    delete_comparison,
    get_comparison_by_slug,
    get_comparisons,
)

router = APIRouter(prefix="/comparisons", tags=["comparisons"])

@router.get("/", response_model=list[ComparisonListItem])
def read_comparisons(db: Annotated[Session, Depends(get_db)]):
    return get_comparisons(db)

@router.post(
    "/", 
    response_model=ComparisonRead, 
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("editor", "admin"))]
)
def create_new_comparison(comparison_in: ComparisonCreate, db: Annotated[Session, Depends(get_db)]):
    return create_comparison(db, comparison_in)

@router.get("/{slug}", response_model=ComparisonRead)
def read_comparison(slug: str, db: Annotated[Session, Depends(get_db)]):
    return get_comparison_by_slug(db, slug)

@router.delete(
    "/{comparison_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("editor", "admin"))]
)
def remove_comparison(comparison_id: int, db: Annotated[Session, Depends(get_db)]):
    delete_comparison(db, comparison_id)
    return None