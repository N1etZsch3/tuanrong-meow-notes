import hashlib
from io import BytesIO
from uuid import UUID, uuid4

from PIL import Image

from app.core.config import Settings, get_settings
from app.core.errors import APIError, ErrorCode
from app.modules.files import service
from app.modules.files.content_security import (
    MediaCheckSubmission,
    get_content_security_client,
)
from app.modules.files.dependencies import get_object_storage, get_optional_object_storage
from app.modules.files.models import FileAsset, FileAssetVariant
from tests.test_auth_api import auth_headers, create_token, create_user


class FakeObjectStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.deleted_keys: list[str] = []

    def put_object(self, *, object_key: str, body: bytes, content_type: str) -> str:
        self.objects[object_key] = body
        return f"https://cos.test/{object_key}"

    def presign_get_object(self, object_key: str, *, expires: int = 3600) -> str:
        return f"https://signed.test/{object_key}?expires={expires}"

    def get_object(self, object_key: str) -> bytes:
        return self.objects[object_key]

    def delete_object(self, object_key: str) -> None:
        self.deleted_keys.append(object_key)
        self.objects.pop(object_key, None)


class FakeContentSecurityClient:
    def __init__(self, trace_id: str = "wechat-trace-1") -> None:
        self.trace_id = trace_id
        self.calls: list[dict] = []

    def submit_image(self, *, media_url: str, openid: str, scene: int):
        self.calls.append({"media_url": media_url, "openid": openid, "scene": scene})
        return MediaCheckSubmission(trace_id=self.trace_id)


def install_fake_storage(api_client) -> FakeObjectStorage:
    storage = FakeObjectStorage()
    api_client.app.dependency_overrides[get_object_storage] = lambda: storage
    api_client.app.dependency_overrides[get_optional_object_storage] = lambda: storage
    return storage


def install_enforced_content_security(api_client, monkeypatch, *, trace_id="wechat-trace-1"):
    settings = Settings(
        _env_file=None,
        wechat_miniapp_appid="miniapp-id",
        wechat_miniapp_secret="miniapp-secret",
        wechat_content_security_mode="enforced",
        wechat_content_security_callback_token="callback-token",
    )
    client = FakeContentSecurityClient(trace_id)
    api_client.app.dependency_overrides[get_settings] = lambda: settings
    api_client.app.dependency_overrides[get_content_security_client] = lambda: client
    monkeypatch.setattr(
        service,
        "exchange_wechat_code_for_openid",
        lambda _code, settings=None: "openid-uploader",
    )
    return client


def image_bytes(
    *,
    fmt: str = "JPEG",
    size: tuple[int, int] = (1000, 750),
    color: tuple[int, int, int] = (230, 160, 90),
) -> bytes:
    image = Image.new("RGB", size, color)
    buffer = BytesIO()
    image.save(buffer, format=fmt)
    return buffer.getvalue()


def create_completed_cat_photo_asset(db_session, user) -> FileAsset:
    asset_id = uuid4()
    asset = FileAsset(
        id=asset_id,
        storage_provider="tencent_cos",
        bucket="catmap-test",
        region="ap-guangzhou",
        env="test",
        usage_type="cat_photo",
        owner_type="temporary",
        owner_id=None,
        source_filename="stored-cat.jpg",
        source_mime_type="image/jpeg",
        source_size_bytes=2048,
        source_width=640,
        source_height=480,
        source_checksum_sha256="stored-cat-sha256",
        default_variant_key="display",
        default_url="https://cos.test/catmap/test/cat/display.jpg",
        default_thumb_variant_key="thumb_md",
        default_thumb_url="https://cos.test/catmap/test/cat/thumb_md.jpg",
        process_preset="normal_photo_v1",
        process_status="completed",
        security_status="legacy",
        visibility="internal",
        uploaded_by=user.id,
    )
    asset.variants.extend(
        [
            FileAssetVariant(
                variant_key="thumb_md",
                object_key=f"catmap/test/cat/{asset_id}/thumb_md.jpg",
                url="https://cos.test/catmap/test/cat/thumb_md.jpg",
                mime_type="image/jpeg",
                file_ext="jpg",
                width=320,
                height=240,
                size_bytes=1024,
                quality=80,
                resize_mode="fit",
                checksum_sha256="thumb-md-sha256",
                sort_order=0,
            ),
            FileAssetVariant(
                variant_key="display",
                object_key=f"catmap/test/cat/{asset_id}/display.jpg",
                url="https://cos.test/catmap/test/cat/display.jpg",
                mime_type="image/jpeg",
                file_ext="jpg",
                width=640,
                height=480,
                size_bytes=2048,
                quality=82,
                resize_mode="fit",
                checksum_sha256="display-sha256",
                sort_order=1,
            ),
        ]
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)
    return asset


def raise_cos_config_error():
    raise APIError(
        code=ErrorCode.FILE_COS_UPLOAD_FAILED,
        message="腾讯云 COS 配置未完成",
        status_code=500,
    )


def test_get_file_upload_config_returns_image_limits(api_client, db_session):
    user = create_user(
        db_session,
        student_no="trmx0001",
        password="trmx0001",
        must_change_password=False,
        profile_completed=True,
    )
    token = create_token(user)

    response = api_client.get("/api/v1/files/config", headers=auth_headers(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    data = payload["data"]
    assert data["max_file_size_bytes"] == 10 * 1024 * 1024
    assert data["max_batch_count"] == 9
    assert "image/jpeg" in data["allowed_mime_types"]
    assert "user_avatar" in {item["usage_type"] for item in data["usage_types"]}
    assert "task_checkin_photo" in {item["usage_type"] for item in data["usage_types"]}
    assert "supply_record_photo" in {item["usage_type"] for item in data["usage_types"]}
    usage_configs = {item["usage_type"]: item for item in data["usage_types"]}
    assert usage_configs["medicine_photo"]["label"] == "药品照片"
    assert usage_configs["medicine_photo"]["max_batch_count"] == 5


def test_upload_user_avatar_allows_incomplete_profile_and_creates_variants(api_client, db_session):
    storage = install_fake_storage(api_client)
    user = create_user(
        db_session,
        student_no="trmx0002",
        password="trmx0002",
        must_change_password=False,
        profile_completed=False,
    )
    token = create_token(user)

    response = api_client.post(
        "/api/v1/files/images",
        headers=auth_headers(token),
        data={
            "usage_type": "user_avatar",
            "owner_type": "user",
            "owner_id": str(user.id),
            "visibility": "internal",
        },
        files={"file": ("avatar.png", image_bytes(fmt="PNG"), "image/png")},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["usage_type"] == "user_avatar"
    assert data["owner_type"] == "user"
    assert data["owner_id"] == str(user.id)
    assert data["process_status"] == "completed"
    assert data["default_variant_key"] == "avatar_lg"
    assert data["default_thumb_variant_key"] == "avatar_md"
    assert set(data["variants"]) == {"avatar_sm", "avatar_md", "avatar_lg"}
    assert data["variants"]["avatar_sm"]["width"] == 128
    assert data["variants"]["avatar_sm"]["height"] == 128
    assert data["source"]["source_filename"] == "avatar.png"
    assert len(storage.objects) == 3

    asset = db_session.get(FileAsset, UUID(data["asset_id"]))
    assert asset is not None
    assert asset.uploaded_by == user.id
    assert asset.default_url == data["default_url"]
    variants = (
        db_session.query(FileAssetVariant)
        .filter(FileAssetVariant.file_asset_id == asset.id)
        .all()
    )
    assert {variant.variant_key for variant in variants} == {"avatar_sm", "avatar_md", "avatar_lg"}


def test_saved_user_avatar_content_is_available_to_other_users(api_client, db_session):
    storage = install_fake_storage(api_client)
    member = create_user(
        db_session,
        student_no="trmx-avatar-member",
        password="Password123",
        must_change_password=False,
        profile_completed=True,
    )
    admin = create_user(
        db_session,
        student_no="trmx-avatar-admin",
        password="Password123",
        role="admin",
        must_change_password=False,
        profile_completed=True,
    )
    member_token = create_token(member)
    admin_token = create_token(admin)

    upload_response = api_client.post(
        "/api/v1/files/images",
        headers=auth_headers(member_token),
        data={
            "usage_type": "user_avatar",
            "owner_type": "user",
            "owner_id": str(member.id),
            "visibility": "public",
        },
        files={"file": ("avatar.png", image_bytes(fmt="PNG"), "image/png")},
    )

    assert upload_response.status_code == 200
    asset_id = upload_response.json()["data"]["asset_id"]
    avatar_content_url = f"/api/v1/files/assets/{asset_id}/content?scene=avatar_profile"

    save_response = api_client.patch(
        "/api/v1/profile/me",
        headers=auth_headers(member_token),
        json={"avatar_url": avatar_content_url},
    )
    assert save_response.status_code == 200

    admin_response = api_client.get(
        f"/api/v1/admin/users/{member.id}",
        headers=auth_headers(admin_token),
    )
    assert admin_response.status_code == 200
    assert admin_response.json()["data"]["profile"]["avatar_url"] == avatar_content_url

    content_response = api_client.get(avatar_content_url)
    assert content_response.status_code == 200
    assert content_response.headers["content-type"].startswith("image/jpeg")
    assert content_response.content
    assert storage.objects


def test_upload_business_image_requires_completed_profile(api_client, db_session):
    install_fake_storage(api_client)
    user = create_user(
        db_session,
        student_no="trmx0003",
        password="trmx0003",
        must_change_password=False,
        profile_completed=False,
    )
    token = create_token(user)

    response = api_client.post(
        "/api/v1/files/images",
        headers=auth_headers(token),
        data={"usage_type": "cat_photo"},
        files={"file": ("cat.jpg", image_bytes(), "image/jpeg")},
    )

    assert response.status_code == 403
    assert response.json()["code"] == 63006


def test_upload_admin_only_usage_rejects_member(api_client, db_session):
    install_fake_storage(api_client)
    user = create_user(
        db_session,
        student_no="trmx0004",
        password="trmx0004",
        must_change_password=False,
        profile_completed=True,
    )
    token = create_token(user)

    response = api_client.post(
        "/api/v1/files/images",
        headers=auth_headers(token),
        data={"usage_type": "map_point_route"},
        files={"file": ("route.jpg", image_bytes(), "image/jpeg")},
    )

    assert response.status_code == 403
    assert response.json()["code"] == 40302


def test_upload_task_point_photo_accepts_common_high_resolution_phone_image(api_client, db_session):
    storage = install_fake_storage(api_client)
    user = create_user(
        db_session,
        student_no="trmx0010",
        password="trmx0010",
        role="admin",
        must_change_password=False,
        profile_completed=True,
    )
    token = create_token(user)

    response = api_client.post(
        "/api/v1/files/images",
        headers=auth_headers(token),
        data={"usage_type": "map_point_scene", "owner_type": "task"},
        files={"file": ("task-point.jpg", image_bytes(size=(6000, 4000)), "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["source"]["source_width"] == 6000
    assert data["source"]["source_height"] == 4000
    assert data["variants"]["display"]["width"] == 1280
    assert len(storage.objects) == 4


def test_admin_can_upload_supply_point_scene_photo(api_client, db_session):
    install_fake_storage(api_client)
    admin = create_user(
        db_session,
        student_no="trmx0013",
        password="trmx0013",
        role="admin",
        must_change_password=False,
        profile_completed=True,
    )
    token = create_token(admin)

    response = api_client.post(
        "/api/v1/files/images",
        headers=auth_headers(token),
        data={"usage_type": "map_point_scene", "owner_type": "supply_point"},
        files={"file": ("supply-point.jpg", image_bytes(), "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["usage_type"] == "map_point_scene"
    assert data["owner_type"] == "supply_point"


def test_member_can_upload_supply_record_photo(api_client, db_session):
    install_fake_storage(api_client)
    member = create_user(
        db_session,
        student_no="trmx0014",
        password="trmx0014",
        must_change_password=False,
        profile_completed=True,
    )
    token = create_token(member)

    response = api_client.post(
        "/api/v1/files/images",
        headers=auth_headers(token),
        data={"usage_type": "supply_record_photo", "owner_type": "supply_point_record"},
        files={"file": ("supply-record.jpg", image_bytes(), "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["usage_type"] == "supply_record_photo"
    assert data["owner_type"] == "supply_point_record"


def test_member_can_upload_medicine_photo(api_client, db_session):
    install_fake_storage(api_client)
    member = create_user(
        db_session,
        student_no="trmx0015",
        password="trmx0015",
        must_change_password=False,
        profile_completed=True,
    )
    token = create_token(member)

    response = api_client.post(
        "/api/v1/files/images",
        headers=auth_headers(token),
        data={"usage_type": "medicine_photo", "owner_type": "medicine_catalog"},
        files={"file": ("medicine.jpg", image_bytes(), "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["usage_type"] == "medicine_photo"
    assert data["owner_type"] == "medicine_catalog"


def test_upload_rejects_corrupt_image(api_client, db_session):
    install_fake_storage(api_client)
    user = create_user(
        db_session,
        student_no="trmx0005",
        password="trmx0005",
        must_change_password=False,
        profile_completed=True,
    )
    token = create_token(user)

    response = api_client.post(
        "/api/v1/files/images",
        headers=auth_headers(token),
        data={"usage_type": "user_avatar"},
        files={"file": ("broken.jpg", b"not actually an image", "image/jpeg")},
    )

    assert response.status_code == 400
    assert response.json()["code"] == 65004


def test_get_asset_variant_uses_scene_mapping(api_client, db_session):
    install_fake_storage(api_client)
    user = create_user(
        db_session,
        student_no="trmx0006",
        password="trmx0006",
        must_change_password=False,
        profile_completed=True,
    )
    token = create_token(user)
    upload_response = api_client.post(
        "/api/v1/files/images",
        headers=auth_headers(token),
        data={"usage_type": "cat_photo", "owner_type": "temporary"},
        files={"file": ("cat.jpg", image_bytes(), "image/jpeg")},
    )
    asset_id = upload_response.json()["data"]["asset_id"]

    response = api_client.get(
        f"/api/v1/files/assets/{asset_id}/variant?scene=map_marker_preview",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["asset_id"] == asset_id
    assert data["variant_key"] == "thumb_sm"
    assert data["url"].startswith("https://signed.test/")
    assert "/thumb_sm.jpg" in data["url"]


def test_get_asset_variant_falls_back_to_stored_url_when_cos_config_missing(
    api_client,
    db_session,
):
    user = create_user(
        db_session,
        student_no="trmx0011",
        password="trmx0011",
        must_change_password=False,
        profile_completed=True,
    )
    asset = create_completed_cat_photo_asset(db_session, user)
    token = create_token(user)
    api_client.app.dependency_overrides[get_object_storage] = raise_cos_config_error
    api_client.app.dependency_overrides[get_optional_object_storage] = lambda: None

    response = api_client.get(
        f"/api/v1/files/assets/{asset.id}/variant?scene=cat_list_cover",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["variant_key"] == "thumb_md"
    assert data["url"] == "https://cos.test/catmap/test/cat/thumb_md.jpg"


def test_get_asset_content_streams_cos_variant_without_redirect_for_mini_program(
    api_client,
    db_session,
):
    install_fake_storage(api_client)
    user = create_user(
        db_session,
        student_no="trmx0009",
        password="trmx0009",
        role="admin",
        must_change_password=False,
        profile_completed=True,
    )
    token = create_token(user)
    upload_response = api_client.post(
        "/api/v1/files/images",
        headers=auth_headers(token),
        data={"usage_type": "map_point_scene", "owner_type": "task"},
        files={"file": ("task-point.jpg", image_bytes(), "image/jpeg")},
    )
    asset_id = upload_response.json()["data"]["asset_id"]

    response = api_client.get(
        f"/api/v1/files/assets/{asset_id}/content?scene=task_list_cover",
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert "location" not in response.headers
    Image.open(BytesIO(response.content)).verify()


def test_get_asset_content_falls_back_to_stored_url_when_cos_config_missing(
    api_client,
    db_session,
):
    user = create_user(
        db_session,
        student_no="trmx0012",
        password="trmx0012",
        must_change_password=False,
        profile_completed=True,
    )
    asset = create_completed_cat_photo_asset(db_session, user)
    api_client.app.dependency_overrides[get_object_storage] = raise_cos_config_error
    api_client.app.dependency_overrides[get_optional_object_storage] = lambda: None

    response = api_client.get(
        f"/api/v1/files/assets/{asset.id}/content?scene=cat_list_cover",
        follow_redirects=False,
    )

    assert response.status_code == 307
    assert response.headers["location"] == "https://cos.test/catmap/test/cat/thumb_md.jpg"


def test_bind_temporary_asset_to_owner(api_client, db_session):
    install_fake_storage(api_client)
    user = create_user(
        db_session,
        student_no="trmx0007",
        password="trmx0007",
        must_change_password=False,
        profile_completed=True,
    )
    token = create_token(user)
    upload_response = api_client.post(
        "/api/v1/files/images",
        headers=auth_headers(token),
        data={"usage_type": "cat_photo"},
        files={"file": ("cat.jpg", image_bytes(), "image/jpeg")},
    )
    asset_id = upload_response.json()["data"]["asset_id"]
    owner_id = uuid4()

    response = api_client.patch(
        f"/api/v1/files/assets/{asset_id}/owner",
        headers=auth_headers(token),
        json={"owner_type": "cat", "owner_id": str(owner_id)},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["asset_id"] == asset_id
    assert data["owner_type"] == "cat"
    assert data["owner_id"] == str(owner_id)


def test_bind_cannot_reclassify_unreviewed_business_image_as_user_avatar(
    api_client,
    db_session,
):
    install_fake_storage(api_client)
    user = create_user(
        db_session,
        student_no="trmx-avatar-reclassify",
        password="Password123",
        must_change_password=False,
        profile_completed=True,
    )
    token = create_token(user)
    upload_response = api_client.post(
        "/api/v1/files/images",
        headers=auth_headers(token),
        data={"usage_type": "cat_photo"},
        files={"file": ("ordinary.jpg", image_bytes(), "image/jpeg")},
    )
    asset_id = upload_response.json()["data"]["asset_id"]

    response = api_client.patch(
        f"/api/v1/files/assets/{asset_id}/owner",
        headers=auth_headers(token),
        json={
            "owner_type": "user",
            "owner_id": str(user.id),
            "usage_type": "user_avatar",
        },
    )

    assert response.status_code == 422
    assert response.json()["code"] == int(ErrorCode.FILE_SECURITY_REJECTED)


def test_delete_asset_soft_deletes_asset_and_variants(api_client, db_session):
    install_fake_storage(api_client)
    user = create_user(
        db_session,
        student_no="trmx0008",
        password="trmx0008",
        must_change_password=False,
        profile_completed=True,
    )
    token = create_token(user)
    upload_response = api_client.post(
        "/api/v1/files/images",
        headers=auth_headers(token),
        data={"usage_type": "cat_photo"},
        files={"file": ("cat.jpg", image_bytes(), "image/jpeg")},
    )
    asset_id = upload_response.json()["data"]["asset_id"]

    response = api_client.delete(
        f"/api/v1/files/assets/{asset_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["data"]["deleted"] is True

    asset = db_session.get(FileAsset, UUID(asset_id))
    assert asset.process_status == "deleted"
    assert asset.deleted_at is not None
    assert all(variant.deleted_at is not None for variant in asset.variants)

    deleted_response = api_client.get(
        f"/api/v1/files/assets/{asset_id}",
        headers=auth_headers(token),
    )
    assert deleted_response.status_code == 409
    assert deleted_response.json()["code"] == 65012


def test_enforced_avatar_upload_stays_pending_until_wechat_passes(
    api_client,
    db_session,
    monkeypatch,
):
    storage = install_fake_storage(api_client)
    security = install_enforced_content_security(api_client, monkeypatch)
    user = create_user(
        db_session,
        student_no="trmx-security-pass",
        password="Password123",
        must_change_password=False,
        profile_completed=True,
    )
    user.profile.avatar_url = "/legacy/avatar.jpg"
    db_session.commit()
    token = create_token(user)

    response = api_client.post(
        "/api/v1/files/images",
        headers=auth_headers(token),
        data={
            "usage_type": "user_avatar",
            "owner_type": "user",
            "owner_id": str(user.id),
            "visibility": "public",
            "wechat_code": "fresh-code",
        },
        files={"file": ("avatar.png", image_bytes(fmt="PNG"), "image/png")},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["security_status"] == "pending"
    assert data["default_url"] is None
    assert data["review_message"] == "图片已上传，审核通过后自动生效"
    assert security.calls == [
        {
            "media_url": security.calls[0]["media_url"],
            "openid": "openid-uploader",
            "scene": 1,
        }
    ]
    assert security.calls[0]["media_url"].startswith("https://signed.test/")
    db_session.refresh(user.profile)
    assert user.profile.avatar_url == "/legacy/avatar.jpg"
    assert user.profile.avatar_review_status == "pending"
    assert str(user.profile.avatar_review_asset_id) == data["asset_id"]
    assert len(storage.objects) == 3

    blocked = api_client.get(
        f"/api/v1/files/assets/{data['asset_id']}/content?scene=avatar_profile"
    )
    assert blocked.status_code == 409
    assert blocked.json()["code"] == int(ErrorCode.FILE_SECURITY_PENDING)

    result = service.handle_security_callback(
        db_session,
        {
            "trace_id": "wechat-trace-1",
            "errcode": 0,
            "result": {"suggest": "pass", "label": 100},
        },
    )
    assert result["security_status"] == "passed"
    db_session.refresh(user.profile)
    assert user.profile.avatar_review_status == "passed"
    assert user.profile.avatar_asset_id == user.profile.avatar_review_asset_id
    assert user.profile.avatar_url.endswith(f"/{data['asset_id']}/content?scene=avatar_profile")

    content = api_client.get(user.profile.avatar_url)
    assert content.status_code == 200
    assert content.headers["content-type"] == "image/jpeg"


def test_rejected_avatar_keeps_previous_avatar_and_callback_is_idempotent(
    api_client,
    db_session,
    monkeypatch,
):
    install_fake_storage(api_client)
    install_enforced_content_security(api_client, monkeypatch, trace_id="wechat-trace-risky")
    user = create_user(
        db_session,
        student_no="trmx-security-risky",
        password="Password123",
        must_change_password=False,
        profile_completed=True,
    )
    user.profile.avatar_url = "/legacy/avatar.jpg"
    db_session.commit()
    token = create_token(user)
    response = api_client.post(
        "/api/v1/files/images",
        headers=auth_headers(token),
        data={
            "usage_type": "user_avatar",
            "owner_type": "user",
            "owner_id": str(user.id),
            "wechat_code": "fresh-code",
        },
        files={"file": ("avatar.jpg", image_bytes(), "image/jpeg")},
    )
    asset_id = response.json()["data"]["asset_id"]
    payload = {
        "trace_id": "wechat-trace-risky",
        "errcode": 0,
        "result": {"suggest": "risky", "label": 20002},
    }

    first = service.handle_security_callback(db_session, payload)
    second = service.handle_security_callback(db_session, payload)

    assert first["security_status"] == "rejected"
    assert second["security_status"] == "rejected"
    db_session.refresh(user.profile)
    assert user.profile.avatar_url == "/legacy/avatar.jpg"
    assert user.profile.avatar_review_status == "rejected"
    blocked = api_client.get(
        f"/api/v1/files/assets/{asset_id}/content?scene=avatar_profile"
    )
    assert blocked.status_code == 422
    assert blocked.json()["message"] == "图片包含违规内容，请更换后重试"


def test_older_avatar_callback_cannot_override_a_newer_pending_avatar(
    api_client,
    db_session,
    monkeypatch,
):
    install_fake_storage(api_client)
    security = install_enforced_content_security(
        api_client,
        monkeypatch,
        trace_id="wechat-avatar-first",
    )
    user = create_user(
        db_session,
        student_no="trmx-avatar-order",
        password="Password123",
        must_change_password=False,
        profile_completed=True,
    )
    user.profile.avatar_url = "/legacy/avatar.jpg"
    db_session.commit()
    token = create_token(user)

    first = api_client.post(
        "/api/v1/files/images",
        headers=auth_headers(token),
        data={
            "usage_type": "user_avatar",
            "owner_type": "user",
            "owner_id": str(user.id),
            "wechat_code": "first-code",
        },
        files={"file": ("first.jpg", image_bytes(color=(220, 120, 80)), "image/jpeg")},
    )
    first_asset_id = first.json()["data"]["asset_id"]

    security.trace_id = "wechat-avatar-second"
    second = api_client.post(
        "/api/v1/files/images",
        headers=auth_headers(token),
        data={
            "usage_type": "user_avatar",
            "owner_type": "user",
            "owner_id": str(user.id),
            "wechat_code": "second-code",
        },
        files={"file": ("second.jpg", image_bytes(color=(80, 120, 220)), "image/jpeg")},
    )
    second_asset_id = second.json()["data"]["asset_id"]
    db_session.refresh(user.profile)
    assert str(user.profile.avatar_review_asset_id) == second_asset_id

    service.handle_security_callback(
        db_session,
        {
            "trace_id": "wechat-avatar-first",
            "errcode": 0,
            "result": {"suggest": "pass", "label": 100},
        },
    )
    db_session.refresh(user.profile)
    assert user.profile.avatar_url == "/legacy/avatar.jpg"
    assert str(user.profile.avatar_review_asset_id) == second_asset_id
    assert str(user.profile.avatar_review_asset_id) != first_asset_id
    assert user.profile.avatar_review_status == "pending"

    service.handle_security_callback(
        db_session,
        {
            "trace_id": "wechat-avatar-second",
            "errcode": 0,
            "result": {"suggest": "pass", "label": 100},
        },
    )
    db_session.refresh(user.profile)
    assert str(user.profile.avatar_asset_id) == second_asset_id
    assert user.profile.avatar_url.endswith(f"/{second_asset_id}/content?scene=avatar_profile")


def test_content_security_callback_verifies_signature_and_applies_result(
    api_client,
    db_session,
    monkeypatch,
):
    install_fake_storage(api_client)
    install_enforced_content_security(api_client, monkeypatch, trace_id="wechat-route-trace")
    user = create_user(
        db_session,
        student_no="trmx-security-route",
        password="Password123",
        must_change_password=False,
        profile_completed=True,
    )
    token = create_token(user)
    api_client.post(
        "/api/v1/files/images",
        headers=auth_headers(token),
        data={
            "usage_type": "user_avatar",
            "owner_type": "user",
            "owner_id": str(user.id),
            "wechat_code": "fresh-code",
        },
        files={"file": ("avatar.jpg", image_bytes(), "image/jpeg")},
    )
    timestamp = "1783810000"
    nonce = "nonce-1"
    source = "".join(sorted(("callback-token", timestamp, nonce)))
    signature = hashlib.sha1(source.encode()).hexdigest()

    rejected_signature = api_client.post(
        f"/api/v1/wechat/content-security/events?signature=bad&timestamp={timestamp}&nonce={nonce}",
        json={
            "Event": "wxa_media_check",
            "trace_id": "wechat-route-trace",
            "errcode": 0,
            "result": {"suggest": "pass", "label": 100},
        },
    )
    assert rejected_signature.status_code == 403

    response = api_client.post(
        f"/api/v1/wechat/content-security/events?signature={signature}&timestamp={timestamp}&nonce={nonce}",
        json={
            "Event": "wxa_media_check",
            "trace_id": "wechat-route-trace",
            "errcode": 0,
            "result": {"suggest": "pass", "label": 100},
        },
    )
    assert response.status_code == 200
    assert response.text == "success"
    db_session.refresh(user.profile)
    assert user.profile.avatar_review_status == "passed"


def test_xml_content_security_callback_applies_passed_avatar(
    api_client,
    db_session,
    monkeypatch,
):
    install_fake_storage(api_client)
    install_enforced_content_security(api_client, monkeypatch, trace_id="wechat-route-xml")
    user = create_user(
        db_session,
        student_no="trmx-security-xml",
        password="Password123",
        must_change_password=False,
        profile_completed=True,
    )
    token = create_token(user)
    api_client.post(
        "/api/v1/files/images",
        headers=auth_headers(token),
        data={
            "usage_type": "user_avatar",
            "owner_type": "user",
            "owner_id": str(user.id),
            "wechat_code": "fresh-code",
        },
        files={"file": ("avatar.jpg", image_bytes(), "image/jpeg")},
    )
    timestamp = "1783810001"
    nonce = "nonce-xml"
    source = "".join(sorted(("callback-token", timestamp, nonce)))
    signature = hashlib.sha1(source.encode()).hexdigest()
    body = b"""<xml>
      <Event><![CDATA[wxa_media_check]]></Event>
      <trace_id><![CDATA[wechat-route-xml]]></trace_id>
      <errcode>0</errcode>
      <result>
        <suggest><![CDATA[pass]]></suggest>
        <label>100</label>
      </result>
    </xml>"""

    response = api_client.post(
        f"/api/v1/wechat/content-security/events?signature={signature}"
        f"&timestamp={timestamp}&nonce={nonce}",
        content=body,
        headers={"content-type": "application/xml"},
    )

    assert response.status_code == 200
    assert response.text == "success"
    db_session.refresh(user.profile)
    assert user.profile.avatar_review_status == "passed"


def test_profile_update_rejects_direct_avatar_url_bypass(api_client, db_session):
    user = create_user(
        db_session,
        student_no="trmx-avatar-bypass",
        password="Password123",
        must_change_password=False,
        profile_completed=True,
    )
    token = create_token(user)

    response = api_client.patch(
        "/api/v1/profile/me",
        headers=auth_headers(token),
        json={"avatar_url": "https://unreviewed.example/avatar.jpg"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == int(ErrorCode.FILE_SECURITY_REJECTED)


def test_non_avatar_images_skip_content_security_and_are_immediately_readable(
    api_client,
    db_session,
    monkeypatch,
):
    install_fake_storage(api_client)
    security = install_enforced_content_security(
        api_client,
        monkeypatch,
        trace_id="wechat-business-trace",
    )
    admin = create_user(
        db_session,
        student_no="trmx-security-business",
        password="Password123",
        role="admin",
        must_change_password=False,
        profile_completed=True,
    )
    token = create_token(admin)
    response = api_client.post(
        "/api/v1/files/images",
        headers=auth_headers(token),
        data={
            "usage_type": "map_point_scene",
            "owner_type": "task",
        },
        files={"file": ("scene.jpg", image_bytes(), "image/jpeg")},
    )
    assert response.status_code == 200
    asset_id = response.json()["data"]["asset_id"]
    assert security.calls == []
    assert response.json()["data"]["security_status"] == "legacy"
    assert response.json()["data"]["default_url"] is not None

    readable = api_client.get(
        f"/api/v1/files/assets/{asset_id}/variant?scene=task_list_cover",
        headers=auth_headers(token),
    )
    assert readable.status_code == 200
    assert readable.json()["data"]["url"].startswith("https://signed.test/")

    asset = db_session.get(FileAsset, UUID(asset_id))
    asset.security_status = "failed"
    db_session.commit()

    historical_failure = api_client.get(
        f"/api/v1/files/assets/{asset_id}",
        headers=auth_headers(token),
    )
    assert historical_failure.status_code == 200
    assert historical_failure.json()["data"]["security_status"] == "legacy"
    assert historical_failure.json()["data"]["default_url"] is not None

    readable_after_old_failure = api_client.get(
        f"/api/v1/files/assets/{asset_id}/variant?scene=task_list_cover",
        headers=auth_headers(token),
    )
    assert readable_after_old_failure.status_code == 200


def test_enforced_avatar_upload_requires_fresh_wechat_code(api_client, db_session, monkeypatch):
    install_fake_storage(api_client)
    install_enforced_content_security(api_client, monkeypatch)
    user = create_user(
        db_session,
        student_no="trmx-security-code",
        password="Password123",
        must_change_password=False,
        profile_completed=True,
    )
    token = create_token(user)
    response = api_client.post(
        "/api/v1/files/images",
        headers=auth_headers(token),
        data={"usage_type": "user_avatar", "owner_type": "user", "owner_id": str(user.id)},
        files={"file": ("avatar.jpg", image_bytes(), "image/jpeg")},
    )
    assert response.status_code == 400
    assert response.json()["code"] == int(ErrorCode.FILE_SECURITY_CODE_REQUIRED)
