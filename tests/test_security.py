from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_has_random_salt():
    password = "a long password for testing"
    first, second = hash_password(password), hash_password(password)
    assert first != second
    assert verify_password(password, first)
    assert not verify_password("incorrect", first)


def test_access_token_has_subject_and_configured_lifetime():
    user_id = uuid4()
    payload = decode_access_token(create_access_token(user_id))
    assert payload.sub == user_id
    assert payload.exp - payload.iat == get_settings().access_token_expire_minutes * 60


@pytest.mark.parametrize("overrides", [
    {"secret_key": ""}, {"secret_key": "short"}, {"secret_key": "x" * 64},
    {"algorithm": "none"}, {"access_token_expire_minutes": 0},
])
def test_settings_reject_unsafe_auth_configuration(overrides):
    with pytest.raises(ValidationError):
        Settings(**overrides)
