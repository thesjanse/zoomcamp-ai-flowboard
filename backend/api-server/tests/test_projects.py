def test_list_projects_includes_archived(client, demo):
    res = client.get("/api/projects", headers=demo)
    assert res.status_code == 200
    assert [p["name"] for p in res.json()] == [
        "Northstar",
        "Field notes",
        "Orbit / archive",
    ]


def test_list_projects_exclude_archived(client, demo):
    res = client.get("/api/projects?includeArchived=false", headers=demo)
    names = [p["name"] for p in res.json()]
    assert names == ["Northstar", "Field notes"]
    assert "Orbit / archive" not in names


def test_list_projects_requires_auth(client):
    assert client.get("/api/projects").status_code == 401


def test_create_project(client, demo):
    res = client.post(
        "/api/projects",
        json={
            "name": "Test Project Alpha",
            "description": "A test",
            "color": "#ff0000",
        },
        headers=demo,
    )
    assert res.status_code == 201
    body = res.json()
    assert body["id"] == "project-4"
    assert body["key"] == "TPA"
    assert body["status"] == "active"
    assert body["archived"] is False
    assert body["creatorId"] == "u1"
    assert [m["role"] for m in body["members"]] == ["admin"]
    assert [c["name"] for c in client.get(f"/api/projects/{body['id']}/columns", headers=demo).json()] == [
        "To Do",
        "In Progress",
        "Done",
    ]


def test_create_project_invalid(client, demo):
    res = client.post("/api/projects", json={"name": "", "description": ""}, headers=demo)
    assert res.status_code == 422


def test_get_project(client, demo):
    res = client.get("/api/projects/p1", headers=demo)
    assert res.status_code == 200
    assert res.json()["name"] == "Northstar"
    assert len(res.json()["members"]) == 5


def test_get_project_forbidden(client, rowan):
    assert client.get("/api/projects/p2", headers=rowan).status_code == 404
    assert client.get("/api/projects/nope", headers=rowan).status_code == 404


def test_update_project(client, demo):
    res = client.patch(
        "/api/projects/p1",
        json={"name": "Renamed", "description": "New desc", "color": "#112233"},
        headers=demo,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["name"] == "Renamed"
    assert body["description"] == "New desc"
    assert body["color"] == "#112233"
    assert body["icon"] == "R"


def test_update_project_as_member_forbidden(client, inez):
    res = client.patch(
        "/api/projects/p1", json={"name": "Nope"}, headers=inez
    )
    assert res.status_code == 403


def test_update_project_empty_body(client, demo):
    res = client.patch("/api/projects/p1", json={}, headers=demo)
    assert res.status_code == 422


def test_archive_and_restore(client, demo):
    archived = client.post("/api/projects/p1/archive", headers=demo)
    assert archived.status_code == 200
    assert archived.json()["archived"] is True

    res = client.get("/api/projects?includeArchived=false", headers=demo)
    assert "Northstar" not in [p["name"] for p in res.json()]

    restored = client.post("/api/projects/p1/restore", headers=demo)
    assert restored.status_code == 200
    assert restored.json()["archived"] is False


def test_archive_as_member_forbidden(client, inez):
    assert client.post("/api/projects/p1/archive", headers=inez).status_code == 403


def test_delete_project_requires_archive(client, demo):
    res = client.delete("/api/projects/p1", headers=demo)
    assert res.status_code == 409


def test_delete_project(client, demo):
    client.post("/api/projects/p1/archive", headers=demo)
    res = client.delete("/api/projects/p1", headers=demo)
    assert res.status_code == 204
    assert client.get("/api/projects/p1", headers=demo).status_code == 404