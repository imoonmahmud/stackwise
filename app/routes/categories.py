from typing import Annotated, Literal
from decimal import Decimal
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.category import CategoryCreate, CategoryRead
from app.schemas.tool import ToolList
from app.services.category_service import create_category, get_categories, get_category_by_slug
from app.services.tool_service import get_tools
from app.core.dependencies import require_role

router = APIRouter(prefix="/categories", tags=["categories"])

@router.get('/', response_model=list[CategoryRead])
def list_categories_endpoint(db: Annotated[Session, Depends(get_db)]):
    return get_categories(db)

@router.post(
    '/', 
    response_model=CategoryRead, 
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("editor", "admin"))]
)
def create_category_endpoint(
    category_in: CategoryCreate, db: Annotated[Session, Depends(get_db)]
):
    return create_category(db, category_in)

@router.get("/{slug}", response_model=CategoryRead)
def read_category_endpoint(slug: str, db: Session = Depends(get_db)):
    return get_category_by_slug(db, slug)

@router.get('/{slug}/tools', response_model=ToolList)
def read_category_tools_endpoint(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
    search: str | None = None,
    free_plan: bool | None = None,
    api_available: bool | None = None,
    pricing_model: str | None = None,
    feature: list[str] | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort: Literal["name", "-name", "newest"] = "name",
    max_price: Decimal | None = Query(default=None, ge=0),
):
    get_category_by_slug(db, slug)
    return get_tools(
        db=db,
        search=search,
        free_plan=free_plan,
        api_available=api_available,
        pricing_model=pricing_model,
        category=slug,
        feature=feature,
        limit=limit,
        offset=offset,
        sort=sort,
        max_price=max_price
    )