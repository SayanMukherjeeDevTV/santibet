import uuid

from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip():
    raw = "CorrectHorse123!"
    hashed = hash_password(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True


def test_wrong_password_fails_verification():
    hashed = hash_password("CorrectHorse123!")
    assert verify_password("WrongPassword", hashed) is False


def test_access_token_roundtrip():
    user_id = uuid.uuid4()
    token = create_access_token(user_id, "user")
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == str(user_id)
    assert payload["role"] == "user"
    assert payload["type"] == "access"


def test_tampered_token_is_rejected():
    user_id = uuid.uuid4()
    token = create_access_token(user_id, "user")
    tampered = token[:-4] + ("aaaa" if not token.endswith("aaaa") else "bbbb")
    assert decode_token(tampered) is None
