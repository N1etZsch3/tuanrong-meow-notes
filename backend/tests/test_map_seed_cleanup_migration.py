from pathlib import Path

SAMPLE_MAP_POINT_IDS = (
    "33333333-3333-4333-8333-333333333301",
    "33333333-3333-4333-8333-333333333302",
    "33333333-3333-4333-8333-333333333303",
    "33333333-3333-4333-8333-333333333304",
    "33333333-3333-4333-8333-333333333305",
)


def test_sample_map_points_are_removed_by_cleanup_migration() -> None:
    migration_path = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "20260624_0004_remove_sample_map_points.py"
    )

    assert migration_path.exists()

    migration_source = migration_path.read_text(encoding="utf-8")
    assert "DELETE FROM map_points" in migration_source

    for point_id in SAMPLE_MAP_POINT_IDS:
        assert point_id in migration_source
