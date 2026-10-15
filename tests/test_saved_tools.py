from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.models.user import User
from app.models.tool import Tool
from app.models.saved_tool import saved_tools
from app.core.security import hash_password, create_access_token

def test_save_and_unsave_flow(client, db_session):
    user = User(email="saver@example.com", hashed_password=hash_password("password123"), role="user", is_active=True)
    tool = Tool(name="Postman", slug="postman", short_description="API testing tool")
    db_session.add_all([user, tool])
    db_session.commit()
    db_session.refresh(tool)

    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(f"/tools/{tool.id}/save", headers=headers)
    assert res.status_code == 204

    res_list = client.get("/auth/me/saved-tools", headers=headers)
    assert res_list.status_code == 200
    data = res_list.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == tool.id

    res_again = client.post(f"/tools/{tool.id}/save", headers=headers)
    assert res_again.status_code == 204

    res_list = client.get("/auth/me/saved-tools", headers=headers)
    assert res_list.json()["total"] == 1

    res_unsave = client.delete(f"/tools/{tool.id}/save", headers=headers)
    assert res_unsave.status_code == 204

    res_list = client.get("/auth/me/saved-tools", headers=headers)
    assert res_list.json()["total"] == 0
    assert res_list.json()["items"] == []

    res_unsave_never = client.delete(f"/tools/{tool.id}/save", headers=headers)
    assert res_unsave_never.status_code == 204


def test_save_unsave_unknown_tool(client, db_session):
    user = User(email="unknown@example.com", hashed_password=hash_password("password123"), role="user", is_active=True)
    db_session.add(user)
    db_session.commit()

    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    res_save = client.post("/tools/99999/save", headers=headers)
    assert res_save.status_code == 404

    res_unsave = client.delete("/tools/99999/save", headers=headers)
    assert res_unsave.status_code == 404


def test_auth_validation_on_save(anon_client, db_session):
    tool = Tool(name="Docker", slug="docker", short_description="Containers")
    db_session.add(tool)
    db_session.commit()
    db_session.refresh(tool)

    res = anon_client.post(f"/tools/{tool.id}/save")
    assert res.status_code == 401

def test_user_isolation(client, db_session):
    user_a = User(email="a@example.com", hashed_password=hash_password("password123"), role="user", is_active=True)
    user_b = User(email="b@example.com", hashed_password=hash_password("password123"), role="user", is_active=True)
    tool = Tool(name="Redis", slug="redis", short_description="Cache")
    db_session.add_all([user_a, user_b, tool])
    db_session.commit()
    db_session.refresh(tool)

    token_a = create_access_token(user_a.id)
    token_b = create_access_token(user_b.id)

    client.post(f"/tools/{tool.id}/save", headers={"Authorization": f"Bearer {token_a}"})

    res_b = client.get("/auth/me/saved-tools", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b.json()["total"] == 0

    client.post(f"/tools/{tool.id}/save", headers={"Authorization": f"Bearer {token_b}"})
    assert client.get("/auth/me/saved-tools", headers={"Authorization": f"Bearer {token_b}"}).json()["total"] == 1

    client.delete(f"/tools/{tool.id}/save", headers={"Authorization": f"Bearer {token_a}"})
    assert client.get("/auth/me/saved-tools", headers={"Authorization": f"Bearer {token_a}"}).json()["total"] == 0
    assert client.get("/auth/me/saved-tools", headers={"Authorization": f"Bearer {token_b}"}).json()["total"] == 1


def test_request_user_id_injection_protection(client, db_session):
    user_a = User(email="aisol@example.com", hashed_password=hash_password("password123"), role="user", is_active=True)
    user_b = User(email="bisol@example.com", hashed_password=hash_password("password123"), role="user", is_active=True)
    tool_a = Tool(name="ToolA", slug="tool-a", short_description="A")
    tool_b = Tool(name="ToolB", slug="tool-b", short_description="B")
    db_session.add_all([user_a, user_b, tool_a, tool_b])
    db_session.commit()
    db_session.refresh(tool_a)
    db_session.refresh(tool_b)

    client.post(f"/tools/{tool_a.id}/save", headers={"Authorization": f"Bearer {create_access_token(user_a.id)}"})
    client.post(f"/tools/{tool_b.id}/save", headers={"Authorization": f"Bearer {create_access_token(user_b.id)}"})

    token_a = create_access_token(user_a.id)

    res = client.get(f"/auth/me/saved-tools?user_id={user_b.id}", headers={"Authorization": f"Bearer {token_a}"})
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == tool_a.id


def test_saved_list_filtering_and_empty(client, db_session):
    user = User(email="filter@example.com", hashed_password=hash_password("password123"), role="user", is_active=True)
    tool1 = Tool(name="Alpha Tool", slug="alpha", short_description="Alpha", has_free_plan=True)
    tool2 = Tool(name="Beta Tool", slug="beta", short_description="Beta", has_free_plan=False)
    db_session.add_all([user, tool1, tool2])
    db_session.commit()
    db_session.refresh(tool1)
    db_session.refresh(tool2)

    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    res_empty = client.get("/auth/me/saved-tools", headers=headers)
    assert res_empty.status_code == 200
    assert res_empty.json() == {"items": [], "total": 0, "limit": 20, "offset": 0}

    client.post(f"/tools/{tool1.id}/save", headers=headers)
    client.post(f"/tools/{tool2.id}/save", headers=headers)

    res_filtered = client.get("/auth/me/saved-tools?free_plan=true", headers=headers)
    data = res_filtered.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == tool1.id


def test_cascade_behavior(client, db_session):
    user = User(email="cascade@example.com", hashed_password=hash_password("password123"), role="user", is_active=True)
    tool = Tool(name="Temp Tool", slug="temp-tool", short_description="Temp")
    db_session.add_all([user, tool])
    db_session.commit()
    db_session.refresh(tool)

    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    client.post(f"/tools/{tool.id}/save", headers=headers)
    assert client.get("/auth/me/saved-tools", headers=headers).json()["total"] == 1

    db_session.delete(tool)
    db_session.commit()

    res = client.get("/auth/me/saved-tools", headers=headers)
    assert res.status_code == 200
    assert res.json()["total"] == 0


def test_save_twice_and_unsave_never_saved(client, db_session):
    user = User(email="flow@example.com", hashed_password=hash_password("password123"), role="user", is_active=True)
    tool = Tool(name="Git", slug="git", short_description="Version control")
    db_session.add_all([user, tool])
    db_session.commit()
    db_session.refresh(tool)

    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    res1 = client.post(f"/tools/{tool.id}/save", headers=headers)
    assert res1.status_code == 204
    res2 = client.post(f"/tools/{tool.id}/save", headers=headers)
    assert res2.status_code == 204

    res_list = client.get("/auth/me/saved-tools", headers=headers)
    assert res_list.status_code == 200
    assert res_list.json()["total"] == 1

    client.delete(f"/tools/{tool.id}/save", headers=headers)

    res_unsave_never = client.delete(f"/tools/{tool.id}/save", headers=headers)
    assert res_unsave_never.status_code == 204


@pytest.mark.parametrize("method, url", [
    ("POST", "/tools/1/save"),
    ("DELETE", "/tools/1/save"),
    ("GET", "/auth/me/saved-tools"),
])
def test_endpoints_require_login_no_token_and_invalid_token(anon_client, method, url):
    no_token = anon_client.request(method, url)
    assert no_token.status_code == 401

    bad_token = anon_client.request(method, url, headers={"Authorization": "Bearer not-a-real-token"})
    assert bad_token.status_code == 401


def test_user_isolation(client, db_session):
    user_a = User(email="a@example.com", hashed_password=hash_password("password123"), role="user", is_active=True)
    user_b = User(email="b@example.com", hashed_password=hash_password("password123"), role="user", is_active=True)
    tool = Tool(name="Redis", slug="redis", short_description="Cache")
    db_session.add_all([user_a, user_b, tool])
    db_session.commit()
    db_session.refresh(tool)

    token_a = create_access_token(user_a.id)
    token_b = create_access_token(user_b.id)

    client.post(f"/tools/{tool.id}/save", headers={"Authorization": f"Bearer {token_a}"})
    assert client.get("/auth/me/saved-tools", headers={"Authorization": f"Bearer {token_b}"}).json()["total"] == 0

    client.post(f"/tools/{tool.id}/save", headers={"Authorization": f"Bearer {token_b}"})
    assert client.get("/auth/me/saved-tools", headers={"Authorization": f"Bearer {token_b}"}).json()["total"] == 1

    client.delete(f"/tools/{tool.id}/save", headers={"Authorization": f"Bearer {token_a}"})
    assert client.get("/auth/me/saved-tools", headers={"Authorization": f"Bearer {token_a}"}).json()["total"] == 0
    assert client.get("/auth/me/saved-tools", headers={"Authorization": f"Bearer {token_b}"}).json()["total"] == 1


def test_cascade_behavior(client, db_session):
    user = User(email="cascade@example.com", hashed_password=hash_password("password123"), role="user", is_active=True)
    tool = Tool(name="Temp Tool", slug="temp-tool", short_description="Temp")
    db_session.add_all([user, tool])
    db_session.commit()
    db_session.refresh(tool)

    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    client.post(f"/tools/{tool.id}/save", headers=headers)
    assert client.get("/auth/me/saved-tools", headers=headers).json()["total"] == 1

    db_session.delete(tool)
    db_session.commit()

    res = client.get("/auth/me/saved-tools", headers=headers)
    assert res.status_code == 200
    assert res.json()["total"] == 0