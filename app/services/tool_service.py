from typing import Annotated

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, or_

from app.models.tool import Tool
from app.schemas.tool import ToolCreate, ToolUpdate
from app.models.category import Category

def _get_categories_or_404(db: Session, category_id: list[int]):
    unique_ids = set(category_id)
    if not unique_ids:
        return []

    categories = db.execute(
        select(Category).where(Category.id.in_(unique_ids))
    ).scalars().all()

    if len(categories) != len(unique_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more categories not found"
        )
    return list(categories)


def create_tool(db: Session, tool_in: ToolCreate):
    categories = _get_categories_or_404(db, tool_in.category_ids)

    data = tool_in.model_dump(exclude={'category_ids'})
    db_tool = Tool(**data, categories=categories)

    db.add(db_tool)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A tool with this slug already exists"
        )
    db.refresh(db_tool)
    return db_tool
    

def get_tools(
    db: Session, 
    search: str | None = None,
    free_plan: str | None = None,
    api_available: bool | None = None,
    pricing_model: bool | None = None,
    category: str | None = None
) -> list[Tool]:
    query = select(Tool).options(selectinload(Tool.categories))

    if search and search.strip():
        search_term = search.strip()
        query = query.where(
            or_(
                Tool.name.icontains(search_term, autoescape=True),
                Tool.short_description.icontains(search_term, autoescape=True)
            )
        )

    if free_plan is not None:
        query = query.where(Tool.has_free_plan == free_plan)
    if api_available is not None:
        query = query.where(Tool.api_available == api_available)
    if pricing_model is not None:
        query = query.where(Tool.pricing_model == pricing_model)

    if category is not None:
        query = query.where(Tool.categories.any(Category.slug == category))

    query = query.order_by(Tool.name.asc())
    result = db.execute(query)
    return list(result.scalars().all())


def get_tool_by_slug(db: Session, slug: str):
    tool = db.execute(
        select(Tool).where(Tool.slug == slug)
        .options(selectinload(Tool.categories))
    ).scalars().first()

    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found"
        )
    
    return tool

def update_tool(db: Session, tool_id: int, tool_in: ToolUpdate):
    db_tool = db.get(Tool, tool_id)
    if not db_tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found"
        )

    fields = tool_in.model_dump(exclude_unset=True, exclude_none=True)

    category_ids = fields.pop('category_ids', None)
    if category_ids is not None:
        db_tool.categories = _get_categories_or_404(db, category_ids)

    for key, value in fields.items():
        setattr(db_tool, key, value)

    try:
        db.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A tool with this slug already exists"
        )
    db.refresh(db_tool)
    return db_tool


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
