def test_public_stats_returns_envelope_without_auth(api_client):
    response = api_client.get("/api/v1/public/stats")

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    assert "trace_id" in payload
    data = payload["data"]
    assert data["in_campus_cats"] >= 0
    assert 0.0 <= data["neuter_rate"] <= 1.0
    assert data["total_cats"] >= data["in_campus_cats"]


def test_public_site_returns_association_info(api_client):
    response = api_client.get("/api/v1/public/site")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["association_name"]
    assert isinstance(data["intro_paragraphs"], list)
    assert isinstance(data["feeding_tips"], list)


def test_public_cats_list_paginates_and_hides_location_fields(api_client):
    response = api_client.get("/api/v1/public/cats", params={"page": 1, "page_size": 2})

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["items"]) <= 2
    assert data["total"] >= len(data["items"])

    item = data["items"][0]
    assert item["cat_id"]
    assert item["name"]
    # Location-bearing / internal fields must never appear in public output.
    leaked_fields = (
        "resident_area_text",
        "last_seen_at",
        "feeding_notes",
        "medical_notes",
        "capture_notes",
    )
    for leaked in leaked_fields:
        assert leaked not in item


def test_public_cats_keyword_filter(api_client):
    response = api_client.get("/api/v1/public/cats", params={"keyword": "橘"})

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] >= 1
    assert all("橘" in item["name"] or item["alias_summary"] for item in data["items"])


def test_public_cat_detail_returns_story_and_photos(api_client):
    list_response = api_client.get("/api/v1/public/cats")
    cat_id = list_response.json()["data"]["items"][0]["cat_id"]

    response = api_client.get(f"/api/v1/public/cats/{cat_id}")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["cat_id"] == cat_id
    assert isinstance(data["photos"], list)
    for leaked in ("resident_area_text", "last_seen_at", "medical_notes"):
        assert leaked not in data


def test_public_cat_detail_unknown_id_returns_404(api_client):
    response = api_client.get("/api/v1/public/cats/does-not-exist")

    assert response.status_code == 404
    assert response.json()["code"] == 40401


def test_public_posts_filter_by_type(api_client):
    trivia = api_client.get("/api/v1/public/posts", params={"type": "trivia"})
    merch = api_client.get("/api/v1/public/posts", params={"type": "merch"})

    assert trivia.status_code == 200
    assert merch.status_code == 200
    assert all(item["post_type"] == "trivia" for item in trivia.json()["data"]["items"])
    assert all(item["post_type"] == "merch" for item in merch.json()["data"]["items"])


def test_public_posts_rejects_invalid_type(api_client):
    response = api_client.get("/api/v1/public/posts", params={"type": "spam"})

    assert response.status_code == 400
    assert response.json()["code"] == 40001


def test_public_post_detail_returns_blocks(api_client):
    list_response = api_client.get("/api/v1/public/posts", params={"type": "trivia"})
    post_id = list_response.json()["data"]["items"][0]["post_id"]

    response = api_client.get(f"/api/v1/public/posts/{post_id}")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["post_id"] == post_id
    assert isinstance(data["blocks"], list)
    assert len(data["blocks"]) >= 1


def test_public_post_detail_unknown_id_returns_404(api_client):
    response = api_client.get("/api/v1/public/posts/does-not-exist")

    assert response.status_code == 404
    assert response.json()["code"] == 40401
