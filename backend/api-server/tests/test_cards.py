def test_create_card(client, demo):
    res = client.post(
        "/api/projects/p1/cards",
        json={
            "title": "Fresh card",
            "description": "A fresh card",
            "priority": "medium",
            "assigneeId": "u4",
            "dueDate": "2026-12-25",
            "labels": ["UX"],
            "columnId": "column-1",
        },
        headers=demo,
    )
    assert res.status_code == 201
    body = res.json()
    assert body["id"] == "NST-148"
    assert body["projectId"] == "p1"
    assert body["columnId"] == "column-1"
    assert body["priority"] == "medium"
    assert body["assigneeId"] == "u4"
    assert body["dueDate"] == "2026-12-25"
    assert body["labels"] == ["UX"]
    assert body["creatorId"] == "u1"
    assert body["position"] == 3
    assert body["blocking"] == []
    assert body["blockedBy"] == []


def test_create_card_appends_in_column(client, demo):
    client.post(
        "/api/projects/p1/cards",
        json={
            "title": "One",
            "description": "",
            "priority": "low",
            "assigneeId": None,
            "dueDate": None,
            "labels": [],
            "columnId": "column-1",
        },
        headers=demo,
    )
    res = client.post(
        "/api/projects/p1/cards",
        json={
            "title": "Two",
            "description": "",
            "priority": "low",
            "assigneeId": None,
            "dueDate": None,
            "labels": [],
            "columnId": "column-1",
        },
        headers=demo,
    )
    assert res.json()["id"] == "NST-149"
    assert res.json()["position"] == 4


def test_create_card_invalid_column(client, demo):
    res = client.post(
        "/api/projects/p1/cards",
        json={
            "title": "Bad col",
            "description": "",
            "priority": "low",
            "assigneeId": None,
            "dueDate": None,
            "labels": [],
            "columnId": "column-5",
        },
        headers=demo,
    )
    assert res.status_code == 422


def test_create_card_assignee_must_be_member(client, demo):
    res = client.post(
        "/api/projects/p2/cards",
        json={
            "title": "Bad assignee",
            "description": "",
            "priority": "low",
            "assigneeId": "u5",
            "dueDate": None,
            "labels": [],
            "columnId": "column-5",
        },
        headers=demo,
    )
    assert res.status_code == 422


def test_create_card_empty_title(client, demo):
    res = client.post(
        "/api/projects/p1/cards",
        json={
            "title": "",
            "description": "",
            "priority": "low",
            "assigneeId": None,
            "dueDate": None,
            "labels": [],
            "columnId": "column-1",
        },
        headers=demo,
    )
    assert res.status_code == 422


def test_get_card(client, demo):
    res = client.get("/api/cards/NST-141", headers=demo)
    assert res.status_code == 200
    body = res.json()
    assert body["blocking"] == ["NST-147"]
    assert body["blockedBy"] == []
    assert body["commentCount"] == 2


def test_get_card_forbidden(client, rowan):
    assert client.get("/api/cards/FLD-24", headers=rowan).status_code == 404
    assert client.get("/api/cards/UNKNOWN-1", headers=rowan).status_code == 404


def test_patch_card(client, demo):
    before = client.get("/api/cards/NST-142", headers=demo).json()["updatedAt"]
    res = client.patch(
        "/api/cards/NST-142",
        json={"title": "Renamed", "priority": "urgent"},
        headers=demo,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["title"] == "Renamed"
    assert body["priority"] == "urgent"
    assert body["updatedAt"] >= before


def test_patch_card_assignee_must_be_member(client, demo):
    res = client.patch(
        "/api/cards/FLD-24",
        json={"assigneeId": "u5"},
        headers=demo,
    )
    assert res.status_code == 422


def test_patch_card_empty_body(client, demo):
    res = client.patch("/api/cards/NST-142", json={}, headers=demo)
    assert res.status_code == 422


def test_move_card(client, demo):
    res = client.post(
        "/api/cards/NST-142/move",
        json={"columnId": "column-2", "position": None},
        headers=demo,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["columnId"] == "column-2"
    assert body["position"] == 2

    board = client.get("/api/projects/p1/board", headers=demo).json()
    c2 = [c for c in board["cards"] if c["columnId"] == "column-2"]
    assert [c["id"] for c in c2] == ["NST-141", "NST-147", "NST-142"]


def test_move_card_with_position(client, demo):
    res = client.post(
        "/api/cards/NST-142/move",
        json={"columnId": "column-2", "position": 0},
        headers=demo,
    )
    assert res.status_code == 200
    board = client.get("/api/projects/p1/board", headers=demo).json()
    c2 = [c for c in board["cards"] if c["columnId"] == "column-2"]
    assert [c["id"] for c in c2] == ["NST-142", "NST-141", "NST-147"]


def test_move_card_wrong_project_column(client, demo):
    res = client.post(
        "/api/cards/NST-142/move",
        json={"columnId": "column-5"},
        headers=demo,
    )
    assert res.status_code == 404


def test_delete_card_without_relationships(client, demo):
    res = client.delete("/api/cards/NST-142", headers=demo)
    assert res.status_code == 204
    assert client.get("/api/cards/NST-142", headers=demo).status_code == 404


def test_delete_card_with_relationships_requires_resolution(client, demo):
    res = client.delete("/api/cards/NST-141", headers=demo)
    assert res.status_code == 409


def test_delete_card_reconnect(client, demo):
    res = client.request(
        "DELETE",
        "/api/cards/NST-141",
        json={"resolveRelationships": "reconnect", "reconnectToCardId": "NST-138"},
        headers=demo,
    )
    assert res.status_code == 204
    assert client.get("/api/cards/NST-141", headers=demo).status_code == 404

    target = client.get("/api/cards/NST-147", headers=demo).json()
    assert target["blockedBy"] == ["NST-138"]
    source = client.get("/api/cards/NST-138", headers=demo).json()
    assert source["blocking"] == ["NST-147"]


def test_delete_card_reconnect_requires_target(client, demo):
    res = client.request(
        "DELETE",
        "/api/cards/NST-141",
        json={"resolveRelationships": "reconnect"},
        headers=demo,
    )
    assert res.status_code == 409

    res = client.request(
        "DELETE",
        "/api/cards/NST-141",
        json={"resolveRelationships": "reconnect", "reconnectToCardId": "FLD-24"},
        headers=demo,
    )
    assert res.status_code == 409


def test_delete_card_delete_relationships(client, demo):
    res = client.request(
        "DELETE",
        "/api/cards/NST-141",
        json={"resolveRelationships": "delete"},
        headers=demo,
    )
    assert res.status_code == 204
    target = client.get("/api/cards/NST-147", headers=demo).json()
    assert target["blockedBy"] == []