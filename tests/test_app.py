def test_health_is_open(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "UP"


def test_internal_requires_token(client):
    assert client.get("/internal/ping").status_code == 401
    assert client.get("/internal/ping", headers={"X-Internal-Token": "wrong"}).status_code == 401


def test_internal_with_token(client):
    response = client.get("/internal/ping", headers={"X-Internal-Token": "test-token"})
    assert response.status_code == 200


def test_api_docs_are_closed(client):
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404
