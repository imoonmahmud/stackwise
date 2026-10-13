from fastapi import HTTPException, status
from sqlalchemy import select, asc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.solution import Solution
from app.models.solution_tool import SolutionTool
from app.models.tool import Tool
from app.schemas.solution import SolutionCreate, SolutionUpdate

def get_solutions(db: Session) -> list[Solution]:
    query = select(Solution).order_by(asc(Solution.title))
    return db.execute(query).scalars().all()

def get_solution_by_slug(db: Session, slug: str) -> Solution:
    query = select(Solution).options(
        selectinload(Solution.steps).selectinload(SolutionTool.tool)
    ).where(Solution.slug == slug)
    solution = db.execute(query).scalars().first()
    if not solution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solution not found"
        )
    return solution

def get_solution_by_id(db: Session, solution_id: int) -> Solution:
    query = select(Solution).options(
        selectinload(Solution.steps).selectinload(SolutionTool.tool)
    ).where(Solution.id == solution_id)
    solution = db.execute(query).scalars().first()
    if not solution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solution not found"
        )
    return solution

def create_solution(db: Session, solution_in: SolutionCreate) -> Solution:
    tool_ids = [step.tool_id for step in solution_in.steps]
    if tool_ids:
        tools_query = select(Tool).where(Tool.id.in_(tool_ids))
        found_tools = db.execute(tools_query).scalars().all()
        if len(found_tools) != len(set(tool_ids)):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more tools not found"
            )

    data = solution_in.model_dump(exclude={"steps"})
    
    solution = Solution(
        **data,
        steps=[
            SolutionTool(
                tool_id=step_data.tool_id,
                step_order=idx,
                role=step_data.role,
                note=step_data.note
            )
            for idx, step_data in enumerate(solution_in.steps, start=1)
        ]
    )

    db.add(solution)

    try:
        db.commit()
        return get_solution_by_id(db, solution.id)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Solution with this slug already exists"
        )

def update_solution(db: Session, solution_id: int, solution_in: SolutionUpdate) -> Solution:
    solution = get_solution_by_id(db, solution_id)
    update_data = solution_in.model_dump(exclude_unset=True)

    if "steps" in update_data:
        steps_data = update_data.pop("steps")
        tool_ids = [s.tool_id for s in solution_in.steps]
        if tool_ids:
            tools_query = select(Tool).where(Tool.id.in_(tool_ids))
            found_tools = db.execute(tools_query).scalars().all()
            if len(found_tools) != len(set(tool_ids)):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="One or more tools not found"
                )
        
        solution.steps.clear()
        db.flush()

        solution.steps = [
            SolutionTool(
                tool_id=s.tool_id,
                step_order=idx,
                role=s.role,
                note=s.note
            )
            for idx, s in enumerate(solution_in.steps, start=1)
        ]

    for field, value in update_data.items():
        setattr(solution, field, value)

    try:
        db.commit()
        return get_solution_by_id(db, solution.id)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Solution with this slug already exists"
        )

def delete_solution(db: Session, solution_id: int) -> None:
    solution = get_solution_by_id(db, solution_id)
    db.delete(solution)
    db.commit()