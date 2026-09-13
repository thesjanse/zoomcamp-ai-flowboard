def _members(client, headers, project_id="p1"):
    res = client.get(f"/api/projects/{project_id}/members", headers=headers)
    assert res.status_code == 200
    return res.json()


def test_list_members(client, demo):
    members = _members(client, demo)
    assert len(members) == 5
    assert members[0]["id"] == "u1"
    assert members[0]["role"] == "admin"
    assert members[1]["role"] == "admin"
    assert all(m["role"] == "member" for m in members[2:])


def test_list_members_forbidden(client, rowan):
    assert client.get("/api/projects/p2/members", headers=rowan).status_code == 404


def test_promote_member(client, demo):
    res = client.patch(
        "/api/projects/p1/members/u4", json={"role": "admin"}, headers=demo
    )
    assert res.status_code == 200
    assert res.json()["role"] == "admin"


def test_promote_by_member_forbidden(client, theo):
    res = client.patch(
        "/api/projects/p1/members/u4", json={"role": "admin"}, headers=theo
    )
    assert res.status_code == 403


def test_demote_admin_by_creator(client, demo):
    client.patch("/api/projects/p1/members/u5", json={"role": "admin"}, headers=demo)
    res = client.patch(
        "/api/projects/p1/members/u5", json={"role": "member"}, headers=demo
    )
    assert res.status_code == 200
    assert res.json()["role"] == "member"


def test_demote_creator_forbidden(client, demo):
    res = client.patch(
        "/api/projects/p1/members/u1", json={"role": "member"}, headers=demo
    )
    assert res.status_code == 403


def test_demote_admin_by_non_creator_forbidden(client, demo, mara):
    client.patch("/api/projects/p1/members/u5", json={"role": "admin"}, headers=demo)
    res = client.patch(
        "/api/projects/p1/members/u5", json={"role": "member"}, headers=mara
    )
    assert res.status_code == 403


def test_remove_member(client, demo):
    res = client.delete("/api/projects/p1/members/u5", headers=demo)
    assert res.status_code == 204
    assert len(_members(client, demo)) == 4


def test_remove_admin_by_non_creator_forbidden(client, demo, mara):
    client.patch("/api/projects/p1/members/u5", json={"role": "admin"}, headers=demo)
    res = client.delete("/api/projects/p1/members/u5", headers=mara)
    assert res.status_code == 403


def test_remove_creator_forbidden(client, mara):
    res = client.delete("/api/projects/p1/members/u1", headers=mara)
    assert res.status_code == 403


def test_remove_unknown_member(client, demo):
    res = client.delete("/api/projects/p1/members/nope", headers=demo)
    assert res.status_code == 404


def test_creator_deletes_self_leave_rules(client, demo):
    res = client.delete("/api/projects/p1/members/u1", headers=demo)
    assert res.status_code == 409


def test_leave_project_as_member(client, demo, inez):
    before = client.get("/api/projects/p1/members", headers=demo).json()
    assert len(before) == 5
    res = client.post("/api/projects/p1/leave", headers=inez)
    assert res.status_code == 204
    after = client.get("/api/projects/p1/members", headers=demo).json()
    assert len(after) == 4
    assert client.get("/api/projects/p1/members", headers=inez).status_code == 404


def test_leave_creator_with_others_forbidden(client, demo):
    res = client.post("/api/projects/p1/leave", headers=demo)
    assert res.status_code == 409


def test_leave_creator_archives_project(client, store, register):
    headers = register("Solo Admin", "solo@demo.dev")
    created = client.post(
        "/api/projects", json={"name": "Solo project", "description": ""}, headers=headers
    ).json()
    pid = created["id"]
    res = client.post(f"/api/projects/{pid}/leave", headers=headers)
    assert res.status_code == 204
    project = store.projects[pid]
    assert project["archived"] is True
    assert client.get(f"/api/projects/{pid}", headers=headers).status_code == 404


def test_transfer_admin(client, demo, mara):
    res = client.post(
        "/api/projects/p1/transfer", json={"adminId": "u2"}, headers=demo
    )
    assert res.status_code == 200
    assert res.json()["creatorId"] == "u2"
    roles = {m["id"]: m["role"] for m in res.json()["members"]}
    assert roles["u1"] == "member"
    assert roles["u2"] == "admin"

    # old creator is no longer creator/admin
    assert client.post("/api/projects/p1/archive", headers=demo).status_code == 403
    assert client.post("/api/projects/p1/archive", headers=mara).status_code == 200


def test_transfer_requires_creator(client, mara):
    res = client.post(
        "/api/projects/p1/transfer", json={"adminId": "u2"}, headers=mara
    )
    assert res.status_code == 403


def test_transfer_to_non_admin(client, demo):
    res = client.post(
        "/api/projects/p1/transfer", json={"adminId": "u4"}, headers=demo
    )
    assert res.status_code == 404