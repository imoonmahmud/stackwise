from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.pricing_plan import PricingPlan
from app.schemas.pricing_plan import PlanCreate, PlanUpdate

from app.models.tool import Tool

def _get_plan_or_404(db: Session, plan_id: int):
    query = select(PricingPlan).where(PricingPlan.id == plan_id)
    plan = db.execute(query).scalars().first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pricing plan not found"
        )
    return plan

def create_plan_for_tool(db: Session, tool_id: int, plan_in: PlanCreate):
    query = select(Tool).where(Tool.id == tool_id)
    tool = db.execute(query).scalars().first()
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found"
        )
    
    plan = PricingPlan(**plan_in.model_dump(), tool_id=tool_id)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan

def update_plan(db: Session, plan_id: int, plan_in: PlanUpdate):
    plan = _get_plan_or_404(db, plan_id)
    update_data = plan_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(plan, field, value)

    db.commit()
    db.refresh(plan)
    return plan

def delete_plan(db: Session, plan_id: int):
    plan = _get_plan_or_404(db, plan_id)
    db.delete(plan)
    db.commit()