def _columns_for(client, headers, project_id="p1"):
    res = client.get(f"/api/projects/{project_id}/columns", headers=headers)
    assert res.status_code == 200
    return res.json()


def test_list_columns(client, demo):
    cols = _columns_for(client, demo)
    assert len(cols) == 4
    assert [c["position"] for c in cols] == [0, 1, 2, 3]
    assert [c["name"] for c in cols] == ["Backlog", "In progress", "Review", "Shipped"]


def test_list_columns_forbidden(client, rowan):
    assert client.get("/api/projects/p2/columns", headers=rowan).status_code == 404


def test_create_column(client, demo):
    res = client.post(
        "/api/projects/p1/columns", json={"name": "Ideas"}, headers=demo
    )
    assert res.status_code == 201
    body = res.json()
    assert body["name"] == "Ideas"
    assert body["position"] == 4
    assert len(_columns_for(client, demo)) == 5


def test_create_column_as_member_forbidden(client, inez):
    assert (
        client.post(
            "/api/projects/p1/columns", json={"name": "Ideas"}, headers=inez
        ).status_code
        == 403
    )


def test_column_limit_of_7(client, demo):
    for i in range(3):
        res = client.post(
            "/api/projects/p1/columns", json={"name": f"Col {i}"}, headers=demo
        )
        assert res.status_code == 201
    assert len(_columns_for(client, demo)) == 7
    res = client.post(
        "/api/projects/p1/columns", json={"name": "Too many"}, headers=demo
    )
    assert res.status_code == 409


def test_update_column_name(client, demo):
    res = client.patch(
        "/api/columns/column-1", json={"name": "Backlog!"}, headers=demo
    )
    assert res.status_code == 200
    assert res.json()["name"] == "Backlog!"


def test_update_column_position(client, demo):
    res = client.patch(
        "/api/columns/column-1", json={"position": 3}, headers=demo
    )
    assert res.status_code == 200
    assert [c["id"] for c in _columns_for(client, demo)] == [
        "column-2",
        "column-3",
        "column-4",
        "column-1",
    ]


def test_update_column_as_member_forbidden(client, inez):
    assert (
        client.patch("/api/columns/column-1", json={"name": "No"}, headers=inez).status_code
        == 403
    )


def test_delete_empty_column(client, demo):
    created = client.post(
        "/api/projects/p1/columns", json={"name": "Spare"}, headers=demo
    ).json()
    res = client.delete(f"/api/columns/{created['id']}", headers=demo)
    assert res.status_code == 204
    assert [c["id"] for c in _columns_for(client, demo)] == [
        "column-1",
        "column-2",
        "column-3",
        "column-4",
    ]


def test_delete_column_with_cards_requires_destination(client, demo):
    res = client.delete("/api/columns/column-2", headers=demo)
    assert res.status_code == 409


def test_delete_column_with_move_cards_to(client, demo):
    res = client.delete(
        "/api/columns/column-2", params={"moveCardsTo": "column-1"}, headers=demo
    )
    assert res.status_code == 204

    board = client.get("/api/projects/p1/board", headers=demo).json()
    in_backlog = [c["id"] for c in board["cards"] if c["columnId"] == "column-1"]
    assert {"NST-141", "NST-147"} <= set(in_backlog)


def test_delete_column_invalid_destination(client, demo):
    res = client.delete(
        "/api/columns/column-2", params={"moveCardsTo": "column-5"}, headers=demo
    )
    assert res.status_code == 409


def test_delete_last_column_forbidden(client, demo):
    created = client.post(
        "/api/projects",
        json={"name": "Solo", "description": ""},
        headers=demo,
    ).json()
    pid = created["id"]
    headers = demo
    for _ in range(2):
        col = _columns_for(client, headers, pid)[0]
        assert client.delete(f"/api/columns/{col['id']}", headers=headers).status_code == 204
    last = _columns_for(client, headers, pid)[0]
    assert client.delete(f"/api/columns/{last['id']}", headers=headers).status_code == 409


def test_unknown_column(client, demo):
    assert client.delete("/api/columns/nope", headers=demo).status_code == 404