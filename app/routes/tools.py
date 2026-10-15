from typing import Annotated, Literal
from decimal import Decimal

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.tool import ToolCreate, ToolRead, ToolUpdate, ToolList
from app.core.dependencies import require_role, get_current_user
from app.services.saved_tool_service import save_tool, unsave_tool
from app.services.tool_service import (
    create_tool,
    get_tools, 
    get_tool_by_slug,
    update_tool,
    delete_tool
)

router = APIRouter(prefix="/tools", tags=["tools"])

@router.post("/{tool_id}/save", status_code=status.HTTP_204_NO_CONTENT)
def bookmark_tool(
    tool_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    save_tool(db, current_user, tool_id)
    return None


@router.delete("/{tool_id}/save", status_code=status.HTTP_204_NO_CONTENT)
def unbookmark_tool(
    tool_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    unsave_tool(db, current_user, tool_id)
    return None

@router.post(
    "/", 
    response_model=ToolRead, 
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("editor", "admin"))]
)
def create_tool_endpoint(db: Annotated[Session, Depends(get_db)], data: ToolCreate):
    return create_tool(db, data)

@router.get("/", response_model=ToolList)
def get_tools_endpoint(
    db: Annotated[Session, Depends(get_db)], 
    search: str | None = None,
    free_plan: bool | None = None,
    api_available: bool | None = None,
    pricing_model: str | None = None,
    category: str | None = None,
    feature: list[str] | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort: Literal["name", "-name", "newest"] = "name",
    max_price: Decimal | None = Query(default=None, ge=0)
):
    return get_tools(
        db=db, 
        search=search,
        free_plan=free_plan,
        api_available=api_available,
        pricing_model=pricing_model,
        category=category,
        feature=feature,
        limit=limit,
        offset=offset,
        sort=sort,
        max_price=max_price
    )

@router.get("/{slug}", response_model=ToolRead)
def get_tool_by_slug_endpoint(slug: str, db: Annotated[Session, Depends(get_db)]):
    return get_tool_by_slug(db=db, slug=slug)

@router.patch(
    "/{tool_id}", 
    response_model=ToolRead,
    dependencies=[Depends(require_role("editor", "admin"))]
)
def update_tool_endpoint(db: Annotated[Session, Depends(get_db)], tool_id: int, data: ToolUpdate):
    return update_tool(db, tool_id, data)

@router.delete(
    "/{tool_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("editor", "admin"))]
)
def delete_tool_endpoint(db: Annotated[Session, Depends(get_db)], tool_id: int):
    return delete_tool(db, tool_id)