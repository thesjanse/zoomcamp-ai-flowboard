def test_create_invite(client, demo):
    res = client.post("/api/projects/p1/invites", json={}, headers=demo)
    assert res.status_code == 201
    body = res.json()
    assert "token" in body
    assert "expiresAt" in body


def test_create_invite_as_member_forbidden(client, inez):
    res = client.post("/api/projects/p1/invites", headers=inez)
    assert res.status_code == 403


def test_accept_invite_adds_member(client, demo, register):
    token = client.post("/api/projects/p1/invites", headers=demo).json()["token"]
    headers = register("Newbie", "newbie@demo.dev")

    res = client.post(f"/api/invites/{token}/accept", headers=headers)
    assert res.status_code == 200
    assert res.json()["id"] == "p1"

    projects = client.get("/api/projects", headers=headers).json()
    assert [p["name"] for p in projects] == ["Northstar"]


def test_accept_revoked_invite(client, demo, register):
    first = client.post("/api/projects/p1/invites", headers=demo).json()["token"]
    second = client.post("/api/projects/p1/invites", headers=demo).json()["token"]

    headers = register("Newbie", "newbie@demo.dev")
    assert client.post(f"/api/invites/{first}/accept", headers=headers).status_code == 410
    assert client.post(f"/api/invites/{second}/accept", headers=headers).status_code == 200


def test_accept_invalid_token(client, demo, register):
    headers = register("Newbie", "newbie@demo.dev")
    res = client.post("/api/invites/not-a-real-token/accept", headers=headers)
    assert res.status_code == 410


def test_member_accepting_invite_without_duplicate(client, demo, inez):
    token = client.post("/api/projects/p1/invites", headers=demo).json()["token"]
    res = client.post(f"/api/invites/{token}/accept", headers=inez)
    assert res.status_code == 200
    members = client.get("/api/projects/p1/members", headers=demo).json()
    assert len([m for m in members if m["id"] == "u4"]) == 1


def test_accept_invite_membership_scoped(client, demo, register):
    token = client.post("/api/projects/p1/invites", headers=demo).json()["token"]
    headers = register("Newbie", "newbie@demo.dev")
    client.post(f"/api/invites/{token}/accept", headers=headers)
    # member of p1 only, not p2
    assert client.get("/api/projects/p2", headers=headers).status_code == 404