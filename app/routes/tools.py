from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.tool import ToolCreate, ToolRead, ToolUpdate
from app.services.tool_service import (
    create_tool,
    get_tools, 
    get_tool_by_slug,
    update_tool,
    delete_tool
)

router = APIRouter(prefix="/tools", tags=["tools"])

@router.post("/", response_model=ToolRead, status_code=status.HTTP_201_CREATED)
def create_tool_endpoint(db: Annotated[Session, Depends(get_db)], data: ToolCreate):
    return create_tool(db, data)

@router.get("/", response_model=list[ToolRead])
def get_tools_endpoint(
    db: Annotated[Session, Depends(get_db)], 
    search: str | None = None,
    free_plan: bool | None = None,
    api_available: bool | None = None,
    pricing_model: str | None = None,
    category: str | None = None
) -> list[ToolRead]:
    return get_tools(
        db=db, 
        search=search,
        free_plan=free_plan,
        api_available=api_available,
        pricing_model=pricing_model,
        category=category
    )

@router.get("/{slug}", response_model=ToolRead)
def get_tool_by_slug_endpoint(slug: str, db: Annotated[Session, Depends(get_db)]):
    return get_tool_by_slug(db=db, slug=slug)

@router.patch("/{tool_id}", response_model=ToolRead)
def update_tool_endpoint(db: Annotated[Session, Depends(get_db)], tool_id: int, data: ToolUpdate):
    return update_tool(db, tool_id, data)

@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tool_endpoint(db: Annotated[Session, Depends(get_db)], tool_id: int):
    return delete_tool(db, tool_id)