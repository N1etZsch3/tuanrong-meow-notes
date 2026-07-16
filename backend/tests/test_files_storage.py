from app.modules.files.storage import (
    TencentCosObjectStorage,
    object_key_belongs_to_environment,
)


class RecordingCosClient:
    def __init__(self) -> None:
        self.deleted_keys: list[str] = []

    def delete_object(self, *, Bucket: str, Key: str) -> None:  # noqa: N803
        self.deleted_keys.append(Key)


def make_storage(environment: str = "dev") -> TencentCosObjectStorage:
    storage = object.__new__(TencentCosObjectStorage)
    storage._environment = environment
    storage._bucket = "test-bucket"
    storage._client = RecordingCosClient()
    return storage


def test_object_key_environment_guard_uses_complete_prefix() -> None:
    assert object_key_belongs_to_environment("catmap/dev/task/item.jpg", "dev")
    assert object_key_belongs_to_environment("catmap/dev/task/item.jpg", "/dev/")
    assert not object_key_belongs_to_environment("catmap/prod/task/item.jpg", "dev")
    assert not object_key_belongs_to_environment("catmap/development/task/item.jpg", "dev")
    assert not object_key_belongs_to_environment("catmap/dev/task/item.jpg", "")


def test_cos_delete_refuses_keys_from_another_environment() -> None:
    storage = make_storage()

    storage.delete_object("catmap/prod/task/production.jpg")
    storage.delete_object("catmap/dev/task/development.jpg")

    assert storage._client.deleted_keys == ["catmap/dev/task/development.jpg"]
