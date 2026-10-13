from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.solution import SolutionCreate, SolutionListItem, SolutionRead, SolutionUpdate
from app.services.solution_service import (
    create_solution,
    delete_solution,
    get_solution_by_slug,
    get_solutions,
    update_solution,
)

router = APIRouter(prefix="/solutions", tags=["solutions"])

@router.get("/", response_model=list[SolutionListItem])
def read_solutions(db: Annotated[Session, Depends(get_db)]):
    return get_solutions(db)

@router.post("/", response_model=SolutionRead, status_code=status.HTTP_201_CREATED)
def create_new_solution(solution_in: SolutionCreate, db: Annotated[Session, Depends(get_db)]):
    return create_solution(db, solution_in)

@router.get("/{slug}", response_model=SolutionRead)
def read_solution(slug: str, db: Annotated[Session, Depends(get_db)]):
    return get_solution_by_slug(db, slug)

@router.patch("/{solution_id}", response_model=SolutionRead)
def patch_solution(solution_id: int, solution_in: SolutionUpdate, db: Annotated[Session, Depends(get_db)]):
    return update_solution(db, solution_id, solution_in)

@router.delete("/{solution_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_solution(solution_id: int, db: Annotated[Session, Depends(get_db)]):
    delete_solution(db, solution_id)
    return None