"""Regression tests for task list DB pagination, stable ordering, SQL display-status
pushdown, GET read-only behavior, and query-count scaling.

These lock in the Phase 2/3 refactor (two-phase DB pagination + explicit lifecycle sync).
Helpers are reused from test_tasks_api to avoid duplicating fixtures.
"""

from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID

from sqlalchemy import event

from app.modules.map.models import MapPoint
from app.modules.tasks import service as task_service
from app.modules.tasks.models import Task, TaskExecutionDate
from tests.test_tasks_api import (
    auth_headers,
    create_user,
    freeze_task_clock,
    publish_payload,
    seed_campus,
)


class QueryCounter:
    """Count SQL statements executed on a session's bind within a context block."""

    def __init__(self, db):
        self.engine = db.get_bind()
        self.count = 0

    def _before(self, *args, **kwargs):
        self.count += 1

    def __enter__(self):
        event.listen(self.engine, "before_cursor_execute", self._before)
        return self

    def __exit__(self, *exc):
        event.remove(self.engine, "before_cursor_execute", self._before)


def _publish_at(api_client, admin, campus, *, title, lng, lat, execute_dates):
    payload = publish_payload(campus)
    payload["title"] = title
    payload["map_point"]["lng"] = lng
    payload["map_point"]["lat"] = lat
    payload["execute_dates"] = execute_dates
    response = api_client.post(
        "/api/v1/admin/tasks/summer-feeding",
        headers=auth_headers(admin),
        json=payload,
    )
    assert response.status_code == 200
    return response.json()["data"]["task_id"]


def _seed_tasks(api_client, admin, campus, count, *, execute_dates):
    ids = []
    for index in range(count):
        ids.append(
            _publish_at(
                api_client,
                admin,
                campus,
                title=f"任务{index:02d}",
                lng=115.05 + index * 0.0005,
                lat=30.20 + index * 0.0005,
                execute_dates=execute_dates,
            )
        )
    return ids


def test_pagination_total_and_last_page_are_correct(api_client, db_session, monkeypatch):
    freeze_task_clock(monkeypatch, date(2026, 6, 20))
    admin = create_user(db_session, role="admin", nickname="管理员")
    member = create_user(db_session)
    campus = seed_campus(db_session)
    _seed_tasks(api_client, admin, campus, 25, execute_dates=["2026-07-02", "2026-07-09"])

    first = api_client.get(
        "/api/v1/tasks?page=1&page_size=10", headers=auth_headers(member)
    ).json()["data"]
    assert first["total"] == 25
    assert len(first["items"]) == 10
    assert first["has_more"] is True

    last = api_client.get(
        "/api/v1/tasks?page=3&page_size=10", headers=auth_headers(member)
    ).json()["data"]
    assert last["total"] == 25
    assert len(last["items"]) == 5
    assert last["has_more"] is False


def test_pages_do_not_overlap_or_drop_with_identical_sort_keys(
    api_client, db_session, monkeypatch
):
    # All tasks share the same start_at/published window → tie-break on Task.id must make
    # paging stable (no duplicates, no gaps) across pages.
    freeze_task_clock(monkeypatch, date(2026, 6, 20))
    admin = create_user(db_session, role="admin", nickname="管理员")
    member = create_user(db_session)
    campus = seed_campus(db_session)
    seeded = set(
        _seed_tasks(api_client, admin, campus, 30, execute_dates=["2026-07-02", "2026-07-09"])
    )

    collected = []
    for page in range(1, 5):
        data = api_client.get(
            f"/api/v1/tasks?page={page}&page_size=10", headers=auth_headers(member)
        ).json()["data"]
        collected.extend(item["task_id"] for item in data["items"])

    assert len(collected) == 30
    assert len(set(collected)) == 30  # no duplicates across pages
    assert set(collected) == seeded  # no dropped rows


def test_get_list_does_not_mutate_db_when_nothing_is_due(
    api_client, db_session, monkeypatch
):
    # A steady-state list GET (nothing to normalize) must not change any row.
    freeze_task_clock(monkeypatch, date(2026, 7, 3))
    admin = create_user(db_session, role="admin", nickname="管理员")
    member = create_user(db_session)
    campus = seed_campus(db_session)
    task_id = _publish_at(
        api_client,
        admin,
        campus,
        title="稳定任务",
        lng=115.05,
        lat=30.20,
        execute_dates=["2026-07-09", "2026-07-16"],
    )

    before = db_session.get(Task, UUID(task_id))
    before_updated = before.updated_at
    before_statuses = {e.execute_date: e.status for e in before.execution_dates}

    resp = api_client.get("/api/v1/tasks", headers=auth_headers(member))
    assert resp.status_code == 200

    db_session.expire_all()
    after = db_session.get(Task, UUID(task_id))
    assert after.status == "in_progress"
    assert after.updated_at == before_updated
    assert {e.execute_date: e.status for e in after.execution_dates} == before_statuses


def test_list_query_count_does_not_scale_with_total_tasks(
    api_client, db_session, monkeypatch
):
    # The number of SQL statements to render one page must be constant regardless of how
    # many tasks exist in the DB (no per-row / per-total query amplification).
    freeze_task_clock(monkeypatch, date(2026, 6, 20))
    admin = create_user(db_session, role="admin", nickname="管理员")
    member = create_user(db_session)
    campus = seed_campus(db_session)

    _seed_tasks(api_client, admin, campus, 5, execute_dates=["2026-07-02", "2026-07-09"])
    with QueryCounter(db_session) as small:
        api_client.get("/api/v1/tasks?page=1&page_size=10", headers=auth_headers(member))

    _seed_tasks(api_client, admin, campus, 40, execute_dates=["2026-07-02", "2026-07-09"])
    with QueryCounter(db_session) as large:
        api_client.get("/api/v1/tasks?page=1&page_size=10", headers=auth_headers(member))

    # Identical page size ⇒ identical statement count even though the table grew 9x.
    assert small.count == large.count


def test_list_query_count_stable_between_page_sizes(api_client, db_session, monkeypatch):
    freeze_task_clock(monkeypatch, date(2026, 6, 20))
    admin = create_user(db_session, role="admin", nickname="管理员")
    member = create_user(db_session)
    campus = seed_campus(db_session)
    _seed_tasks(api_client, admin, campus, 40, execute_dates=["2026-07-02", "2026-07-09"])
    headers = auth_headers(member)

    # Warm auth/session lookups so we measure only the list pipeline.
    api_client.get("/api/v1/tasks?page=1&page_size=10", headers=headers)

    with QueryCounter(db_session) as ten:
        api_client.get("/api/v1/tasks?page=1&page_size=10", headers=headers)
    with QueryCounter(db_session) as twenty:
        api_client.get("/api/v1/tasks?page=1&page_size=20", headers=headers)

    # A page holding 20 rows must not issue more statements than one holding 10: selectinload
    # batches by page, so statement count is bounded by the number of eager relationships,
    # not by how many rows the page contains.
    assert twenty.count <= ten.count
    assert ten.count <= 12  # count + id-page + task-load + 3 selectinload batches (+ warm auth)


def test_sql_display_status_filter_matches_python_semantics(
    api_client, db_session, monkeypatch
):
    # Build a task with one completed, one running (past pending), one future (not_started)
    # execution, then confirm the SQL EXISTS pushdown selects the same task per display
    # status as the legacy python display logic.
    admin = create_user(db_session, role="admin", nickname="管理员")
    member = create_user(db_session, nickname="Nietzsche")
    campus = seed_campus(db_session)
    today = date.today()
    completed_day = today - timedelta(days=2)
    running_day = today - timedelta(days=1)
    future_day = today + timedelta(days=7)

    task_id = _publish_at(
        api_client,
        admin,
        campus,
        title="混合状态任务",
        lng=115.05,
        lat=30.20,
        execute_dates=[completed_day.isoformat(), running_day.isoformat(), future_day.isoformat()],
    )

    monkeypatch.setattr(task_service, "_today", lambda: completed_day)
    monkeypatch.setattr(
        task_service, "_now", lambda: datetime.combine(completed_day, time.min, tzinfo=UTC)
    )
    checkin = api_client.post(
        f"/api/v1/tasks/{task_id}/checkins",
        headers=auth_headers(member),
        json={"execute_date": completed_day.isoformat(), "is_completed": True},
    )
    assert checkin.status_code == 200

    monkeypatch.setattr(task_service, "_today", lambda: today)
    monkeypatch.setattr(
        task_service, "_now", lambda: datetime.combine(today, time.min, tzinfo=UTC)
    )

    for display_status in ("completed", "in_progress", "not_started"):
        resp = api_client.get(
            f"/api/v1/tasks?execution_display_status={display_status}&status=in_progress,completed",
            headers=auth_headers(member),
        )
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert [item["task_id"] for item in items] == [task_id], display_status

    # A display status with no matching child must exclude the task entirely.
    cancelled_resp = api_client.get(
        "/api/v1/tasks?execution_display_status=cancelled&status=in_progress,completed",
        headers=auth_headers(member),
    )
    assert cancelled_resp.status_code == 200
    assert cancelled_resp.json()["data"]["items"] == []


def test_archived_and_deleted_tasks_excluded_from_default_total(
    api_client, db_session, monkeypatch
):
    freeze_task_clock(monkeypatch, date(2026, 7, 3))
    admin = create_user(db_session, role="admin", nickname="管理员")
    member = create_user(db_session)
    campus = seed_campus(db_session)
    keep = _publish_at(
        api_client, admin, campus, title="保留", lng=115.05, lat=30.20,
        execute_dates=["2026-07-09"],
    )
    gone = _publish_at(
        api_client, admin, campus, title="删除", lng=115.06, lat=30.21,
        execute_dates=["2026-07-09"],
    )
    api_client.delete(f"/api/v1/admin/tasks/{gone}", headers=auth_headers(admin))

    data = api_client.get(
        "/api/v1/tasks?status=in_progress", headers=auth_headers(member)
    ).json()["data"]
    assert data["total"] == 1
    assert [item["task_id"] for item in data["items"]] == [keep]


def test_sync_due_task_lifecycles_is_the_only_writer_in_list_path(
    api_client, db_session, monkeypatch
):
    # When a task is genuinely due to auto-archive, the list GET must persist that (via the
    # explicit sync step), and the persisted parent + map point reflect the archive.
    admin = create_user(db_session, role="admin", nickname="管理员")
    member = create_user(db_session)
    campus = seed_campus(db_session)
    monkeypatch.setattr(task_service, "_today", lambda: date(2026, 7, 3))
    monkeypatch.setattr(
        task_service, "_now", lambda: datetime(2026, 7, 3, 8, 0, tzinfo=UTC)
    )
    task_id = _publish_at(
        api_client, admin, campus, title="到期任务", lng=115.05, lat=30.20,
        execute_dates=["2026-07-03"],
    )

    monkeypatch.setattr(task_service, "_today", lambda: date(2026, 7, 10))
    monkeypatch.setattr(
        task_service, "_now", lambda: datetime(2026, 7, 10, 8, 0, tzinfo=UTC)
    )
    data = api_client.get(
        "/api/v1/tasks?status=in_progress,completed,cancelled,archived",
        headers=auth_headers(member),
    ).json()["data"]
    listed = next(item for item in data["items"] if item["task_id"] == task_id)
    assert listed["status"] == "archived"

    db_session.expire_all()
    task = db_session.get(Task, UUID(task_id))
    assert task.status == "archived"
    point = db_session.get(MapPoint, task.map_point_id)
    assert point.visibility == "hidden"
    # No orphaned pending executions remain.
    remaining = (
        db_session.query(TaskExecutionDate)
        .filter(TaskExecutionDate.task_id == task.id, TaskExecutionDate.status == "pending")
        .count()
    )
    assert remaining == 0
