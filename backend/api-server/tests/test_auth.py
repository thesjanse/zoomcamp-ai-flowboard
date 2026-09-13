def test_register(client):
    res = client.post(
        "/api/auth/register",
        json={"name": "New Person", "email": "new@demo.dev", "password": "password123"},
    )
    assert res.status_code == 201
    body = res.json()
    assert set(body) == {"token", "user"}
    assert body["user"]["email"] == "new@demo.dev"
    assert body["user"]["name"] == "New Person"
    assert "passwordHash" not in body["user"]


def test_register_duplicate_email(client):
    res = client.post(
        "/api/auth/register",
        json={"name": "Dup", "email": "demo@demo.dev", "password": "password123"},
    )
    assert res.status_code == 409


def test_register_validation(client):
    bad = [
        {"name": "", "email": "a@a.dev", "password": "password123"},
        {"name": "X", "email": "not-an-email", "password": "password123"},
        {"name": "X", "email": "a@a.dev", "password": "short"},
    ]
    for payload in bad:
        res = client.post("/api/auth/register", json=payload)
        assert res.status_code == 422, payload


def test_register_forbids_extra_fields(client):
    res = client.post(
        "/api/auth/register",
        json={"name": "X", "email": "a@a.dev", "password": "password123", "role": "admin"},
    )
    assert res.status_code == 422


def test_login_and_me(client, demo):
    res = client.get("/api/me", headers=demo)
    assert res.status_code == 200
    assert res.json()["email"] == "demo@demo.dev"


def test_login_wrong_password(client):
    res = client.post(
        "/api/auth/login", json={"email": "demo@demo.dev", "password": "wrong"}
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid credentials"


def test_login_unknown_email(client):
    res = client.post(
        "/api/auth/login", json={"email": "ghost@demo.dev", "password": "password123"}
    )
    assert res.status_code == 401


def test_me_requires_token(client):
    res = client.get("/api/me")
    assert res.status_code == 401


def test_me_rejects_bad_token(client):
    res = client.get("/api/me", headers={"Authorization": "Bearer nope"})
    assert res.status_code == 401


def test_logout_revokes_token(client, demo):
    res = client.post("/api/auth/logout", headers=demo)
    assert res.status_code == 204
    res = client.get("/api/me", headers=demo)
    assert res.status_code == 401


def test_change_email(client, demo):
    res = client.patch("/api/auth/email", json={"email": "new@demo.dev"}, headers=demo)
    assert res.status_code == 200
    assert res.json()["email"] == "new@demo.dev"

    old = client.post(
        "/api/auth/login", json={"email": "demo@demo.dev", "password": "password123"}
    )
    assert old.status_code == 401
    new = client.post(
        "/api/auth/login", json={"email": "new@demo.dev", "password": "password123"}
    )
    assert new.status_code == 200


def test_change_email_taken(client, demo):
    res = client.patch("/api/auth/email", json={"email": "mara@demo.dev"}, headers=demo)
    assert res.status_code == 409


def test_change_password(client, demo):
    res = client.patch(
        "/api/auth/password",
        json={"currentPassword": "password123", "newPassword": "newpassword99"},
        headers=demo,
    )
    assert res.status_code == 204

    old = client.post(
        "/api/auth/login", json={"email": "demo@demo.dev", "password": "password123"}
    )
    assert old.status_code == 401
    new = client.post(
        "/api/auth/login",
        json={"email": "demo@demo.dev", "password": "newpassword99"},
    )
    assert new.status_code == 200


def test_change_password_wrong_current(client, demo):
    res = client.patch(
        "/api/auth/password",
        json={"currentPassword": "wrong", "newPassword": "newpassword99"},
        headers=demo,
    )
    assert res.status_code == 401


def test_delete_account_blocked_while_admin(client, demo):
    res = client.delete("/api/auth/account", headers=demo)
    assert res.status_code == 409


def test_delete_account_member_only(client, register):
    headers = register("Solo", "solo@demo.dev")
    created = client.post(
        "/api/projects",
        json={"name": "Solo project", "description": ""},
        headers=headers,
    )
    project_id = created.json()["id"]
    left = client.post(f"/api/projects/{project_id}/leave", headers=headers)
    assert left.status_code == 204

    res = client.delete("/api/auth/account", headers=headers)
    assert res.status_code == 204
    assert client.get("/api/me", headers=headers).status_code == 401