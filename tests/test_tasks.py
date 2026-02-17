from datetime import date, timedelta


async def test_create_task_success(client):
    payload = {
        "title": "Write assessment",
        "description": "FastAPI + Postgres",
        "priority": 4,
        "due_date": (date.today() + timedelta(days=1)).isoformat(),
        "tags": ["work", "urgent"],
    }
    r = await client.post("/tasks", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "Write assessment"
    assert data["priority"] == 4
    assert {t["name"] for t in data["tags"]} == {"work", "urgent"}


async def test_create_task_validation_priority(client):
    payload = {
        "title": "Bad priority",
        "priority": 99,
        "due_date": (date.today() + timedelta(days=1)).isoformat(),
    }
    r = await client.post("/tasks", json=payload)
    assert r.status_code == 422
    body = r.json()
    assert body["error"] == "Validation Failed"
    assert "priority" in body["details"]


async def test_create_task_validation_due_date_past(client):
    payload = {
        "title": "Past due",
        "priority": 3,
        "due_date": (date.today() - timedelta(days=1)).isoformat(),
    }
    r = await client.post("/tasks", json=payload)
    assert r.status_code == 422
    body = r.json()
    assert body["error"] == "Validation Failed"
    assert body["details"]["due_date"]


async def test_filter_by_priority_and_tags_any(client):
    # create tasks
    due = (date.today() + timedelta(days=3)).isoformat()

    await client.post("/tasks", json={"title": "t1", "priority": 5, "due_date": due, "tags": ["work"]})
    await client.post("/tasks", json={"title": "t2", "priority": 2, "due_date": due, "tags": ["home"]})
    await client.post("/tasks", json={"title": "t3", "priority": 5, "due_date": due, "tags": ["urgent"]})

    # filter priority=5 and tags includes ANY of work,urgent
    r = await client.get("/tasks", params={"priority": 5, "tags": "work,urgent", "limit": 50, "offset": 0})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 2
    titles = {t["title"] for t in body["items"]}
    assert "t1" in titles
    assert "t3" in titles


async def test_patch_partial_update_edge_cases(client):
    due = (date.today() + timedelta(days=5)).isoformat()
    create = await client.post(
        "/tasks",
        json={"title": "patchme", "description": "keep", "priority": 3, "due_date": due, "tags": ["a"]},
    )
    task_id = create.json()["id"]

    # patch only priority, ensure description unchanged
    r = await client.patch(f"/tasks/{task_id}", json={"priority": 5})
    assert r.status_code == 200
    data = r.json()
    assert data["priority"] == 5
    assert data["description"] == "keep"

    # patch description explicitly to null, should overwrite
    r2 = await client.patch(f"/tasks/{task_id}", json={"description": None})
    assert r2.status_code == 200
    assert r2.json()["description"] is None


async def test_soft_delete_removes_from_list(client):
    due = (date.today() + timedelta(days=2)).isoformat()
    create = await client.post("/tasks", json={"title": "delete-me", "priority": 1, "due_date": due})
    task_id = create.json()["id"]

    delr = await client.delete(f"/tasks/{task_id}")
    assert delr.status_code == 204

    # GET by id should be 404 now
    getr = await client.get(f"/tasks/{task_id}")
    assert getr.status_code == 404

    # list should not include it
    listr = await client.get("/tasks", params={"limit": 100, "offset": 0})
    titles = {t["title"] for t in listr.json()["items"]}
    assert "delete-me" not in titles
