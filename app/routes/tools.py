from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.tool import ToolCreate, ToolRead
from app.services.tool_service import create_tool, DuplicateSlugError

router = APIRouter(prefix="/tools", tags=["tools"])

@router.post(
    "/",
    response_model=ToolRead,
    status_code=status.HTTP_201_CREATED
)
def create_tool_endpoint(
    db: Annotated[Session, Depends(get_db)],
    data: ToolCreate
):
    try:
        return create_tool(db, data)
    except DuplicateSlugError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A tool with this slug already exists"
        )
