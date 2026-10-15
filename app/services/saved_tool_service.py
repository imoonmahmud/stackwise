from fastapi import HTTPException, status
from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.saved_tool import saved_tools
from app.models.tool import Tool
from app.models.user import User


def _get_tool_or_404(db: Session, tool_id: int) -> Tool:
    tool = db.get(Tool, tool_id)
    if tool is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
    return tool


def save_tool(db: Session, user: User, tool_id: int) -> None:
    _get_tool_or_404(db, tool_id)
    stmt = insert(saved_tools).values(user_id=user.id, tool_id=tool_id).on_conflict_do_nothing()
    try:
        db.execute(stmt)
        db.commit()
    except IntegrityError:      # the tool was deleted between the check and the insert
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")


def unsave_tool(db: Session, user: User, tool_id: int) -> None:
    _get_tool_or_404(db, tool_id)
    db.execute(
        delete(saved_tools).where(
            saved_tools.c.user_id == user.id,
            saved_tools.c.tool_id == tool_id,
        )
    )
    db.commit()