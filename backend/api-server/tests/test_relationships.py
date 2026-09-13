def test_list_relationships(client, demo):
    res = client.get("/api/cards/NST-141/relationships", headers=demo)
    assert res.status_code == 200
    body = res.json()
    assert len(body["blockedBy"]) == 0
    assert len(body["blocking"]) == 1
    assert body["blocking"][0]["targetCardId"] == "NST-147"


def test_list_relationships_blocking(client, demo):
    res = client.get("/api/cards/NST-147/relationships", headers=demo)
    assert res.status_code == 200
    body = res.json()
    assert len(body["blocking"]) == 0
    assert len(body["blockedBy"]) == 1
    assert body["blockedBy"][0]["sourceCardId"] == "NST-141"


def test_list_relationships_forbidden(client, rowan):
    assert client.get("/api/cards/FLD-24/relationships", headers=rowan).status_code == 404


def test_create_relationship(client, demo):
    res = client.post(
        "/api/cards/NST-142/relationships",
        json={"targetCardId": "NST-138"},
        headers=demo,
    )
    assert res.status_code == 201
    body = res.json()
    assert body["sourceCardId"] == "NST-142"
    assert body["targetCardId"] == "NST-138"
    assert body["type"] == "blocks"


def test_create_relationship_self(client, demo):
    res = client.post(
        "/api/cards/NST-142/relationships",
        json={"targetCardId": "NST-142"},
        headers=demo,
    )
    assert res.status_code == 409


def test_create_relationship_cross_project(client, demo):
    res = client.post(
        "/api/cards/NST-142/relationships",
        json={"targetCardId": "FLD-24"},
        headers=demo,
    )
    assert res.status_code == 409


def test_create_relationship_duplicate(client, demo):
    res = client.post(
        "/api/cards/NST-141/relationships",
        json={"targetCardId": "NST-147"},
        headers=demo,
    )
    assert res.status_code == 409


def test_delete_relationship(client, demo):
    res = client.delete(
        "/api/cards/NST-141/relationships/NST-147",
        headers=demo,
    )
    assert res.status_code == 204
    rels = client.get("/api/cards/NST-141/relationships", headers=demo).json()
    assert len(rels["blocking"]) == 0
    assert len(rels["blockedBy"]) == 0