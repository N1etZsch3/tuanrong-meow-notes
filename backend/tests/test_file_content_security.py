from uuid import uuid4

import pytest

from app.core.config import Settings
from app.core.errors import APIError, ErrorCode
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.files import content_security
from app.modules.files import service as file_service
from app.modules.files.models import FileAsset


def test_wechat_media_check_uses_v2_image_profile_contract(monkeypatch):
    content_security._token_cache.clear()
    calls: list[tuple[str, dict]] = []

    def fake_post(url: str, payload: dict, _timeout: float):
        calls.append((url, payload))
        if url == content_security.WECHAT_STABLE_TOKEN_URL:
            return {"access_token": "access-token-1", "expires_in": 7200}
        return {"errcode": 0, "errmsg": "ok", "trace_id": "trace-media-1"}

    monkeypatch.setattr(content_security, "_post_json", fake_post)
    client = content_security.WeChatContentSecurityClient(
        Settings(
            _env_file=None,
            wechat_miniapp_appid="miniapp-id",
            wechat_miniapp_secret="miniapp-secret",
        )
    )

    submission = client.submit_image(
        media_url="https://signed.example/avatar.jpg",
        openid="openid-user-1",
        scene=1,
    )

    assert submission.trace_id == "trace-media-1"
    assert calls[1][0].startswith(content_security.WECHAT_MEDIA_CHECK_URL)
    assert calls[1][1] == {
        "media_url": "https://signed.example/avatar.jpg",
        "media_type": 2,
        "version": 2,
        "scene": 1,
        "openid": "openid-user-1",
    }


def test_callback_signature_matches_wechat_plaintext_mode():
    assert content_security.verify_callback_signature(
        token="callback-token",
        signature="706a0ea250c9290a83b90d414d0ad48a8ab6ae0d",
        timestamp="1783810000",
        nonce="nonce-1",
    ) is False

    import hashlib

    source = "".join(sorted(("callback-token", "1783810000", "nonce-1")))
    signature = hashlib.sha1(source.encode()).hexdigest()
    assert content_security.verify_callback_signature(
        token="callback-token",
        signature=signature,
        timestamp="1783810000",
        nonce="nonce-1",
    ) is True


def test_new_file_assets_fail_closed_by_default():
    status_default = FileAsset.__table__.c.security_status.default

    assert status_default is not None
    assert status_default.arg == "pending"


def _business_asset(db_session, user: User, *, status: str, usage_type: str) -> FileAsset:
    asset = FileAsset(
        storage_provider="tencent_cos",
        bucket="catmap-test",
        region="ap-guangzhou",
        env="test",
        usage_type=usage_type,
        owner_type="temporary",
        source_filename="reviewed.jpg",
        source_mime_type="image/jpeg",
        source_size_bytes=1024,
        source_width=640,
        source_height=480,
        default_variant_key="display",
        default_url=f"https://cos.test/{uuid4()}/display.jpg",
        default_thumb_variant_key="thumb_md",
        default_thumb_url=f"https://cos.test/{uuid4()}/thumb_md.jpg",
        process_preset="normal_photo_v1",
        process_status="completed",
        security_status=status,
        visibility="internal",
        uploaded_by=user.id,
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)
    return asset


def _business_user(db_session, *, role: str = "member") -> User:
    user = User(
        student_no=f"security{uuid4().hex[:10]}",
        password_hash=hash_password("Password123"),
        role=role,
        status="active",
        must_change_password=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_business_binding_resolves_only_passed_asset_to_canonical_urls(
    db_session,
    monkeypatch,
):
    monkeypatch.setattr(
        file_service,
        "get_settings",
        lambda: Settings(_env_file=None, wechat_content_security_mode="enforced"),
    )
    user = _business_user(db_session)
    asset = _business_asset(db_session, user, status="passed", usage_type="medicine_photo")

    resolved = file_service.resolve_business_image(
        db=db_session,
        current_user=user,
        file_id=None,
        file_url=asset.default_url,
        thumbnail_url="https://untrusted.example/thumb.jpg",
        allowed_usage_types={"medicine_photo"},
    )

    assert resolved == (asset.id, asset.default_url, asset.default_thumb_url)


@pytest.mark.parametrize(
    ("status", "expected_code"),
    [("pending", ErrorCode.FILE_SECURITY_PENDING), ("legacy", ErrorCode.FILE_SECURITY_REJECTED)],
)
def test_business_binding_rejects_asset_that_is_not_newly_approved(
    db_session,
    monkeypatch,
    status,
    expected_code,
):
    monkeypatch.setattr(
        file_service,
        "get_settings",
        lambda: Settings(_env_file=None, wechat_content_security_mode="enforced"),
    )
    user = _business_user(db_session)
    asset = _business_asset(db_session, user, status=status, usage_type="medicine_photo")

    with pytest.raises(APIError) as exc_info:
        file_service.resolve_business_image(
            db=db_session,
            current_user=user,
            file_id=asset.id,
            file_url=asset.default_url,
            thumbnail_url=None,
            allowed_usage_types={"medicine_photo"},
        )

    assert exc_info.value.code == expected_code


def test_business_binding_rejects_wrong_usage_and_other_members_asset(
    db_session,
    monkeypatch,
):
    monkeypatch.setattr(
        file_service,
        "get_settings",
        lambda: Settings(_env_file=None, wechat_content_security_mode="enforced"),
    )
    owner = _business_user(db_session)
    other_member = _business_user(db_session)
    asset = _business_asset(db_session, owner, status="passed", usage_type="medicine_photo")

    with pytest.raises(APIError) as usage_error:
        file_service.resolve_business_image(
            db=db_session,
            current_user=owner,
            file_id=asset.id,
            file_url=asset.default_url,
            thumbnail_url=None,
            allowed_usage_types={"task_checkin_photo"},
        )
    with pytest.raises(APIError) as ownership_error:
        file_service.resolve_business_image(
            db=db_session,
            current_user=other_member,
            file_id=asset.id,
            file_url=asset.default_url,
            thumbnail_url=None,
            allowed_usage_types={"medicine_photo"},
        )

    assert usage_error.value.code == ErrorCode.FILE_SECURITY_REJECTED
    assert ownership_error.value.code == ErrorCode.FILE_FORBIDDEN
