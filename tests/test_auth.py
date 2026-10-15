from datetime import timedelta, datetime, timezone
import pytest
import jwt

from app.core.security import hash_password, create_access_token
from app.models.user import User
from app.config import settings

def test_register_success(anon_client):
    response = anon_client.post(
        "/auth/register",
        json={"email": "NewUser@Example.com", "password": "securepassword123"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["role"] == "user" 
    assert data["is_active"] is True
    assert "password" not in data
    assert "hashed_password" not in data

def test_register_duplicate_email_case_insensitive(anon_client):
    payload = {"email": "Test@Example.com", "password": "password123"}
    res1 = anon_client.post("/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = anon_client.post("/auth/register", json={"email": "TEST@example.com", "password": "otherpassword"})
    assert res2.status_code == 409

@pytest.mark.parametrize(
    "email,password",
    [
        ("valid@example.com", "short"),
        ("not-an-email", "securepassword123"),
    ]
)
def test_register_validation_errors(anon_client, email, password):
    response = anon_client.post("/auth/register", json={"email": email, "password": password})
    assert response.status_code == 422

def test_register_mass_assignment_role_ignored(anon_client, db_session):
    response = anon_client.post(
        "/auth/register",
        json={"email": "hacker@example.com", "password": "securepassword123", "role": "admin"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "user"

def test_register_password_hashing_differs(anon_client, db_session):
    anon_client.post(
        "/auth/register",
        json={"email": "hashcheck@example.com", "password": "mypassword123"}
    )
    user = db_session.query(User).filter(User.email == "hashcheck@example.com").first()
    assert user.hashed_password != "mypassword123"


def test_login_success(anon_client):
    anon_client.post(
        "/auth/register",
        json={"email": "login@example.com", "password": "correctpassword"}
    )
    response = anon_client.post(
        "/auth/login",
        data={"username": "login@example.com", "password": "correctpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_credentials_same_error_message(anon_client):
    anon_client.post(
        "/auth/register",
        json={"email": "existing@example.com", "password": "correctpassword"}
    )

    res_wrong_pass = anon_client.post(
        "/auth/login",
        data={"username": "existing@example.com", "password": "wrongpassword"}
    )
    assert res_wrong_pass.status_code == 401

    res_unknown_email = anon_client.post(
        "/auth/login",
        data={"username": "unknown@example.com", "password": "correctpassword"}
    )
    assert res_unknown_email.status_code == 401

    assert res_wrong_pass.json()["detail"] == res_unknown_email.json()["detail"]

def test_login_inactive_user(anon_client, db_session):
    user = User(
        email="inactive@example.com",
        hashed_password=hash_password("password123"),
        role="user",
        is_active=False
    )
    db_session.add(user)
    db_session.commit()

    response = anon_client.post(
        "/auth/login",
        data={"username": "inactive@example.com", "password": "password123"}
    )
    assert response.status_code == 401

def test_auth_me_valid_token(anon_client):
    anon_client.post(
        "/auth/register",
        json={"email": "me@example.com", "password": "securepassword123"}
    )
    login_res = anon_client.post(
        "/auth/login",
        data={"username": "me@example.com", "password": "securepassword123"}
    )
    token = login_res.json()["access_token"]

    response = anon_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"

@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Authorization": "Bearer notarealtoken"}
    ]
)
def test_auth_me_invalid_or_missing_token(anon_client, headers):
    response = anon_client.get("/auth/me", headers=headers)
    assert response.status_code == 401

def test_auth_me_expired_token(anon_client):
    expired_token = create_access_token(user_id=1, expires_delta=timedelta(seconds=-10))
    response = anon_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401

def test_auth_me_deleted_user(db_session, anon_client):
    user = User(
        email="todelete@example.com",
        hashed_password=hash_password("password123"),
        role="user"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    token = create_access_token(user.id)
    
    db_session.delete(user)
    db_session.commit()

    response = anon_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401

def test_write_endpoint_without_token_unauthorized(anon_client):
    response = anon_client.post("/tools/", json={"name": "Tool", "slug": "tool"})
    assert response.status_code == 401

def test_write_endpoint_with_user_role_forbidden(db_session, anon_client):
    user = User(
        email="regularuser@example.com",
        hashed_password=hash_password("password123"),
        role="user"
    )
    db_session.add(user)
    db_session.commit()
    token = create_access_token(user.id)

    response = anon_client.post(
        "/tools/",
        json={"name": "Tool", "slug": "tool", "short_description": "desc"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403

@pytest.mark.parametrize("role", ["editor", "admin"])
def test_write_endpoint_with_editor_or_admin_role_succeeds(db_session, anon_client, role):
    admin_or_editor = User(
        email=f"{role}@example.com",
        hashed_password=hash_password("password123"),
        role=role
    )
    db_session.add(admin_or_editor)
    db_session.commit()
    token = create_access_token(admin_or_editor.id)

    response = anon_client.post(
        "/tools/",
        json={"name": f"Tool {role}", "slug": f"tool-{role}", "short_description": "desc"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201


def test_get_public_endpoint_without_token_succeeds(anon_client):
    response = anon_client.get("/tools/")
    assert response.status_code == 200

def test_token_signed_with_different_secret(anon_client, db_session):
    user = User(email="sec@example.com", hashed_password=hash_password("password123"), role="editor", is_active=True)
    db_session.add(user)
    db_session.commit()
    
    bad_token = jwt.encode({"sub": str(user.id), "exp": datetime.now(timezone.utc) + timedelta(minutes=15)}, "wrong-secret-key", algorithm="HS256")
    
    response = anon_client.get("/auth/me", headers={"Authorization": f"Bearer {bad_token}"})
    assert response.status_code == 401

def test_token_tampered_payload(anon_client, db_session):
    user = User(email="tamper@example.com", hashed_password=hash_password("password123"), role="editor", is_active=True)
    db_session.add(user)
    db_session.commit()
    
    valid_token = create_access_token(user.id)
    tampered_token = valid_token + "maliciousdata"
    
    response = anon_client.get("/auth/me", headers={"Authorization": f"Bearer {tampered_token}"})
    assert response.status_code == 401

def test_token_sub_not_a_number(anon_client):
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    bad_sub_token = jwt.encode({"sub": "abc", "exp": expire}, settings.SECRET_KEY, algorithm="HS256")
    
    response = anon_client.get("/auth/me", headers={"Authorization": f"Bearer {bad_sub_token}"})
    assert response.status_code == 401

def test_token_no_sub_claim(anon_client):
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    no_sub_token = jwt.encode({"exp": expire}, settings.SECRET_KEY, algorithm="HS256")
    
    response = anon_client.get("/auth/me", headers={"Authorization": f"Bearer {no_sub_token}"})
    assert response.status_code == 401

def test_user_deactivated_after_token_issued(anon_client, db_session):
    user = User(email="active@example.com", hashed_password=hash_password("password123"), role="editor", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    token = create_access_token(user.id)
    
    user.is_active = False
    db_session.commit()
    
    response = anon_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401

def test_user_role_downgraded_dynamically(anon_client, db_session):
    user = User(email="promoted@example.com", hashed_password=hash_password("password123"), role="editor", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    token = create_access_token(user.id)
    
    user.role = "user"
    db_session.commit()
    
    response = anon_client.post(
        "/tools/",
        json={"name": "New Tool", "slug": "new-tool", "short_description": "desc"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


def test_login_mixed_case_capitals(anon_client):
    res = anon_client.post(
        "/auth/register",
        json={"email": "Capitals.Test@Example.com", "password": "securepassword123"}
    )
    assert res.status_code == 201

    response = anon_client.post(
        "/auth/login",
        data={"username": "cApItAlS.tEsT@eXaMpLe.CoM", "password": "securepassword123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()