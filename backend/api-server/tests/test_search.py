def test_search_project(client, demo):
    res = client.get("/api/search", params={"q": "North"}, headers=demo)
    assert res.status_code == 200
    assert res.json()[0] == {
        "type": "project",
        "id": "p1",
        "title": "Northstar",
        "subtitle": "NST project",
    }


def test_search_card(client, demo):
    res = client.get("/api/search", params={"q": "NST-142"}, headers=demo)
    assert res.status_code == 200
    result = res.json()[0]
    assert result["type"] == "card"
    assert result["id"] == "NST-142"


def test_search_archived_project(client, demo):
    res = client.get("/api/search", params={"q": "orbit"}, headers=demo)
    results = [r for r in res.json() if r["type"] == "project"]
    assert results[0]["subtitle"] == "Archived project"


def test_search_empty_query(client, demo):
    assert client.get("/api/search", params={"q": " "}, headers=demo).status_code == 422


def test_search_requires_auth(client):
    assert client.get("/api/search", params={"q": "north"}).status_code == 401


def test_search_only_own_projects(client, rowan):
    res = client.get("/api/search", params={"q": "friction"}, headers=rowan)
    assert res.status_code == 200
    assert res.json() == []


def test_search_result_shape(client, demo):
    res = client.get("/api/search", params={"q": "field"}, headers=demo)
    for result in res.json():
        assert set(result) == {"type", "id", "title", "subtitle"}