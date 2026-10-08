from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models.tool import Tool
from app.schemas.tool import ToolCreate

class DuplicateSlugError(Exception):
    pass

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
        raise DuplicateSlugError
    db.refresh(new_tool)

    return new_tool