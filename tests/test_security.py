from datetime import timedelta
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)

def test_password_hashing():
    plain = "secure-password-123"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("wrong-password", hashed) is False

def test_token_round_trip():
    user_id = 42
    token = create_access_token(user_id)
    sub = decode_access_token(token)
    assert sub == 42

def test_expired_token():
    token = create_access_token(10, expires_delta=timedelta(seconds=-1))
    sub = decode_access_token(token)
    assert sub is None