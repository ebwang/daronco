# backend/tests/test_hosts.py
"""Tests for the /api/hosts endpoints (CRUD, user association and validation)."""


def test_get_hosts_returns_empty_list_when_there_is_no_data(client):
    response = client.get("/api/hosts")

    assert response.status_code == 200
    assert response.json() == []


def test_post_host_without_user(client, host_payload):
    response = client.post("/api/hosts", json=host_payload)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["user_id"] is None
    for field, value in host_payload.items():
        assert body[field] == value


def test_post_host_with_unknown_user_returns_404(client, host_payload):
    host_payload["user_id"] = 999

    response = client.post("/api/hosts", json=host_payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "User with id=999 does not exist."


def test_post_host_linked_to_user(client, host_payload, create_user):
    user = create_user()
    host_payload["user_id"] = user["id"]

    response = client.post("/api/hosts", json=host_payload)

    assert response.status_code == 201
    assert response.json()["user_id"] == user["id"]
    hosts = client.get(f"/api/users/{user['id']}").json()["hosts"]
    assert [host["hostname"] for host in hosts] == [host_payload["hostname"]]


def test_post_host_without_required_field_returns_422(client, host_payload):
    host_payload.pop("ips")

    response = client.post("/api/hosts", json=host_payload)

    assert response.status_code == 422
    assert any(error["loc"][-1] == "ips" for error in response.json()["detail"])


def test_post_host_with_invalid_cpu_count_returns_422(client, host_payload):
    host_payload["cpu_count"] = "two"

    response = client.post("/api/hosts", json=host_payload)

    assert response.status_code == 422
    assert any(error["loc"][-1] == "cpu_count" for error in response.json()["detail"])


def test_get_hosts_ordered_by_id(client, create_host):
    first_host = create_host(hostname="host-a")
    second_host = create_host(hostname="host-b")

    body = client.get("/api/hosts").json()

    assert [host["id"] for host in body] == [first_host["id"], second_host["id"]]
    assert [host["hostname"] for host in body] == ["host-a", "host-b"]


def test_delete_host(client, create_host):
    host = create_host()

    response = client.delete(f"/api/hosts/{host['id']}")

    assert response.status_code == 200
    assert response.json() == {"message": "Host deleted successfully", "id": host["id"]}
    assert client.get("/api/hosts").json() == []


def test_delete_unknown_host_returns_404(client):
    response = client.delete("/api/hosts/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Host not found"


def test_delete_host_does_not_affect_the_user(client, create_user, create_host):
    user = create_user()
    host = create_host(user_id=user["id"])

    client.delete(f"/api/hosts/{host['id']}")

    response = client.get(f"/api/users/{user['id']}")
    assert response.status_code == 200
    assert response.json()["hosts"] == []
