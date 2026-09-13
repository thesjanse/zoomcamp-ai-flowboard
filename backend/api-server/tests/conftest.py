import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.store import Store

PASSWORD = "password123"


@pytest.fixture
def store() -> Store:
    return Store(seed=True)


@pytest.fixture
def client(store: Store) -> TestClient:
    return TestClient(create_app(store))


@pytest.fixture
def login(client: TestClient):
    def _login(email: str = "demo@demo.dev", password: str = PASSWORD):
        res = client.post(
            "/api/auth/login", json={"email": email, "password": password}
        )
        assert res.status_code == 200, res.text
        return {"Authorization": f"Bearer {res.json()['token']}"}

    return _login


@pytest.fixture
def register(client: TestClient):
    def _register(name: str, email: str, password: str = PASSWORD):
        res = client.post(
            "/api/auth/register",
            json={"name": name, "email": email, "password": password},
        )
        assert res.status_code == 201, res.text
        return {"Authorization": f"Bearer {res.json()['token']}"}

    return _register


@pytest.fixture
def demo(login):
    return login("demo@demo.dev")


@pytest.fixture
def mara(login):
    return login("mara@demo.dev")


@pytest.fixture
def theo(login):
    return login("theo@demo.dev")


@pytest.fixture
def inez(login):
    return login("inez@demo.dev")


@pytest.fixture
def rowan(login):
    return login("rowan@demo.dev")