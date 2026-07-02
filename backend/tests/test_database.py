from collections.abc import Iterator

import pytest


def test_settings_requires_database_url(monkeypatch):
    from app.core.config import Settings

    monkeypatch.delenv("CATMAP_DATABASE_URL", raising=False)

    settings = Settings(_env_file=None, database_url=None)

    with pytest.raises(RuntimeError, match="CATMAP_DATABASE_URL"):
        _ = settings.required_database_url


def test_settings_returns_configured_database_url():
    from app.core.config import Settings

    database_url = "postgresql+psycopg://catmap_app:secret@example.test:35432/catmap"

    settings = Settings(_env_file=None, database_url=database_url)

    assert settings.required_database_url == database_url


def test_settings_reads_bom_prefixed_env_file(tmp_path, monkeypatch):
    from app.core.config import Settings

    monkeypatch.delenv("CATMAP_TENCENT_COS_SECRET_ID", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_bytes(
        "\ufeffCATMAP_TENCENT_COS_SECRET_ID=secret-id-from-env\n"
        "CATMAP_TENCENT_COS_SECRET_KEY=secret-key-from-env\n"
        "CATMAP_TENCENT_COS_BUCKET=catmap-test\n".encode()
    )

    settings = Settings(_env_file=env_file)

    assert settings.tencent_cos_secret_id == "secret-id-from-env"
    assert settings.tencent_cos_secret_key == "secret-key-from-env"
    assert settings.tencent_cos_bucket == "catmap-test"


def test_session_dependency_yields_session_and_closes(monkeypatch):
    import app.db.session as session_module

    closed = False

    class FakeSession:
        def close(self) -> None:
            nonlocal closed
            closed = True

    monkeypatch.setattr(session_module, "SessionLocal", lambda: FakeSession())

    dependency: Iterator[FakeSession] = session_module.get_db()
    session = next(dependency)

    assert isinstance(session, FakeSession)

    with pytest.raises(StopIteration):
        next(dependency)
    assert closed is True
