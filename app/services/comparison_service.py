from fastapi import HTTPException, status
from sqlalchemy import select, asc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from app.models.comparison import Comparison
from app.models.comparison_tool import ComparisonTool
from app.models.tool import Tool
from app.models.feature import Feature
from app.schemas.comparison import ComparisonCreate

def build_comparison_table(tools: list[Tool]) -> list[dict]:
    all_features = sorted(
        {f for tool in tools for f in tool.features},
        key=lambda x: x.name
    )

    rows = []

    rows.append({
        "label": "Pricing model",
        "values": [tool.pricing_model for tool in tools]
    })

    rows.append({
        "label": "Free plan",
        "values": [tool.has_free_plan for tool in tools]
    })

    rows.append({
        "label": "API",
        "values": [tool.api_available for tool in tools]
    })

    starting_prices = []
    for tool in tools:
        valid_prices = [
            plan.price for plan in tool.pricing_plans
            if plan.price is not None and plan.price > 0 and not plan.is_free
        ]
        if valid_prices:
            starting_prices.append(f"${min(valid_prices):.2f}")
        else:
            starting_prices.append(None)
    
    rows.append({
        "label": "Starting price",
        "values": starting_prices
    })

    for feature in all_features:
        feature_values = [
            any(f.id == feature.id for f in tool.features)
            for tool in tools
        ]
        rows.append({
            "label": feature.name,
            "values": feature_values
        })

    return rows

def get_comparisons(db: Session) -> list[dict]:
    query = select(Comparison).options(selectinload(Comparison.tools)).order_by(asc(Comparison.slug))
    comparisons = db.execute(query).scalars().all()
    return [
        {
            "slug": c.slug,
            "summary": c.summary,
            "tool_count": len(c.tools)
        }
        for c in comparisons
    ]

def get_comparison_by_slug(db: Session, slug: str) -> dict:
    query = select(Comparison).options(
        selectinload(Comparison.tools).selectinload(ComparisonTool.tool).options(
            selectinload(Tool.features), selectinload(Tool.pricing_plans)
        )
    ).where(Comparison.slug == slug)
    
    comparison = db.execute(query).scalars().first()
    if not comparison:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comparison not found")

    sorted_links = sorted(comparison.tools, key=lambda x: x.position)
    tools = [link.tool for link in sorted_links]
    tool_briefs = [{"id": t.id, "name": t.name, "slug": t.slug} for t in tools]

    rows = build_comparison_table(tools)

    return {
        "slug": comparison.slug,
        "summary": comparison.summary,
        "created_at": comparison.created_at,
        "tools": tool_briefs,
        "rows": rows
    }

def create_comparison(db: Session, comparison_in: ComparisonCreate) -> dict:
    tools_query = select(Tool).where(Tool.id.in_(comparison_in.tool_ids)).options(
        selectinload(Tool.features), selectinload(Tool.pricing_plans)
    )
    found_tools = db.execute(tools_query).scalars().all()
    
    if len(found_tools) != len(set(comparison_in.tool_ids)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more tools not found")

    tool_map = {t.id: t for t in found_tools}
    ordered_tools = [tool_map[tid] for tid in comparison_in.tool_ids]

    sorted_tool_slugs = sorted([t.slug for t in ordered_tools])
    canonical_slug = "-vs-".join(sorted_tool_slugs)

    comparison = Comparison(
        slug=canonical_slug,
        summary=comparison_in.summary,
        tools=[
            ComparisonTool(
                tool_id=t.id,
                position=idx
            )
            for idx, t in enumerate(ordered_tools, start=1)
        ]
    )

    db.add(comparison)
    try:
        db.commit()
        return get_comparison_by_slug(db, canonical_slug)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Comparison with these tools already exists"
        )

def delete_comparison(db: Session, comparison_id: int) -> None:
    query = select(Comparison).where(Comparison.id == comparison_id)
    comparison = db.execute(query).scalars().first()
    if not comparison:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comparison not found")
    db.delete(comparison)
    db.commit()