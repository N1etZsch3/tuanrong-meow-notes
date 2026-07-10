def test_auth_models_are_registered_in_metadata():
    from app.db.base import Base
    from app.modules.auth import models  # noqa: F401

    assert "users" in Base.metadata.tables
    assert "auth_captchas" in Base.metadata.tables
    assert "user_profiles" in Base.metadata.tables
    assert "admin_operation_logs" in Base.metadata.tables


def test_users_table_contains_required_auth_columns():
    from app.db.base import Base
    from app.modules.auth import models  # noqa: F401

    users = Base.metadata.tables["users"]

    for column_name in [
        "id",
        "student_no",
        "password_hash",
        "role",
        "status",
        "must_change_password",
        "token_version",
        "login_failed_count",
        "locked_until",
        "wechat_openid",
        "wechat_bound_at",
        "last_wechat_login_at",
    ]:
        assert column_name in users.c
