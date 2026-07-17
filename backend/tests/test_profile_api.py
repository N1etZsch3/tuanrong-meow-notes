from tests.test_auth_api import auth_headers, create_token, create_user


def test_get_profile_me_returns_current_user_identity(api_client, db_session):
    user = create_user(
        db_session,
        student_no="trmx0001",
        password="trmx0001",
        must_change_password=False,
        profile_completed=False,
    )
    token = create_token(user)

    response = api_client.get("/api/v1/profile/me", headers=auth_headers(token))

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["meow_no"] == "trmx0001"
    assert data["nickname"] == "小林"
    assert data["profile_completed"] is False


def test_get_profile_me_hides_question_mark_initial_placeholders(api_client, db_session):
    user = create_user(
        db_session,
        student_no="trmx0001",
        password="trmx0001",
        must_change_password=False,
        profile_completed=False,
    )
    user.profile.nickname = "????"
    user.profile.department = "?????"
    user.profile.contact_info = "????"
    db_session.commit()
    token = create_token(user)

    response = api_client.get("/api/v1/profile/me", headers=auth_headers(token))

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["nickname"] == ""
    assert data["department"] is None
    assert data["contact_info"] is None


def test_complete_profile_saves_required_identity_fields(api_client, db_session):
    user = create_user(
        db_session,
        student_no="trmx0001",
        password="trmx0001",
        must_change_password=False,
        profile_completed=False,
    )
    token = create_token(user)

    response = api_client.post(
        "/api/v1/profile/me/complete",
        headers=auth_headers(token),
        json={
            "nickname": "喂猫搭子🥜",
            "avatar_url": None,
            "department": "生存保障部",
            "contact_info": "13800138000",
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["profile_completed"] is True
    assert data["next_action"] == "enter_app"

    db_session.refresh(user.profile)
    assert user.profile.nickname == "喂猫搭子🥜"
    assert user.profile.department == "生存保障部"
    assert user.profile.contact_info == "13800138000"
    assert user.profile.profile_completed is True
    assert user.profile.profile_completed_at is not None


def test_update_profile_me_edits_text_fields_without_bypassing_avatar_review(
    api_client,
    db_session,
):
    user = create_user(
        db_session,
        student_no="trmx0001",
        password="Password123",
        must_change_password=False,
        profile_completed=True,
    )
    token = create_token(user)

    response = api_client.patch(
        "/api/v1/profile/me",
        headers=auth_headers(token),
        json={
            "nickname": "巡查搭子",
            "department": "活动部",
            "contact_info": "13900139000",
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["nickname"] == "巡查搭子"
    assert data["avatar_url"] is None
    assert data["department"] == "活动部"
    assert data["contact_info"] == "13900139000"

    db_session.refresh(user.profile)
    assert user.profile.nickname == "巡查搭子"
    assert user.profile.department == "活动部"
    assert user.profile.contact_info == "13900139000"


def test_update_profile_me_validates_phone_department_and_nickname(api_client, db_session):
    user = create_user(
        db_session,
        student_no="trmx0001",
        password="Password123",
        must_change_password=False,
        profile_completed=True,
    )
    token = create_token(user)

    response = api_client.patch(
        "/api/v1/profile/me",
        headers=auth_headers(token),
        json={
            "nickname": "",
            "department": "救助部",
            "contact_info": "12345",
        },
    )

    assert response.status_code == 422


def test_complete_profile_validates_phone_department_and_nickname(api_client, db_session):
    user = create_user(db_session, must_change_password=False)
    token = create_token(user)

    response = api_client.post(
        "/api/v1/profile/me/complete",
        headers=auth_headers(token),
        json={
            "nickname": "超过二十个字符的昵称不应该被初始化接口接受",
            "department": "救助部",
            "contact_info": "12345",
        },
    )

    assert response.status_code == 422


def test_profile_complete_requires_password_changed(api_client, db_session):
    user = create_user(db_session, must_change_password=True)
    token = create_token(user)

    response = api_client.post(
        "/api/v1/profile/me/complete",
        headers=auth_headers(token),
        json={
            "nickname": "小林",
            "department": "生存保障部",
            "contact_info": "13800138000",
        },
    )

    assert response.status_code == 403
    assert response.json()["code"] == 40301


def test_complete_and_update_profile_supports_multiple_departments(api_client, db_session):
    user = create_user(
        db_session,
        student_no="trmx0007",
        password="trmx0007",
        must_change_password=False,
        profile_completed=False,
    )
    token = create_token(user)

    complete = api_client.post(
        "/api/v1/profile/me/complete",
        headers=auth_headers(token),
        json={
            "nickname": "多部门同学",
            "departments": ["生存保障部", "活动部"],
            "contact_info": "13800138000",
        },
    )
    assert complete.status_code == 200

    profile = api_client.get("/api/v1/profile/me", headers=auth_headers(token))
    assert profile.status_code == 200
    data = profile.json()["data"]
    assert data["departments"] == ["生存保障部", "活动部"]
    # 主部门（兼容旧单值字段）= 第一个部门
    assert data["department"] == "生存保障部"

    # 更新为不同的多部门集合，验证增删对齐
    update = api_client.patch(
        "/api/v1/profile/me",
        headers=auth_headers(token),
        json={"departments": ["宣传部", "秘书部", "养护部"]},
    )
    assert update.status_code == 200
    assert update.json()["data"]["departments"] == ["宣传部", "秘书部", "养护部"]
    assert update.json()["data"]["department"] == "宣传部"


def test_complete_profile_rejects_empty_departments(api_client, db_session):
    user = create_user(
        db_session,
        student_no="trmx0008",
        password="trmx0008",
        must_change_password=False,
        profile_completed=False,
    )
    token = create_token(user)

    response = api_client.post(
        "/api/v1/profile/me/complete",
        headers=auth_headers(token),
        json={
            "nickname": "无部门同学",
            "departments": [],
            "contact_info": "13800138000",
        },
    )
    assert response.status_code == 422


def test_update_profile_legacy_single_department_still_works(api_client, db_session):
    user = create_user(
        db_session,
        student_no="trmx0009",
        password="trmx0009",
        must_change_password=False,
        profile_completed=True,
    )
    token = create_token(user)

    # 旧客户端只传单值 department
    update = api_client.patch(
        "/api/v1/profile/me",
        headers=auth_headers(token),
        json={"department": "活动部"},
    )
    assert update.status_code == 200
    assert update.json()["data"]["departments"] == ["活动部"]
    assert update.json()["data"]["department"] == "活动部"
