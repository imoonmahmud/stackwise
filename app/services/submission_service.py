from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.tool_submission import ToolSubmission
from app.models.tool import Tool
from app.models.user import User
from app.schemas.submission import SubmissionCreate

def create_submission(db: Session, user: User, data: SubmissionCreate) -> ToolSubmission:
    existing_tool = db.execute(select(Tool).where(Tool.slug == data.slug)).scalars().first()
    if existing_tool:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A tool with this slug already exists."
        )

    pending_count = db.execute(
        select(func.count(ToolSubmission.id))
        .where(ToolSubmission.submitted_by_id == user.id, ToolSubmission.status == "pending")
    ).scalar()
    
    if pending_count and pending_count >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="You have too many pending submissions."
        )

    submission = ToolSubmission(
        submitted_by_id=user.id,
        name=data.name,
        slug=data.slug,
        website_url=str(data.website_url),
        short_description=data.short_description,
        pricing_model=data.pricing_model,
        note=data.note,
        status="pending"
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


def get_submission_for_user(db: Session, user: User, submission_id: int) -> ToolSubmission:
    submission = db.get(ToolSubmission, submission_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    
    if user.role not in ("editor", "admin") and submission.submitted_by_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
        
    return submission


def list_my_submissions(db: Session, user: User) -> list[ToolSubmission]:
    stmt = (
        select(ToolSubmission)
        .where(ToolSubmission.submitted_by_id == user.id)
        .order_by(ToolSubmission.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


def list_submissions(db: Session, status_filter: str = "pending", limit: int = 20, offset: int = 0) -> list[ToolSubmission]:
    stmt = (
        select(ToolSubmission)
        .where(ToolSubmission.status == status_filter)
        .order_by(ToolSubmission.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(stmt).scalars().all())


def approve_submission(db: Session, reviewer: User, submission_id: int) -> ToolSubmission:
    submission = db.execute(
        select(ToolSubmission)
        .where(ToolSubmission.id == submission_id)
        .with_for_update()
    ).scalars().first()

    if not submission:
        db.rollback() 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    if submission.status != "pending":
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Submission is no longer pending")

    existing_tool = db.execute(select(Tool).where(Tool.slug == submission.slug)).scalars().first()
    if existing_tool:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A tool with this slug already exists.")

    try:
        new_tool = Tool(
            name=submission.name,
            slug=submission.slug,
            website_url=submission.website_url,
            short_description=submission.short_description,
            pricing_model=submission.pricing_model
        )
        db.add(new_tool)
        db.flush()

        submission.status = "approved"
        submission.reviewer_id = reviewer.id
        submission.reviewed_at = datetime.now(timezone.utc)
        submission.tool_id = new_tool.id

        db.commit()
        db.refresh(submission)
        return submission
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflict during approval.")


def reject_submission(db: Session, reviewer: User, submission_id: int, review_note: str) -> ToolSubmission:
    submission = db.execute(
        select(ToolSubmission)
        .where(ToolSubmission.id == submission_id)
        .with_for_update()
    ).scalars().first()

    if not submission:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    if submission.status != "pending":
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Submission is no longer pending")

    submission.status = "rejected"
    submission.reviewer_id = reviewer.id
    submission.review_note = review_note
    submission.reviewed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(submission)
    return submission