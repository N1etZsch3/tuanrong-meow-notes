from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.modules.auth.models import User, UserProfile
from app.modules.medicines.models import MedicineHolding, MedicinePhoto, MedicineUseApplication

EXPECTED_MEDICINE_TABLES = {
    "medicine_categories",
    "medicine_catalogs",
    "medicine_aliases",
    "medicine_photos",
    "medicine_holdings",
    "medicine_stock_logs",
    "medicine_use_applications",
}


def create_user(db: Session, *, role: str = "member", nickname: str = "药品测试成员") -> User:
    user = User(
        student_no=f"medicine{uuid4().hex[:10]}",
        password_hash=hash_password("Password123"),
        role=role,
        status="active",
        must_change_password=False,
    )
    db.add(user)
    db.flush()
    db.add(UserProfile(user_id=user.id, nickname=nickname, profile_completed=True))
    db.commit()
    db.refresh(user)
    return user


def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(
        user_id=user.id,
        student_no=user.student_no,
        role=user.role,
        token_version=user.token_version,
    )
    return {"Authorization": f"Bearer {token}"}


def create_medicine(api_client, user: User, db: Session, *, initial_quantity: int = 20) -> dict:
    categories_response = api_client.get(
        "/api/v1/medicine-categories",
        headers=auth_headers(user),
    )
    assert categories_response.status_code == 200
    category_id = categories_response.json()["data"]["items"][0]["id"]
    response = api_client.post(
        "/api/v1/medicines",
        headers=auth_headers(user),
        json={
            "catalog": {
                "name": f"阿莫西林-{uuid4().hex[:6]}",
                "category_id": category_id,
                "specification": "250mg/片",
                "unit": "片",
                "description": "常用抗生素",
                "usage_notes": "遵医嘱使用",
                "cover_image_url": "https://img.example.com/amoxicillin.jpg",
            },
            "initial_quantity": initial_quantity,
            "remark": "第一次建档",
        },
    )
    assert response.status_code == 200
    db.expire_all()
    return response.json()["data"]


def test_medicine_models_register_expected_tables():
    import app.modules.medicines.models  # noqa: F401
    from app.db.base import Base

    assert EXPECTED_MEDICINE_TABLES.issubset(Base.metadata.tables)


def test_member_can_create_medicine_and_read_catalog_summary(api_client, db_session):
    member = create_user(db_session, nickname="持有人A")
    headers = auth_headers(member)

    categories_response = api_client.get("/api/v1/medicine-categories", headers=headers)

    assert categories_response.status_code == 200
    categories = categories_response.json()["data"]["items"]
    assert [item["name"] for item in categories] == [
        "抗生素",
        "消炎药",
        "止疼药",
        "驱虫药",
        "外用消毒",
        "眼耳用药",
        "营养补充",
        "其他",
    ]

    create_response = api_client.post(
        "/api/v1/medicines",
        headers=headers,
        json={
            "catalog": {
                "name": "阿莫西林",
                "category_id": categories[0]["id"],
                "specification": "250mg/片",
                "unit": "片",
                "description": "常用抗生素",
                "usage_notes": "遵医嘱使用",
                "cover_image_url": "https://img.example.com/amoxicillin.jpg",
                "photo_urls": [
                    "https://img.example.com/amoxicillin.jpg",
                    "https://img.example.com/amoxicillin-box.jpg",
                    "https://img.example.com/amoxicillin-label.jpg",
                ],
            },
            "initial_quantity": 20,
            "remark": "第一次建档",
        },
    )

    assert create_response.status_code == 200
    created = create_response.json()["data"]
    assert created["medicine_id"]
    assert created["holding_id"]
    assert created["created_catalog"] is True
    assert created["created_holding"] is True
    assert created["initial_stock_log_id"]
    cover_photo = db_session.scalar(
        select(MedicinePhoto).where(
            MedicinePhoto.medicine_id == UUID(created["medicine_id"]),
            MedicinePhoto.photo_type == "cover",
            MedicinePhoto.deleted_at.is_(None),
        ),
    )
    assert cover_photo is not None
    assert cover_photo.file_url == "https://img.example.com/amoxicillin.jpg"
    assert cover_photo.uploaded_by == member.id
    photos = db_session.scalars(
        select(MedicinePhoto)
        .where(
            MedicinePhoto.medicine_id == UUID(created["medicine_id"]),
            MedicinePhoto.deleted_at.is_(None),
        )
        .order_by(MedicinePhoto.sort_order)
    ).all()
    assert [photo.file_url for photo in photos] == [
        "https://img.example.com/amoxicillin.jpg",
        "https://img.example.com/amoxicillin-box.jpg",
        "https://img.example.com/amoxicillin-label.jpg",
    ]
    assert [photo.photo_type for photo in photos] == ["cover", "gallery", "gallery"]

    list_response = api_client.get("/api/v1/medicines", headers=headers)
    assert list_response.status_code == 200
    list_data = list_response.json()["data"]
    assert list_data["total"] == 1
    item = list_data["items"][0]
    assert item["medicine_id"] == created["medicine_id"]
    assert item["name"] == "阿莫西林"
    assert item["category"]["name"] == "抗生素"
    assert item["cover_image_url"] == "https://img.example.com/amoxicillin.jpg"
    assert item["total_current_quantity"] == 20
    assert item["total_in_quantity"] == 20
    assert item["stock_status"] == "sufficient"
    assert item["stock_status_label"] == "库存充足"
    assert item["holder_count"] == 1
    assert item["holders"][0]["holder_nickname"] == "持有人A"
    assert item["holders"][0]["current_quantity"] == 20

    detail_response = api_client.get(
        f"/api/v1/medicines/{created['medicine_id']}",
        headers=headers,
    )
    assert detail_response.status_code == 200
    detail = detail_response.json()["data"]
    assert detail["medicine_id"] == created["medicine_id"]
    assert detail["cover_image_url"] == "https://img.example.com/amoxicillin.jpg"
    assert detail["total_current_quantity"] == 20
    assert detail["permissions"]["can_edit_catalog"] is False
    assert detail["recent_logs"][0]["operation_type"] == "initial_in"
    assert detail["recent_logs"][0]["quantity_after"] == 20

    holding_response = api_client.get(
        f"/api/v1/medicine-holdings/{created['holding_id']}",
        headers=headers,
    )
    assert holding_response.status_code == 200
    holding = holding_response.json()["data"]
    assert holding["holding_id"] == created["holding_id"]
    assert holding["medicine"]["name"] == "阿莫西林"
    assert holding["medicine"]["cover_image_url"] == "https://img.example.com/amoxicillin.jpg"
    assert holding["holder"]["nickname"] == "持有人A"
    assert holding["current_quantity"] == 20
    assert holding["permissions"] == {
        "is_holder": True,
        "can_record": True,
        "can_apply": False,
        "can_review_application": True,
    }

    search_response = api_client.get(
        "/api/v1/medicines/search?keyword=阿莫",
        headers=headers,
    )
    assert search_response.status_code == 200
    search_item = search_response.json()["data"]["items"][0]
    assert search_item["medicine_id"] == created["medicine_id"]
    assert search_item["category"]["name"] == "抗生素"
    assert search_item["cover_image_url"] == "https://img.example.com/amoxicillin.jpg"


def test_admin_create_medicine_without_holder_defaults_to_self(api_client, db_session):
    admin = create_user(db_session, role="admin", nickname="管理员")
    headers = auth_headers(admin)
    categories_response = api_client.get("/api/v1/medicine-categories", headers=headers)
    assert categories_response.status_code == 200
    category_id = categories_response.json()["data"]["items"][0]["id"]

    response = api_client.post(
        "/api/v1/medicines",
        headers=headers,
        json={
            "catalog": {
                "name": "生理盐水",
                "category_id": category_id,
                "specification": "330ml/瓶",
                "unit": "瓶",
                "description": "清洁冲洗",
                "usage_notes": "外用",
                "photo_urls": [
                    "https://img.example.com/saline-1.jpg",
                    "https://img.example.com/saline-2.jpg",
                ],
            },
            "initial_quantity": 2,
            "remark": None,
        },
    )

    assert response.status_code == 200
    created = response.json()["data"]
    holding = db_session.get(MedicineHolding, UUID(created["holding_id"]))
    assert holding is not None
    assert holding.holder_id == admin.id
    assert holding.source_type == "self_created"
    assert holding.admin_creator_id is None


def test_holder_can_record_purchase_use_and_scrap(api_client, db_session):
    holder = create_user(db_session, nickname="持有人A")
    created = create_medicine(api_client, holder, db_session, initial_quantity=20)
    headers = auth_headers(holder)
    holding_url = f"/api/v1/medicine-holdings/{created['holding_id']}"

    purchase_response = api_client.post(
        f"{holding_url}/purchase",
        headers=headers,
        json={
            "quantity": 10,
            "source": "线下购买",
            "unit_price": 2.5,
            "operated_at": "2026-07-06T20:00:00+08:00",
            "remark": "补充库存",
        },
    )
    assert purchase_response.status_code == 200
    assert purchase_response.json()["data"]["current_quantity"] == 30
    assert purchase_response.json()["data"]["total_in_quantity"] == 30

    use_response = api_client.post(
        f"{holding_url}/use",
        headers=headers,
        json={
            "quantity": 3,
            "reason_type": "free_text",
            "reason_text": "北门小黑处理伤口后续用药",
            "usage_description": "今晚观察后使用",
            "related_task_id": None,
        },
    )
    assert use_response.status_code == 200
    assert use_response.json()["data"]["current_quantity"] == 27

    scrap_response = api_client.post(
        f"{holding_url}/scrap",
        headers=headers,
        json={
            "quantity": 2,
            "reason_type": "expired",
            "reason_text": "过期",
            "remark": "发现已过期",
        },
    )
    assert scrap_response.status_code == 200
    assert scrap_response.json()["data"]["current_quantity"] == 25

    detail = api_client.get(holding_url, headers=headers).json()["data"]
    assert detail["current_quantity"] == 25
    assert [log["operation_type"] for log in detail["recent_logs"][:4]] == [
        "scrap",
        "use_self",
        "purchase",
        "initial_in",
    ]


def test_medicine_log_list_and_holding_adjustment_contracts(api_client, db_session):
    holder = create_user(db_session, nickname="持有人A")
    created = create_medicine(api_client, holder, db_session, initial_quantity=20)
    headers = auth_headers(holder)
    holding_url = f"/api/v1/medicine-holdings/{created['holding_id']}"

    adjust_response = api_client.post(
        f"{holding_url}/adjust",
        headers=headers,
        json={
            "quantity": 18,
            "reason_text": "线下盘点校正",
            "operated_at": "2026-07-06T20:30:00+08:00",
        },
    )
    assert adjust_response.status_code == 200
    assert adjust_response.json()["data"]["current_quantity"] == 18

    medicine_logs_response = api_client.get(
        f"/api/v1/medicines/{created['medicine_id']}/logs",
        headers=headers,
    )
    assert medicine_logs_response.status_code == 200
    medicine_logs = medicine_logs_response.json()["data"]
    assert medicine_logs["total"] == 2
    assert medicine_logs["items"][0]["operation_type"] == "adjustment"
    assert medicine_logs["items"][0]["quantity_after"] == 18

    holding_logs_response = api_client.get(f"{holding_url}/logs", headers=headers)
    assert holding_logs_response.status_code == 200
    holding_logs = holding_logs_response.json()["data"]
    assert holding_logs["total"] == 2
    assert [item["operation_type"] for item in holding_logs["items"]] == [
        "adjustment",
        "initial_in",
    ]


def test_holder_can_distribute_and_transfer_stock_between_members(api_client, db_session):
    holder = create_user(db_session, nickname="持有人A")
    receiver = create_user(db_session, nickname="接收成员")
    created = create_medicine(api_client, holder, db_session, initial_quantity=20)
    headers = auth_headers(holder)
    holding_url = f"/api/v1/medicine-holdings/{created['holding_id']}"

    distribute_response = api_client.post(
        f"{holding_url}/distribute",
        headers=headers,
        json={
            "target_user_id": str(receiver.id),
            "quantity": 5,
            "remark": "给成员后续照护",
        },
    )
    assert distribute_response.status_code == 200
    distributed = distribute_response.json()["data"]
    assert distributed["source_current_quantity"] == 15
    assert distributed["target_current_quantity"] == 5
    assert distributed["source_holding_id"] == created["holding_id"]
    assert distributed["target_holding_id"] != created["holding_id"]

    receiver_detail = api_client.get(
        f"/api/v1/medicine-holdings/{distributed['target_holding_id']}",
        headers=auth_headers(receiver),
    ).json()["data"]
    assert receiver_detail["current_quantity"] == 5
    assert receiver_detail["permissions"]["can_record"] is True

    transfer_response = api_client.post(
        f"{holding_url}/transfer",
        headers=headers,
        json={
            "target_user_id": str(receiver.id),
            "reason": "库存交给新负责人",
        },
    )
    assert transfer_response.status_code == 200
    transferred = transfer_response.json()["data"]
    assert transferred["source_holding_id"] == created["holding_id"]
    assert transferred["target_holding_id"] == distributed["target_holding_id"]
    assert transferred["transferred_quantity"] == 15
    assert transferred["target_current_quantity"] == 20

    old_holder_response = api_client.get(holding_url, headers=headers)
    assert old_holder_response.status_code == 200
    old_holding = old_holder_response.json()["data"]
    assert old_holding["status"] == "transferred"
    assert old_holding["permissions"]["can_record"] is False


def test_non_holder_application_lifecycle(api_client, db_session):
    holder = create_user(db_session, nickname="持有人A")
    applicant = create_user(db_session, nickname="申请成员")
    created = create_medicine(api_client, holder, db_session, initial_quantity=20)
    holding_url = f"/api/v1/medicine-holdings/{created['holding_id']}"

    apply_response = api_client.post(
        f"{holding_url}/applications",
        headers=auth_headers(applicant),
        json={
            "quantity": 4,
            "reason_type": "free_text",
            "reason_text": "北门小黑后续用药",
            "usage_description": "今晚投喂后观察",
        },
    )
    assert apply_response.status_code == 200
    application_id = apply_response.json()["data"]["application_id"]
    assert apply_response.json()["data"]["status"] == "pending"

    application_list_response = api_client.get(
        "/api/v1/medicine-applications?scope=review",
        headers=auth_headers(holder),
    )
    assert application_list_response.status_code == 200
    application_list = application_list_response.json()["data"]
    assert application_list["total"] == 1
    assert application_list["items"][0]["application_id"] == application_id
    assert application_list["items"][0]["applicant"]["nickname"] == "申请成员"

    application_detail_response = api_client.get(
        f"/api/v1/medicine-applications/{application_id}",
        headers=auth_headers(applicant),
    )
    assert application_detail_response.status_code == 200
    application_detail = application_detail_response.json()["data"]
    assert application_detail["application_id"] == application_id
    assert application_detail["medicine"]["medicine_id"] == created["medicine_id"]
    assert application_detail["holding"]["holding_id"] == created["holding_id"]

    approve_response = api_client.post(
        f"/api/v1/medicine-applications/{application_id}/approve",
        headers=auth_headers(holder),
        json={"review_comment": "已线下分配"},
    )
    assert approve_response.status_code == 200
    approved = approve_response.json()["data"]
    assert approved["status"] == "approved"
    assert approved["current_quantity"] == 16
    assert approved["stock_log_id"]

    reject_apply_response = api_client.post(
        f"{holding_url}/applications",
        headers=auth_headers(applicant),
        json={"quantity": 2, "reason_text": "继续观察用药"},
    )
    assert reject_apply_response.status_code == 200
    reject_id = reject_apply_response.json()["data"]["application_id"]
    reject_response = api_client.post(
        f"/api/v1/medicine-applications/{reject_id}/reject",
        headers=auth_headers(holder),
        json={"review_comment": "暂不需要"},
    )
    assert reject_response.status_code == 200
    assert reject_response.json()["data"]["status"] == "rejected"

    cancel_apply_response = api_client.post(
        f"{holding_url}/applications",
        headers=auth_headers(applicant),
        json={"quantity": 1, "reason_text": "线下待确认"},
    )
    assert cancel_apply_response.status_code == 200
    cancel_id = cancel_apply_response.json()["data"]["application_id"]
    cancel_response = api_client.post(
        f"/api/v1/medicine-applications/{cancel_id}/cancel",
        headers=auth_headers(applicant),
        json={"cancel_reason": "线下已解决"},
    )
    assert cancel_response.status_code == 200
    assert cancel_response.json()["data"]["status"] == "cancelled"


def test_expired_application_cannot_be_approved(api_client, db_session):
    holder = create_user(db_session, nickname="持有人A")
    applicant = create_user(db_session, nickname="申请成员")
    created = create_medicine(api_client, holder, db_session, initial_quantity=20)
    response = api_client.post(
        f"/api/v1/medicine-holdings/{created['holding_id']}/applications",
        headers=auth_headers(applicant),
        json={"quantity": 3, "reason_text": "过期保护测试"},
    )
    assert response.status_code == 200
    application_id = response.json()["data"]["application_id"]
    application = db_session.get(MedicineUseApplication, UUID(application_id))
    assert application is not None
    application.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db_session.commit()

    approve_response = api_client.post(
        f"/api/v1/medicine-applications/{application_id}/approve",
        headers=auth_headers(holder),
        json={"review_comment": "过期后不能通过"},
    )

    assert approve_response.status_code == 409
    assert approve_response.json()["code"] == 66018


def test_admin_can_manage_categories_and_edit_catalog(api_client, db_session):
    admin = create_user(db_session, role="admin", nickname="管理员")
    member = create_user(db_session, nickname="持有人A")
    created = create_medicine(api_client, member, db_session, initial_quantity=20)
    admin_headers = auth_headers(admin)

    category_response = api_client.post(
        "/api/v1/admin/medicine-categories",
        headers=admin_headers,
        json={
            "name": "术后护理",
            "code": "post_surgery",
            "description": "术后恢复相关",
            "sort_order": 99,
        },
    )
    assert category_response.status_code == 200
    category = category_response.json()["data"]
    assert category["name"] == "术后护理"

    status_response = api_client.patch(
        f"/api/v1/admin/medicine-categories/{category['id']}/status",
        headers=admin_headers,
        json={"is_enabled": False},
    )
    assert status_response.status_code == 200
    assert status_response.json()["data"]["is_enabled"] is False

    edit_response = api_client.patch(
        f"/api/v1/admin/medicines/{created['medicine_id']}",
        headers=admin_headers,
        json={
            "name": "阿莫西林克拉维酸钾",
            "specification": "50mg/片",
            "unit": "片",
            "description": "更新后的说明",
            "usage_notes": "遵医嘱",
        },
    )
    assert edit_response.status_code == 200
    assert edit_response.json()["data"]["medicine_id"] == created["medicine_id"]

    detail = api_client.get(
        f"/api/v1/medicines/{created['medicine_id']}",
        headers=auth_headers(member),
    ).json()["data"]
    assert detail["name"] == "阿莫西林克拉维酸钾"
    assert detail["specification"] == "50mg/片"
    assert detail["description"] == "更新后的说明"


def test_admin_archive_and_delete_require_no_stock_or_pending_applications(
    api_client,
    db_session,
):
    admin = create_user(db_session, role="admin", nickname="管理员")
    holder = create_user(db_session, nickname="持有人A")
    applicant = create_user(db_session, nickname="申请人")
    created = create_medicine(api_client, holder, db_session, initial_quantity=20)
    admin_headers = auth_headers(admin)

    archive_with_stock = api_client.post(
        f"/api/v1/admin/medicines/{created['medicine_id']}/archive",
        headers=admin_headers,
        json={"archive_reason": "暂不使用"},
    )
    assert archive_with_stock.status_code == 409
    assert archive_with_stock.json()["code"] == 66013

    pending_apply = api_client.post(
        f"/api/v1/medicine-holdings/{created['holding_id']}/applications",
        headers=auth_headers(applicant),
        json={"quantity": 1, "reason_text": "待审核申请"},
    )
    assert pending_apply.status_code == 200
    use_all = api_client.post(
        f"/api/v1/medicine-holdings/{created['holding_id']}/use",
        headers=auth_headers(holder),
        json={"quantity": 20, "reason_text": "线下已用完"},
    )
    assert use_all.status_code == 200

    archive_with_pending = api_client.post(
        f"/api/v1/admin/medicines/{created['medicine_id']}/archive",
        headers=admin_headers,
        json={"archive_reason": "暂不使用"},
    )
    assert archive_with_pending.status_code == 409
    assert archive_with_pending.json()["code"] == 66014

    cancel_response = api_client.post(
        f"/api/v1/medicine-applications/{pending_apply.json()['data']['application_id']}/cancel",
        headers=auth_headers(applicant),
        json={"cancel_reason": "不用了"},
    )
    assert cancel_response.status_code == 200

    archive_response = api_client.post(
        f"/api/v1/admin/medicines/{created['medicine_id']}/archive",
        headers=admin_headers,
        json={"archive_reason": "无库存归档"},
    )
    assert archive_response.status_code == 200
    assert archive_response.json()["data"]["status"] == "archived"

    list_response = api_client.get("/api/v1/medicines", headers=auth_headers(holder))
    assert list_response.status_code == 200
    assert list_response.json()["data"]["items"] == []

    delete_response = api_client.delete(
        f"/api/v1/admin/medicines/{created['medicine_id']}?reason=误建测试档案",
        headers=admin_headers,
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["data"]["medicine_id"] == created["medicine_id"]


def test_admin_can_only_delete_empty_holding(api_client, db_session):
    admin = create_user(db_session, role="admin", nickname="管理员")
    holder = create_user(db_session, nickname="持有人A")
    created = create_medicine(api_client, holder, db_session, initial_quantity=20)
    admin_headers = auth_headers(admin)

    non_empty_delete = api_client.delete(
        f"/api/v1/admin/medicine-holdings/{created['holding_id']}?reason=成员退会",
        headers=admin_headers,
    )
    assert non_empty_delete.status_code == 409
    assert non_empty_delete.json()["code"] == 66022

    use_all = api_client.post(
        f"/api/v1/medicine-holdings/{created['holding_id']}/use",
        headers=auth_headers(holder),
        json={"quantity": 20, "reason_text": "线下已处理"},
    )
    assert use_all.status_code == 200

    delete_response = api_client.delete(
        f"/api/v1/admin/medicine-holdings/{created['holding_id']}?reason=成员退会",
        headers=admin_headers,
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["data"]["holding_id"] == created["holding_id"]

    detail_response = api_client.get(
        f"/api/v1/medicine-holdings/{created['holding_id']}",
        headers=auth_headers(holder),
    )
    assert detail_response.status_code == 404
