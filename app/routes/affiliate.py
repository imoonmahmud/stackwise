import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.database import get_db
from app.models.affiliate_link import AffiliateLink
from app.models.tool import Tool
from app.schemas.affiliate import ClickStats, LinkCreate, LinkRead, LinkUpdate
from app.services.affiliate_service import click_stats, record_click, resolve_destination

logger = logging.getLogger(__name__)

router = APIRouter(tags=["affiliate"])                       # public: /go/{slug}
admin_router = APIRouter(                                    # every route here needs editor/admin
    prefix="/admin",
    tags=["affiliate-admin"],
    dependencies=[Depends(require_role("editor", "admin"))],
)


def _is_http_url(url: str) -> bool:
    return url.lower().startswith(("http://", "https://"))


def _get_tool_or_404(db: Session, tool_id: int) -> Tool:
    tool = db.get(Tool, tool_id)
    if tool is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
    return tool


def _other_active_link_exists(db: Session, tool_id: int, exclude_id: int | None = None) -> bool:
    query = select(AffiliateLink.id).where(
        AffiliateLink.tool_id == tool_id, AffiliateLink.is_active.is_(True)
    )
    if exclude_id is not None:
        query = query.where(AffiliateLink.id != exclude_id)
    return db.execute(query).first() is not None


@router.get("/go/{slug}")
def redirect_to_tool(slug: str, request: Request, db: Session = Depends(get_db)):
    tool = db.execute(select(Tool).where(Tool.slug == slug)).scalars().first()
    if tool is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")

    destination = resolve_destination(db, tool)
    if destination is None or not _is_http_url(destination[0]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No destination link available")
    url, link_id = destination

    try:
        record_click(db, tool.id, link_id, request)
    except Exception:
        db.rollback()
        logger.exception("Could not record affiliate click")

    return RedirectResponse(
        url=url, status_code=status.HTTP_302_FOUND, headers={"Cache-Control": "no-store"}
    )


@admin_router.post("/tools/{tool_id}/affiliate-links", response_model=LinkRead,
                   status_code=status.HTTP_201_CREATED)
def create_affiliate_link(tool_id: int, data: LinkCreate, db: Session = Depends(get_db)):
    _get_tool_or_404(db, tool_id)
    if data.is_active and _other_active_link_exists(db, tool_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="An active affiliate link already exists for this tool.")

    link = AffiliateLink(
        tool_id=tool_id,
        network=data.network,
        affiliate_url=str(data.affiliate_url),
        commission_type=data.commission_type,
        commission_value=data.commission_value,
        is_active=data.is_active,
    )
    db.add(link)
    try:
        db.commit()
    except IntegrityError:               # two requests at once: the partial index is the real guard
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="An active affiliate link already exists for this tool.")
    db.refresh(link)
    return link


@admin_router.get("/tools/{tool_id}/affiliate-links", response_model=list[LinkRead])
def list_affiliate_links(tool_id: int, db: Session = Depends(get_db)):
    _get_tool_or_404(db, tool_id)
    return list(db.execute(
        select(AffiliateLink).where(AffiliateLink.tool_id == tool_id).order_by(AffiliateLink.id)
    ).scalars().all())


@admin_router.patch("/affiliate-links/{link_id}", response_model=LinkRead)
def update_affiliate_link(link_id: int, data: LinkUpdate, db: Session = Depends(get_db)):
    link = db.get(AffiliateLink, link_id)
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Affiliate link not found")

    update_data = data.model_dump(exclude_unset=True)
    for field in ("network", "affiliate_url", "is_active"):      # NOT NULL columns
        if field in update_data and update_data[field] is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=f"{field} cannot be null")

    if update_data.get("is_active") is True and _other_active_link_exists(db, link.tool_id, exclude_id=link_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Another active affiliate link already exists for this tool.")

    for field, value in update_data.items():
        setattr(link, field, str(value) if field == "affiliate_url" else value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Another active affiliate link already exists for this tool.")
    db.refresh(link)
    return link


@admin_router.delete("/affiliate-links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_affiliate_link(link_id: int, db: Session = Depends(get_db)):
    link = db.get(AffiliateLink, link_id)
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Affiliate link not found")
    db.delete(link)
    db.commit()


@admin_router.get("/tools/{tool_id}/clicks", response_model=ClickStats)
def get_tool_clicks(tool_id: int, days: int = Query(default=30, ge=1, le=365),
                    db: Session = Depends(get_db)):
    _get_tool_or_404(db, tool_id)
    return click_stats(db, tool_id, days)