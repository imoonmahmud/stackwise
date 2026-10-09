from typing import Annotated

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from app.models.tool import Tool
from app.schemas.tool import ToolCreate, ToolUpdate


def create_tool(db: Session, data: ToolCreate):
    new_tool = Tool(
        name=data.name,
        slug=data.slug,
        short_description=data.short_description
    )
    db.add(new_tool)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Name or slug already exist."
        )
    
    db.refresh(new_tool)
    return new_tool


def get_tools(db: Session):
    result = db.execute(select(Tool).order_by(Tool.name))
    return result.scalars().all()

def get_tool_by_slug(db: Session, slug: str):
    result = db.execute(select(Tool).where(Tool.slug == slug))
    tool = result.scalars().first()
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found"
        )
    
    return tool

def update_tool(db: Session, tool_id: int, data: ToolUpdate):
    result = db.execute(select(Tool).where(Tool.id == tool_id))
    tool = result.scalars().first()
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found"
        )

    fields = data.model_dump(exclude_unset=True, exclude_none=True)
    for key, value in fields.items():
        setattr(tool, key, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Name or slug already exist."
        )

    db.refresh(tool)
    return tool

def delete_tool(db: Session, tool_id: int):
    result = db.execute(select(Tool).where(Tool.id == tool_id))
    tool = result.scalars().first()
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found"
        )

    db.delete(tool)
    db.commit()
