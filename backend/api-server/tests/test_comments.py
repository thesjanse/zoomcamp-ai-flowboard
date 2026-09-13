def test_list_comments(client, demo):
    res = client.get("/api/cards/NST-141/comments", headers=demo)
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 2
    assert body[0]["authorId"] == "u2"
    assert body[1]["authorId"] == "u3"


def test_list_comments_empty(client, demo):
    assert client.get("/api/cards/NST-142/comments", headers=demo).json() == []


def test_list_comments_forbidden(client, rowan):
    assert client.get("/api/cards/FLD-24/comments", headers=rowan).status_code == 404


def test_add_comment(client, inez):
    res = client.post(
        "/api/cards/NST-141/comments",
        json={"body": "Great work"},
        headers=inez,
    )
    assert res.status_code == 201
    body = res.json()
    assert body["authorId"] == "u4"
    assert body["body"] == "Great work"
    assert body["createdAt"] is not None

    board = client.get("/api/projects/p1/board", headers=inez).json()
    card = next(c for c in board["cards"] if c["id"] == "NST-141")
    assert card["commentCount"] == 3


def test_add_comment_to_inaccessible_card(client, rowan):
    res = client.post(
        "/api/cards/FLD-24/comments",
        json={"body": "No"},
        headers=rowan,
    )
    assert res.status_code == 404


def test_add_comment_empty_body(client, demo):
    res = client.post(
        "/api/cards/NST-141/comments",
        json={"body": ""},
        headers=demo,
    )
    assert res.status_code == 422


def test_edit_own_comment(client, mara):
    res = client.patch(
        "/api/comments/cmt-1",
        json={"body": "Updated"},
        headers=mara,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["body"] == "Updated"
    assert body["editedAt"] is not None


def test_edit_others_comment_forbidden(client, theo):
    res = client.patch(
        "/api/comments/cmt-1",
        json={"body": "No"},
        headers=theo,
    )
    assert res.status_code == 403


def test_delete_own_comment(client, theo):
    res = client.delete("/api/comments/cmt-2", headers=theo)
    assert res.status_code == 204
    remaining = client.get("/api/cards/NST-141/comments", headers=theo).json()
    assert [c["id"] for c in remaining] == ["cmt-1"]


def test_delete_others_comment_as_member_forbidden(client, inez):
    res = client.delete("/api/comments/cmt-1", headers=inez)
    assert res.status_code == 403


def test_delete_others_comment_as_admin(client, mara):
    res = client.delete("/api/comments/cmt-1", headers=mara)
    assert res.status_code == 204