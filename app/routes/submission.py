from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import Literal

from app.database import get_db
from app.models.user import User
from app.schemas.submission import SubmissionCreate, SubmissionRead, ReviewReject
from app.core.dependencies import get_current_user, require_role
from app.services.submission_service import (
    create_submission,
    get_submission_for_user,
    list_my_submissions,
    list_submissions,
    approve_submission,
    reject_submission
)

router = APIRouter(tags=["submissions"])

@router.post("/submissions", response_model=SubmissionRead, status_code=status.HTTP_201_CREATED)
def create_submission_endpoint(
    data: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return create_submission(db, current_user, data)


@router.get("/submissions/mine", response_model=list[SubmissionRead])
def get_my_submissions_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return list_my_submissions(db, current_user)


@router.get("/submissions/{submission_id}", response_model=SubmissionRead)
def get_submission_endpoint(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_submission_for_user(db, current_user, submission_id)


@router.get("/admin/submissions", response_model=list[SubmissionRead])
def list_all_submissions_endpoint(
    status: Literal["pending", "approved", "rejected"] = "pending",
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("editor", "admin"))
):
    return list_submissions(db, status_filter=status, limit=limit, offset=offset)


@router.post("/admin/submissions/{id}/approve", response_model=SubmissionRead)
def approve_submission_endpoint(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("editor", "admin"))
):
    return approve_submission(db, current_user, id)


@router.post("/admin/submissions/{id}/reject", response_model=SubmissionRead)
def reject_submission_endpoint(
    id: int,
    data: ReviewReject,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("editor", "admin"))
):
    return reject_submission(db, current_user, id, data.review_note)