import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import User
from app.models.tool import Tool
from app.models.affiliate_link import AffiliateLink
from app.models.affiliate_click import AffiliateClick
from app.core.security import hash_password, create_access_token

def test_redirect_active_link(client, db_session):
    tool = Tool(name="n8n", slug="n8n", website_url="https://n8n.io")
    db_session.add(tool)
    db_session.commit()
    db_session.refresh(tool)

    link = AffiliateLink(tool_id=tool.id, network="PartnerStack", affiliate_url="https://partnerstack.com/n8n", is_active=True)
    db_session.add(link)
    db_session.commit()
    db_session.refresh(link)

    res = client.get("/go/n8n?utm_source=newsletter&url=https://evil.com", follow_redirects=False)
    assert res.status_code == 302
    assert res.headers["location"] == "https://partnerstack.com/n8n"
    assert res.headers["cache-control"] == "no-store"

    click = db_session.query(AffiliateClick).first()
    assert click is not None
    assert click.link_id == link.id
    assert click.utm_source == "newsletter"


def test_redirect_fallback_to_website_url(client, db_session):
    tool = Tool(name="Supabase", slug="supabase", website_url="https://supabase.com")
    db_session.add(tool)
    db_session.commit()
    db_session.refresh(tool)

    res = client.get("/go/supabase", follow_redirects=False)
    assert res.status_code == 302
    assert res.headers["location"] == "https://supabase.com"

    click = db_session.query(AffiliateClick).first()
    assert click is not None
    assert click.link_id is None


def test_redirect_not_found_or_inactive(client, db_session):
    tool = Tool(name="Docker", slug="docker", website_url=None)
    db_session.add(tool)
    db_session.commit()
    db_session.refresh(tool)

    res = client.get("/go/docker", follow_redirects=False)
    assert res.status_code == 404

    res_unknown = client.get("/go/unknown-slug", follow_redirects=False)
    assert res_unknown.status_code == 404

    link = AffiliateLink(tool_id=tool.id, network="Net", affiliate_url="https://inactive.com", is_active=False)
    db_session.add(link)
    db_session.commit()

    res_inactive = client.get("/go/docker", follow_redirects=False)
    assert res_inactive.status_code == 404


def test_redirect_click_failure_resilience(client, db_session, monkeypatch):
    tool = Tool(name="Vercel", slug="vercel", website_url="https://vercel.com")
    db_session.add(tool)
    db_session.commit()
    db_session.refresh(tool)

    def mock_record_click(*args, **kwargs):
        raise Exception("DB down")

    import app.routes.affiliate as aff_routes
    monkeypatch.setattr(aff_routes, "record_click", mock_record_click)

    res = client.get("/go/vercel", follow_redirects=False)
    assert res.status_code == 302
    assert res.headers["location"] == "https://vercel.com"


def test_click_tracking_details(client, db_session):
    tool = Tool(name="Postgres", slug="postgres", website_url="https://postgresql.org")
    db_session.add(tool)
    db_session.commit()
    db_session.refresh(tool)

    headers = {
        "Referer": "https://example.com/blog",
        "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
    }
    res = client.get("/go/postgres?utm_source=twitter&utm_medium=social&utm_campaign=launch", headers=headers, follow_redirects=False)
    assert res.status_code == 302

    click = db_session.query(AffiliateClick).first()
    assert click is not None
    assert click.referrer == "https://example.com/blog"
    assert click.utm_source == "twitter"
    assert click.utm_medium == "social"
    assert click.utm_campaign == "launch"
    assert click.is_bot is True
    assert click.ip_hash is not None
    assert len(click.ip_hash) == 64


def test_admin_affiliate_links_and_second_active_link_conflict(client, anon_client, db_session):
    admin = User(email="admin@example.com", hashed_password=hash_password("password123"), role="admin", is_active=True)
    regular = User(email="user@example.com", hashed_password=hash_password("password123"), role="user", is_active=True)
    tool = Tool(name="Redis", slug="redis", website_url="https://redis.io")
    db_session.add_all([admin, regular, tool])
    db_session.commit()
    db_session.refresh(tool)

    token_admin = create_access_token(admin.id)
    token_regular = create_access_token(regular.id)
    headers_admin = {"Authorization": f"Bearer {token_admin}"}
    headers_regular = {"Authorization": f"Bearer {token_regular}"}

    res_anon = anon_client.get(f"/admin/tools/{tool.id}/affiliate-links")
    assert res_anon.status_code == 401

    res_user = client.get(f"/admin/tools/{tool.id}/affiliate-links", headers=headers_regular)
    assert res_user.status_code == 403

    payload1 = {"network": "NetA", "affiliate_url": "https://a.com", "is_active": True}
    res1 = client.post(f"/admin/tools/{tool.id}/affiliate-links", json=payload1, headers=headers_admin)
    assert res1.status_code == 201

    payload2 = {"network": "NetB", "affiliate_url": "https://b.com", "is_active": True}
    res2 = client.post(f"/admin/tools/{tool.id}/affiliate-links", json=payload2, headers=headers_admin)
    assert res2.status_code == 409

    link1_id = res1.json()["id"]
    client.patch(f"/admin/affiliate-links/{link1_id}", json={"is_active": False}, headers=headers_admin)

    res3 = client.post(f"/admin/tools/{tool.id}/affiliate-links", json=payload2, headers=headers_admin)
    assert res3.status_code == 201


def test_invalid_url_and_days_validation(client, db_session):
    admin = User(email="admin2@example.com", hashed_password=hash_password("password123"), role="admin", is_active=True)
    tool = Tool(name="Kafka", slug="kafka", website_url="https://kafka.apache.org")
    db_session.add_all([admin, tool])
    db_session.commit()

    headers = {"Authorization": f"Bearer {create_access_token(admin.id)}"}

    payload = {"network": "Evil", "affiliate_url": "javascript:alert(1)", "is_active": True}
    res = client.post(f"/admin/tools/{tool.id}/affiliate-links", json=payload, headers=headers)
    assert res.status_code == 422

    assert client.get(f"/admin/tools/{tool.id}/clicks?days=0", headers=headers).status_code == 422
    assert client.get(f"/admin/tools/{tool.id}/clicks?days=400", headers=headers).status_code == 422


from datetime import datetime, timedelta, timezone

def test_click_stats_counts_groups_and_excludes_bots_and_old(client, db_session):
    tool = Tool(name="Redis", slug="redis", website_url="https://redis.io")
    db_session.add(tool); db_session.commit(); db_session.refresh(tool)

    now = datetime.now(timezone.utc)
    def click(**kw):
        db_session.add(AffiliateClick(tool_id=tool.id, **kw))

    click(ip_hash="a", utm_source="twitter", is_bot=False, clicked_at=now)
    click(ip_hash="a", utm_source="twitter", is_bot=False, clicked_at=now)   # same visitor
    click(ip_hash="b", utm_source=None,      is_bot=False, clicked_at=now)
    click(ip_hash="c", utm_source="twitter", is_bot=True,  clicked_at=now)   # bot: excluded
    click(ip_hash="d", utm_source="twitter", is_bot=False, clicked_at=now - timedelta(days=40))  # too old
    db_session.commit()

    data = client.get(f"/admin/tools/{tool.id}/clicks?days=30").json()
    assert data["total"] == 3
    assert data["unique_visitors"] == 2
    assert {"utm_source": "twitter", "clicks": 2} in data["by_source"]
    assert {"utm_source": None, "clicks": 1} in data["by_source"]
    assert sum(day["clicks"] for day in data["by_day"]) == 3


def test_redirect_ignores_url_parameters(client, db_session):
    tool = Tool(name="Redis", slug="redis", website_url="https://redis.io")
    db_session.add(tool); db_session.commit()

    res = client.get("/go/redis?url=https://evil.example&next=https://evil.example",
                     follow_redirects=False)
    assert res.status_code == 302
    assert res.headers["location"] == "https://redis.io"