import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app
from app.models.user import User
from app.models.tool import Tool
from app.models.tool_submission import ToolSubmission
from app.core.security import hash_password, create_access_token

def test_user_submit_success_and_mass_assignment_protection(client, db_session):
    user = User(email="submitter@example.com", hashed_password=hash_password("password123"), role="user", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "name": "Postman",
        "slug": "postman",
        "website_url": "https://www.postman.com",
        "short_description": "API Client",
        "pricing_model": "Freemium",
        "note": "Great tool",
        "status": "approved" 
    }
    res = client.post("/submissions", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "pending"
    assert data["submitted_by_id"] == user.id


def test_submission_unauthenticated(db_session):
    payload = {
        "name": "Docker",
        "slug": "docker",
        "website_url": "https://docker.com"
    }
    with TestClient(app) as anon_client:
        res = anon_client.post("/submissions", json=payload)
        assert res.status_code == 401

@pytest.mark.parametrize("bad_url", ["javascript:alert(1)", "ftp://x.com"])
def test_submission_invalid_urls(client, db_session, bad_url):
    user = User(email="urltest@example.com", hashed_password=hash_password("password123"), role="user", is_active=True)
    db_session.add(user)
    db_session.commit()
    token = create_access_token(user.id)

    payload = {
        "name": "Bad URL Tool",
        "slug": "bad-url-tool",
        "website_url": bad_url
    }
    res = client.post("/submissions", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 422

def test_submission_slug_already_tool(client, db_session):
    user = User(email="slugtest@example.com", hashed_password=hash_password("password123"), role="user", is_active=True)
    existing_tool = Tool(name="Git", slug="git", website_url="https://git-scm.com")
    db_session.add_all([user, existing_tool])
    db_session.commit()

    token = create_access_token(user.id)
    payload = {
        "name": "Git Duplicate",
        "slug": "git",
        "website_url": "https://example.com"
    }
    res = client.post("/submissions", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 409

def test_max_pending_submissions_limit(client, db_session):
    user = User(email="spam@example.com", hashed_password=hash_password("password123"), role="user", is_active=True)
    db_session.add(user)
    db_session.commit()

    for i in range(5):
        sub = ToolSubmission(
            submitted_by_id=user.id,
            name=f"Tool {i}",
            slug=f"tool-{i}",
            website_url="https://example.com",
            status="pending"
        )
        db_session.add(sub)
    db_session.commit()

    token = create_access_token(user.id)
    payload = {
        "name": "Tool 6",
        "slug": "tool-6",
        "website_url": "https://example.com"
    }
    res = client.post("/submissions", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 429


def test_read_mine_and_get_by_id(client, db_session):
    user_a = User(email="usera@example.com", hashed_password=hash_password("password123"), role="user", is_active=True)
    user_b = User(email="userb@example.com", hashed_password=hash_password("password123"), role="user", is_active=True)
    editor = User(email="editor@example.com", hashed_password=hash_password("password123"), role="editor", is_active=True)
    db_session.add_all([user_a, user_b, editor])
    db_session.commit()

    sub_a = ToolSubmission(submitted_by_id=user_a.id, name="Tool A", slug="tool-a", website_url="https://a.com", status="pending")
    sub_b = ToolSubmission(submitted_by_id=user_b.id, name="Tool B", slug="tool-b", website_url="https://b.com", status="pending")
    db_session.add_all([sub_a, sub_b])
    db_session.commit()
    db_session.refresh(sub_a)
    db_session.refresh(sub_b)

    token_a = create_access_token(user_a.id)
    token_b = create_access_token(user_b.id)
    token_editor = create_access_token(editor.id)

    res_mine = client.get("/submissions/mine", headers={"Authorization": f"Bearer {token_a}"})
    assert res_mine.status_code == 200
    items = res_mine.json()
    assert len(items) == 1
    assert items[0]["id"] == sub_a.id

    assert client.get(f"/submissions/{sub_a.id}", headers={"Authorization": f"Bearer {token_a}"}).status_code == 200
    assert client.get(f"/submissions/{sub_a.id}", headers={"Authorization": f"Bearer {token_b}"}).status_code == 404
    assert client.get(f"/submissions/{sub_a.id}", headers={"Authorization": f"Bearer {token_editor}"}).status_code == 200


def test_review_workflow_approval_and_rejection(client, db_session):
    user = User(email="sub@example.com", hashed_password=hash_password("password123"), role="user", is_active=True)
    regular_user = User(email="reg@example.com", hashed_password=hash_password("password123"), role="user", is_active=True)
    editor = User(email="ed@example.com", hashed_password=hash_password("password123"), role="editor", is_active=True)
    db_session.add_all([user, regular_user, editor])
    db_session.commit()

    sub = ToolSubmission(
        submitted_by_id=user.id,
        name="Redis",
        slug="redis",
        website_url="https://redis.io",
        short_description="In-memory cache",
        pricing_model="Open Source",
        status="pending"
    )
    db_session.add(sub)
    db_session.commit()
    db_session.refresh(sub)

    token_reg = create_access_token(regular_user.id)
    token_ed = create_access_token(editor.id)

    assert client.get("/admin/submissions", headers={"Authorization": f"Bearer {token_reg}"}).status_code == 403

    res_list = client.get("/admin/submissions?status=pending", headers={"Authorization": f"Bearer {token_ed}"})
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    res_approve = client.post(f"/admin/submissions/{sub.id}/approve", headers={"Authorization": f"Bearer {token_ed}"})
    assert res_approve.status_code == 200
    approved_data = res_approve.json()
    assert approved_data["status"] == "approved"
    assert approved_data["reviewer_id"] == editor.id
    assert approved_data["reviewed_at"] is not None
    assert approved_data["tool_id"] is not None

    tools_res = client.get("/tools/")
    assert tools_res.status_code == 200
    tool_slugs = [t["slug"] for t in tools_res.json()["items"]]
    assert "redis" in tool_slugs

    res_approve_again = client.post(f"/admin/submissions/{sub.id}/approve", headers={"Authorization": f"Bearer {token_ed}"})
    assert res_approve_again.status_code == 409


def test_rejection_flow_and_constraints(client, db_session):
    user = User(email="sub2@example.com", hashed_password=hash_password("password123"), role="user", is_active=True)
    editor = User(email="ed2@example.com", hashed_password=hash_password("password123"), role="editor", is_active=True)
    db_session.add_all([user, editor])
    db_session.commit()

    sub = ToolSubmission(
        submitted_by_id=user.id,
        name="RabbitMQ",
        slug="rabbitmq",
        website_url="https://rabbitmq.com",
        status="pending"
    )
    db_session.add(sub)
    db_session.commit()
    db_session.refresh(sub)

    token_ed = create_access_token(editor.id)
    headers = {"Authorization": f"Bearer {token_ed}"}

    res_bad_reject = client.post(f"/admin/submissions/{sub.id}/reject", json={}, headers=headers)
    assert res_bad_reject.status_code == 422

    res_reject = client.post(f"/admin/submissions/{sub.id}/reject", json={"review_note": "Not suitable"}, headers=headers)
    assert res_reject.status_code == 200
    assert res_reject.json()["status"] == "rejected"

    res_try_approve = client.post(f"/admin/submissions/{sub.id}/approve", headers=headers)
    assert res_try_approve.status_code == 409


def test_delete_submitter_account_set_null(client, db_session):
    user = User(email="tempuser@example.com", hashed_password=hash_password("password123"), role="user", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    sub = ToolSubmission(
        submitted_by_id=user.id,
        name="Temp Tool",
        slug="temp-tool",
        website_url="https://temp.com",
        status="pending"
    )
    db_session.add(sub)
    db_session.commit()
    db_session.refresh(sub)
    sub_id = sub.id

    db_session.delete(user)
    db_session.commit()

    reloaded_sub = db_session.get(ToolSubmission, sub_id)
    assert reloaded_sub is not None
    assert reloaded_sub.submitted_by_id is None



def test_approve_twice_slug_conflict_and_exact_tool_count(client, db_session):
    user = User(email="sub_twice@example.com", hashed_password=hash_password("password123"), role="user", is_active=True)
    editor = User(email="editor_twice@example.com", hashed_password=hash_password("password123"), role="editor", is_active=True)
    db_session.add_all([user, editor])
    db_session.commit()

    sub = ToolSubmission(
        submitted_by_id=user.id,
        name="Docker",
        slug="docker",
        website_url="https://www.docker.com",
        status="pending"
    )
    db_session.add(sub)
    db_session.commit()
    db_session.refresh(sub)

    headers = {"Authorization": f"Bearer {create_access_token(editor.id)}"}

    res1 = client.post(f"/admin/submissions/{sub.id}/approve", headers=headers)
    assert res1.status_code == 200

    res2 = client.post(f"/admin/submissions/{sub.id}/approve", headers=headers)
    assert res2.status_code == 409

    tools = db_session.execute(select(Tool).where(Tool.slug == "docker")).scalars().all()
    assert len(tools) == 1


def test_slug_taken_after_submission_returns_409(client, db_session):
    user = User(email="sub_race@example.com", hashed_password=hash_password("password123"), role="user", is_active=True)
    editor = User(email="editor_race@example.com", hashed_password=hash_password("password123"), role="editor", is_active=True)
    db_session.add_all([user, editor])
    db_session.commit()

    sub = ToolSubmission(
        submitted_by_id=user.id,
        name="Kubernetes",
        slug="kubernetes",
        website_url="https://kubernetes.io",
        status="pending"
    )
    db_session.add(sub)
    db_session.commit()
    db_session.refresh(sub)

    conflicting_tool = Tool(name="Kubernetes Official", slug="kubernetes", website_url="https://k8s.io")
    db_session.add(conflicting_tool)
    db_session.commit()

    headers = {"Authorization": f"Bearer {create_access_token(editor.id)}"}
    res = client.post(f"/admin/submissions/{sub.id}/approve", headers=headers)
    assert res.status_code == 409


def test_admin_routes_forbidden_for_regular_user(client, db_session):
    user = User(email="regular@example.com", hashed_password=hash_password("password123"), role="user", is_active=True)
    db_session.add(user)
    db_session.commit()

    headers = {"Authorization": f"Bearer {create_access_token(user.id)}"}

    assert client.get("/admin/submissions", headers=headers).status_code == 403
    assert client.post("/admin/submissions/999/approve", headers=headers).status_code == 403
    assert client.post("/admin/submissions/999/reject", json={"review_note": "No"}, headers=headers).status_code == 403


def test_unknown_id_returns_404_on_approve_and_reject(client, db_session):
    editor = User(email="editor_404@example.com", hashed_password=hash_password("password123"), role="editor", is_active=True)
    db_session.add(editor)
    db_session.commit()

    headers = {"Authorization": f"Bearer {create_access_token(editor.id)}"}

    assert client.post("/admin/submissions/99999/approve", headers=headers).status_code == 404
    assert client.post("/admin/submissions/99999/reject", json={"review_note": "Nope"}, headers=headers).status_code == 404