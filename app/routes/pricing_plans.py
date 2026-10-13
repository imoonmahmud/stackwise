from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.pricing_plan import PlanCreate, PlanUpdate, PlanRead
from app.services.pricing_plan_service import create_plan_for_tool, update_plan, delete_plan

router = APIRouter(tags=["pricing-plans"])

@router.post("/tools/{tool_id}/pricing-plans", response_model=PlanRead, status_code=status.HTTP_201_CREATED)
def create_pricing_plan(tool_id: int, plan_in: PlanCreate, db: Session = Depends(get_db)):
    return create_plan_for_tool(db, tool_id, plan_in)

@router.patch("/pricing-plans/{plan_id}", response_model=PlanRead)
def patch_pricing_plan(plan_id: int, plan_in: PlanUpdate, db: Session = Depends(get_db)):
    return update_plan(db, plan_id, plan_in)

@router.delete("/pricing-plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_pricing_plan(plan_id: int, db: Session = Depends(get_db)):
    delete_plan(db, plan_id)
    return None