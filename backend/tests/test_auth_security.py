from datetime import UTC, datetime, timedelta
from uuid import uuid4


def test_password_hash_round_trip_does_not_store_plaintext():
    from app.core.security import hash_password, verify_password

    password_hash = hash_password("Password123")

    assert password_hash != "Password123"
    assert verify_password("Password123", password_hash) is True
    assert verify_password("WrongPassword123", password_hash) is False


def test_access_token_round_trip_contains_token_version():
    from app.core.security import create_access_token, decode_access_token

    user_id = uuid4()
    token = create_access_token(
        user_id=user_id,
        student_no="20252160A1010",
        role="member",
        token_version=3,
        expires_delta=timedelta(minutes=10),
    )

    payload = decode_access_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["student_no"] == "20252160A1010"
    assert payload["role"] == "member"
    assert payload["token_version"] == 3


def test_captcha_code_hash_round_trip_and_svg_data_url():
    from app.modules.auth.captcha import (
        create_captcha_image_data_url,
        generate_captcha_code,
        hash_captcha_code,
        verify_captcha_code,
    )

    code = generate_captcha_code()
    code_hash = hash_captcha_code(code)
    image = create_captcha_image_data_url(code)

    assert len(code) == 4
    assert code_hash != code
    assert verify_captcha_code(code.lower(), code_hash) is True
    assert verify_captcha_code("ZZZZ", code_hash) is False
    assert image.startswith("data:image/svg+xml;base64,")


def test_jwt_expiration_is_valid_datetime_claim():
    from app.core.security import create_access_token, decode_access_token

    token = create_access_token(
        user_id=uuid4(),
        student_no="20252160A1010",
        role="admin",
        token_version=1,
        expires_delta=timedelta(minutes=10),
    )
    payload = decode_access_token(token)

    assert datetime.fromtimestamp(payload["exp"], tz=UTC) > datetime.now(tz=UTC)
