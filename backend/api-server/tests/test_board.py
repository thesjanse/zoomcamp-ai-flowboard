def test_board_full(client, demo):
    res = client.get("/api/projects/p1/board", headers=demo)
    assert res.status_code == 200
    body = res.json()
    assert body["project"]["name"] == "Northstar"
    assert len(body["columns"]) == 4
    assert len(body["cards"]) == 7
    assert len(body["comments"]) == 2
    assert len(body["members"]) == 5


def test_board_forbidden(client, rowan):
    assert client.get("/api/projects/p2/board", headers=rowan).status_code == 404


def test_board_requires_auth(client):
    assert client.get("/api/projects/p1/board").status_code == 401


def test_board_search(client, demo):
    res = client.get("/api/projects/p1/board", params={"search": "ready"}, headers=demo)
    assert [c["id"] for c in res.json()["cards"]] == ["NST-142"]


def test_board_priority_filter(client, demo):
    res = client.get(
        "/api/projects/p1/board", params={"priorities": "urgent"}, headers=demo
    )
    assert [c["id"] for c in res.json()["cards"]] == ["NST-141"]

    res = client.get(
        "/api/projects/p1/board", params={"priorities": "high"}, headers=demo
    )
    assert {c["id"] for c in res.json()["cards"]} == {"NST-142", "NST-147"}


def test_board_assignee_filter(client, demo):
    res = client.get(
        "/api/projects/p1/board", params={"assigneeId": "u4"}, headers=demo
    )
    assert {c["id"] for c in res.json()["cards"]} == {"NST-138", "NST-147"}


def test_board_due_overdue(client, demo):
    res = client.get("/api/projects/p1/board", params={"due": "overdue"}, headers=demo)
    assert [c["id"] for c in res.json()["cards"]] == ["NST-141"]


def test_board_due_no_date(client, demo):
    res = client.get("/api/projects/p1/board", params={"due": "no-date"}, headers=demo)
    assert {c["id"] for c in res.json()["cards"]} == {"NST-138", "NST-129"}


def test_board_due_this_week(client, demo):
    res = client.get("/api/projects/p1/board", params={"due": "this-week"}, headers=demo)
    ids = {c["id"] for c in res.json()["cards"]}
    assert ids == {"NST-142", "NST-145", "NST-147", "NST-136"}


def test_board_combined_filters(client, demo):
    other = client.post(
        "/api/projects/p1/cards",
        json={
            "title": "urgent and high",
            "description": "things to ship now",
            "priority": "urgent",
            "assigneeId": "u4",
            "dueDate": None,
            "labels": [],
            "columnId": "column-1",
        },
        headers=demo,
    )
    assert other.status_code == 201

    res = client.get(
        "/api/projects/p1/board",
        params={"search": "urgent and high"},
        headers=demo,
    )
    assert [c["id"] for c in res.json()["cards"]] == ["NST-148"]