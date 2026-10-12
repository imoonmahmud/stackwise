from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.category import CategoryCreate, CategoryRead
from app.schemas.tool import ToolRead
from app.services.category_service import create_category, get_categories, get_category_by_slug
from app.services.tool_service import get_tools

router = APIRouter(prefix="/categories", tags=["categories"])

@router.get('/', response_model=list[CategoryRead])
def list_categories_endpoint(db: Annotated[Session, Depends(get_db)]):
    return get_categories(db)

@router.post('/', response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category_endpoint(
    category_in: CategoryCreate, db: Annotated[Session, Depends(get_db)]
):
    return create_category(db, category_in)

@router.get("/{slug}", response_model=CategoryRead)
def read_category_endpoint(slug: str, db: Session = Depends(get_db)):
    return get_category_by_slug(db, slug)

@router.get('/{slug}/tools', response_model=list[ToolRead])
def read_category_tools_endpoint(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
    search: str | None = None,
    free_plan: bool | None = None,
    api_available: bool | None = None,
    pricing_model: str | None = None
):
    get_category_by_slug(db, slug)

    return get_tools(
        db=db,
        search=search,
        free_plan=free_plan,
        api_available=api_available,
        pricing_model=pricing_model,
        category=slug
    )