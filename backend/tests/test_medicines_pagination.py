"""Regression tests for medicine catalog/log/application DB pagination, the
EXISTS-based mine/others filter, batched stock summaries, and query-count scaling."""

from uuid import uuid4

from tests.test_medicines_api import auth_headers, create_medicine, create_user
from tests.test_tasks_pagination import QueryCounter


def _create_named_medicine(api_client, user, *, name, initial_quantity=5):
    categories = api_client.get(
        "/api/v1/medicine-categories", headers=auth_headers(user)
    ).json()["data"]["items"]
    response = api_client.post(
        "/api/v1/medicines",
        headers=auth_headers(user),
        json={
            "catalog": {
                "name": name,
                "category_id": categories[0]["id"],
                "unit": "片",
            },
            "initial_quantity": initial_quantity,
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


def test_catalog_pagination_total_and_pages_are_stable(api_client, db_session):
    holder = create_user(db_session, nickname="持有人A")
    created_ids = {
        _create_named_medicine(api_client, holder, name=f"药品{index:02d}-{uuid4().hex[:4]}")[
            "medicine_id"
        ]
        for index in range(12)
    }

    first = api_client.get(
        "/api/v1/medicines?page=1&page_size=5", headers=auth_headers(holder)
    ).json()["data"]
    assert first["total"] == 12
    assert len(first["items"]) == 5
    assert first["has_more"] is True

    collected = []
    for page in range(1, 4):
        data = api_client.get(
            f"/api/v1/medicines?page={page}&page_size=5", headers=auth_headers(holder)
        ).json()["data"]
        collected.extend(item["medicine_id"] for item in data["items"])
    assert len(collected) == 12
    assert set(collected) == created_ids  # no duplicates or drops across pages
    last = api_client.get(
        "/api/v1/medicines?page=3&page_size=5", headers=auth_headers(holder)
    ).json()["data"]
    assert len(last["items"]) == 2
    assert last["has_more"] is False


def test_mine_and_others_filters_use_holdings_correctly(api_client, db_session):
    alice = create_user(db_session, nickname="甲")
    bob = create_user(db_session, nickname="乙")
    mine_ids = {
        _create_named_medicine(api_client, alice, name=f"甲的药{index}-{uuid4().hex[:4]}")[
            "medicine_id"
        ]
        for index in range(3)
    }
    other_ids = {
        _create_named_medicine(api_client, bob, name=f"乙的药{index}-{uuid4().hex[:4]}")[
            "medicine_id"
        ]
        for index in range(2)
    }

    mine = api_client.get(
        "/api/v1/medicines?holding_relation=mine", headers=auth_headers(alice)
    ).json()["data"]
    assert mine["total"] == 3
    assert {item["medicine_id"] for item in mine["items"]} == mine_ids

    others = api_client.get(
        "/api/v1/medicines?holding_relation=others", headers=auth_headers(alice)
    ).json()["data"]
    assert others["total"] == 2
    assert {item["medicine_id"] for item in others["items"]} == other_ids

    # After bob distributes stock to alice, that medicine becomes "mine" for alice too.
    distributed_id = next(iter(other_ids))
    holdings = api_client.get(
        f"/api/v1/medicines/{distributed_id}/holdings", headers=auth_headers(bob)
    ).json()["data"]["items"]
    distribute = api_client.post(
        f"/api/v1/medicine-holdings/{holdings[0]['holding_id']}/distribute",
        headers=auth_headers(bob),
        json={"target_user_id": str(alice.id), "quantity": 1},
    )
    assert distribute.status_code == 200

    mine_after = api_client.get(
        "/api/v1/medicines?holding_relation=mine", headers=auth_headers(alice)
    ).json()["data"]
    assert mine_after["total"] == 4
    others_after = api_client.get(
        "/api/v1/medicines?holding_relation=others", headers=auth_headers(alice)
    ).json()["data"]
    assert others_after["total"] == 1


def test_catalog_summary_aggregates_multiple_holders(api_client, db_session):
    alice = create_user(db_session, nickname="甲")
    bob = create_user(db_session, nickname="乙")
    created = _create_named_medicine(
        api_client, alice, name=f"共享药-{uuid4().hex[:4]}", initial_quantity=10
    )
    distribute = api_client.post(
        f"/api/v1/medicine-holdings/{created['holding_id']}/distribute",
        headers=auth_headers(alice),
        json={"target_user_id": str(bob.id), "quantity": 4},
    )
    assert distribute.status_code == 200

    data = api_client.get("/api/v1/medicines", headers=auth_headers(alice)).json()["data"]
    item = next(i for i in data["items"] if i["medicine_id"] == created["medicine_id"])
    assert item["holder_count"] == 2
    assert item["total_current_quantity"] == 10  # 6 + 4
    assert item["total_in_quantity"] == 14  # 10 initial + 4 distributed-in
    holder_quantities = {h["holder_nickname"]: h["current_quantity"] for h in item["holders"]}
    assert holder_quantities == {"甲": 6, "乙": 4}


def test_list_query_count_constant_regardless_of_catalog_size(api_client, db_session):
    holder = create_user(db_session, nickname="持有人A")
    for index in range(3):
        _create_named_medicine(api_client, holder, name=f"批次一-{index}-{uuid4().hex[:4]}")
    headers = auth_headers(holder)

    api_client.get("/api/v1/medicines?page=1&page_size=10", headers=headers)  # warm auth
    with QueryCounter(db_session) as small:
        api_client.get("/api/v1/medicines?page=1&page_size=10", headers=headers)

    for index in range(15):
        _create_named_medicine(api_client, holder, name=f"批次二-{index}-{uuid4().hex[:4]}")

    api_client.get("/api/v1/medicines?page=1&page_size=10", headers=headers)  # re-warm auth
    with QueryCounter(db_session) as large:
        api_client.get("/api/v1/medicines?page=1&page_size=10", headers=headers)

    # 3 rows vs 18 rows in the table, same page size ⇒ identical statement count
    # (count + page query + batched holdings; no per-medicine holdings/COUNT queries).
    assert small.count == large.count
    assert large.count <= 6

    with QueryCounter(db_session) as mine_counter:
        api_client.get(
            "/api/v1/medicines?holding_relation=mine&page=1&page_size=10", headers=headers
        )
    # mine/others uses EXISTS inside the same statements — no extra per-catalog queries.
    assert mine_counter.count == large.count


def test_stock_log_pagination_pushed_to_database(api_client, db_session):
    holder = create_user(db_session, nickname="持有人A")
    created = create_medicine(api_client, holder, db_session, initial_quantity=20)
    headers = auth_headers(holder)
    holding_url = f"/api/v1/medicine-holdings/{created['holding_id']}"

    api_client.post(f"{holding_url}/purchase", headers=headers, json={"quantity": 5})
    api_client.post(
        f"{holding_url}/use",
        headers=headers,
        json={"quantity": 2, "reason_text": "日常用药"},
    )
    api_client.post(
        f"{holding_url}/scrap",
        headers=headers,
        json={"quantity": 1, "reason_type": "expired", "reason_text": "过期"},
    )
    api_client.post(
        f"{holding_url}/adjust",
        headers=headers,
        json={"quantity": 20, "reason_text": "盘点校正"},
    )
    # 5 logs total: initial_in + purchase + use_self + scrap + adjustment

    collected = []
    for page in range(1, 4):
        data = api_client.get(
            f"{holding_url}/logs?page={page}&page_size=2", headers=headers
        ).json()["data"]
        assert data["total"] == 5
        collected.extend(item["id"] for item in data["items"])
        assert data["has_more"] is (page * 2 < 5)
    assert len(collected) == 5
    assert len(set(collected)) == 5  # no duplicates or drops across pages

    medicine_logs = api_client.get(
        f"/api/v1/medicines/{created['medicine_id']}/logs?page=2&page_size=3",
        headers=headers,
    ).json()["data"]
    assert medicine_logs["total"] == 5
    assert len(medicine_logs["items"]) == 2
    assert medicine_logs["has_more"] is False

    with QueryCounter(db_session) as counter:
        api_client.get(f"{holding_url}/logs?page=1&page_size=2", headers=headers)
    assert counter.count <= 5  # fetch holding + count + page (+ joined loads inline)


def test_applications_list_paginates_in_database(api_client, db_session):
    holder = create_user(db_session, nickname="持有人A")
    applicant = create_user(db_session, nickname="申请人B")
    created = create_medicine(api_client, holder, db_session, initial_quantity=20)

    for index in range(3):
        response = api_client.post(
            f"/api/v1/medicine-holdings/{created['holding_id']}/applications",
            headers=auth_headers(applicant),
            json={"quantity": 1, "reason_text": f"救助用药{index}"},
        )
        assert response.status_code == 200

    page_one = api_client.get(
        "/api/v1/medicine-applications?scope=mine&page=1&page_size=2",
        headers=auth_headers(applicant),
    ).json()["data"]
    assert page_one["total"] == 3
    assert len(page_one["items"]) == 2
    assert page_one["has_more"] is True

    page_two = api_client.get(
        "/api/v1/medicine-applications?scope=mine&page=2&page_size=2",
        headers=auth_headers(applicant),
    ).json()["data"]
    assert len(page_two["items"]) == 1
    assert page_two["has_more"] is False
    ids = {item["application_id"] for item in page_one["items"]} | {
        item["application_id"] for item in page_two["items"]
    }
    assert len(ids) == 3


def test_categories_get_is_read_only_after_seeding(api_client, db_session):
    member = create_user(db_session)
    headers = auth_headers(member)
    first = api_client.get("/api/v1/medicine-categories", headers=headers)
    assert first.status_code == 200
    assert len(first.json()["data"]["items"]) == 8  # seeded on first read

    with QueryCounter(db_session) as counter:
        second = api_client.get("/api/v1/medicine-categories", headers=headers)
    assert second.status_code == 200
    assert second.json()["data"] == first.json()["data"]
    # Steady state: count-check + select only; no INSERT/COMMIT statements.
    assert counter.count <= 4
