import hmac
import hashlib
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from fastapi import HTTPException, status, Request
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from app.models.tool import Tool
from app.models.affiliate_link import AffiliateLink
from app.models.affiliate_click import AffiliateClick
from app.core.security import settings
from app.schemas.affiliate import ClickStats

def is_bot(user_agent: str | None) -> bool:
    if not user_agent:
        return True
    ua = user_agent.lower()
    bot_keywords = ["bot", "crawler", "spider", "preview"]
    return any(keyword in ua for keyword in bot_keywords)


def resolve_destination(db: Session, tool: Tool) -> tuple[str, int | None] | None:
    link = db.execute(
        select(AffiliateLink)
        .where(and_(AffiliateLink.tool_id == tool.id, AffiliateLink.is_active == True))
    ).scalars().first()

    if link:
        return link.affiliate_url, link.id
    
    if tool.website_url:
        return tool.website_url, None

    return None


def record_click(db: Session, tool_id: int, link_id: int | None, request: Request):
    try:
        ip = request.client.host if request.client else "0.0.0.0"
        ip_hash = hmac.new(
            settings.ANALYTICS_SALT.encode(),
            ip.encode(),
            hashlib.sha256
        ).hexdigest()

        referrer = request.headers.get("referer")
        user_agent = request.headers.get("user-agent", "")
        bot_status = is_bot(user_agent)

        query_params = request.query_params
        utm_source = query_params.get("utm_source")
        utm_medium = query_params.get("utm_medium")
        utm_campaign = query_params.get("utm_campaign")

        click = AffiliateClick(
            tool_id=tool_id,
            link_id=link_id,
            referrer=referrer[:500] if referrer else None,
            utm_source=utm_source[:100] if utm_source else None,
            utm_medium=utm_medium[:100] if utm_medium else None,
            utm_campaign=utm_campaign[:100] if utm_campaign else None,
            ip_hash=ip_hash,
            is_bot=bot_status
        )
        db.add(click)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Failed to record analytics click: {e}")
        pass


def click_stats(db: Session, tool_id: int, days: int) -> ClickStats:
    since_date = datetime.now(timezone.utc) - timedelta(days=days)

    base_filter = and_(
        AffiliateClick.tool_id == tool_id,
        AffiliateClick.clicked_at >= since_date,
        AffiliateClick.is_bot == False
    )

    total_clicks = db.execute(
        select(func.count(AffiliateClick.id)).where(base_filter)
    ).scalar() or 0

    unique_visitors = db.execute(
        select(func.count(func.distinct(AffiliateClick.ip_hash))).where(base_filter)
    ).scalar() or 0

    day_results = db.execute(
        select(
            func.date(AffiliateClick.clicked_at).label("click_date"),
            func.count(AffiliateClick.id).label("clicks")
        )
        .where(base_filter)
        .group_by(func.date(AffiliateClick.clicked_at))
        .order_by(func.date(AffiliateClick.clicked_at))
    ).all()

    by_day = [{"date": row.click_date, "clicks": row.clicks} for row in day_results]

    source_results = db.execute(
        select(
            AffiliateClick.utm_source,
            func.count(AffiliateClick.id).label("clicks")
        )
        .where(base_filter)
        .group_by(AffiliateClick.utm_source)
        .order_by(func.count(AffiliateClick.id).desc())
    ).all()

    by_source = [{"utm_source": row.utm_source, "clicks": row.clicks} for row in source_results]

    return ClickStats(
        total=total_clicks,
        unique_visitors=unique_visitors,
        by_day=by_day,
        by_source=by_source
    )