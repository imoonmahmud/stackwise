from fastapi import HTTPException, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, or_, func, desc, asc
from typing import Literal
from decimal import Decimal

from app.models.tool import Tool
from app.schemas.tool import ToolCreate, ToolUpdate
from app.models.category import Category
from app.models.feature import Feature
from app.models.pricing_plan import PricingPlan

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

def _get_features_or_404(db: Session, feature_ids: list[int]):
    unique_ids = set(feature_ids)
    if not unique_ids:
        return []
    query = select(Feature).where(Feature.id.in_(unique_ids))
    features = db.execute(query).scalars().all()
    if len(features) != len(unique_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more feature IDs not found"
        )
    return list(features)


def create_tool(db: Session, tool_in: ToolCreate):
    categories = _get_categories_or_404(db, tool_in.category_ids)
    features = _get_features_or_404(db, tool_in.feature_ids)
    data = tool_in.model_dump(exclude={'category_ids', 'feature_ids'})
    db_tool = Tool(**data, categories=categories, features=features)

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
    free_plan: bool | None = None,
    api_available: bool | None = None,
    pricing_model: str | None = None,
    category: str | None = None,
    feature: list[str] | None = None,
    limit: int = 20,
    offset: int = 0,
    sort: Literal['name', '-name', 'newest'] = 'name',
    max_price: Decimal | None = None
) -> dict:
    query = select(Tool).options(
        selectinload(Tool.categories),
        selectinload(Tool.features),
        selectinload(Tool.pricing_plans)
        )
    
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
    if feature:
        for slug in feature:
            query = query.where(Tool.features.any(Feature.slug == slug))
    if max_price is not None:
        query = query.where(Tool.pricing_plans.any(PricingPlan.price <= max_price))

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0

    if sort == "name":
        query = query.order_by(asc(Tool.name), asc(Tool.id))
    elif sort == "-name":
        query = query.order_by(desc(Tool.name), asc(Tool.id))
    elif sort == "newest":
        query = query.order_by(desc(Tool.created_at), desc(Tool.id))

    query = query.limit(limit).offset(offset)
    items = db.execute(query).scalars().all()
    
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


def get_tool_by_slug(db: Session, slug: str):
    query = select(Tool).options(
        selectinload(Tool.categories),
        selectinload(Tool.features),
        selectinload(Tool.pricing_plans)
    ).where(Tool.slug == slug)

    tool = db.execute(query).scalars().first()
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found"
        )
    
    return tool

def update_tool(db: Session, tool_id: int, tool_in: ToolUpdate):
    tool = db.get(Tool, tool_id)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found"
        )

    update_data = tool_in.model_dump(exclude_unset=True)
    update_data = {k: v for k, v in update_data.items() if v is not None or k in ("category_ids", "feature_ids")}

    if "category_ids" in update_data:
        cat_ids = update_data.pop("category_ids")
        tool.categories = _get_categories_or_404(db, cat_ids)

    if "feature_ids" in update_data:
        feat_ids = update_data.pop("feature_ids")
        tool.features = _get_features_or_404(db, feat_ids)

    for key, value in update_data.items():
        setattr(tool, key, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A tool with this slug already exists"
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
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Connot delete tool because it is used in one or more solution steps"
        )
