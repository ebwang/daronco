# backend/tests/test_users.py
"""Tests for the /api/users endpoints (CRUD, validation and cascade to hosts)."""


def test_post_creates_user_with_201_status(client, user_payload):
    response = client.post("/api/users", json=user_payload)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["created_at"]
    for field, value in user_payload.items():
        assert body[field] == value
    # UserSimpleResponse does not expose the host list
    assert "hosts" not in body


def test_post_persists_user(client, create_user):
    user = create_user()

    response = client.get(f"/api/users/{user['id']}")

    assert response.status_code == 200
    assert response.json()["username"] == "jdoe"
    assert response.json()["hosts"] == []


def test_post_duplicated_username_returns_400(client, user_payload, create_user):
    create_user()

    response = client.post("/api/users", json=user_payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "A user with the username 'jdoe' already exists."


def test_post_without_required_field_returns_422(client, user_payload):
    user_payload.pop("username")

    response = client.post("/api/users", json=user_payload)

    assert response.status_code == 422
    assert any(error["loc"][-1] == "username" for error in response.json()["detail"])


def test_get_returns_empty_list_when_there_is_no_data(client):
    response = client.get("/api/users")

    assert response.status_code == 200
    assert response.json() == []


def test_get_returns_ordered_list_with_nested_hosts(client, create_user, create_host):
    first_user = create_user(username="asmith")
    second_user = create_user(username="bjones")
    create_host(hostname="host-second", user_id=second_user["id"])

    body = client.get("/api/users").json()

    assert [user["id"] for user in body] == [first_user["id"], second_user["id"]]
    assert body[0]["hosts"] == []
    assert [host["hostname"] for host in body[1]["hosts"]] == ["host-second"]
    assert body[1]["hosts"][0]["user_id"] == second_user["id"]


def test_get_unknown_user_returns_404(client):
    response = client.get("/api/users/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_get_user_with_invalid_id_returns_422(client):
    assert client.get("/api/users/abc").status_code == 422


def test_delete_removes_user(client, create_user):
    user = create_user()

    response = client.delete(f"/api/users/{user['id']}")

    assert response.status_code == 200
    assert response.json() == {"message": "User deleted successfully", "id": user["id"]}
    assert client.get(f"/api/users/{user['id']}").status_code == 404
    assert client.get("/api/users").json() == []


def test_delete_unknown_user_returns_404(client):
    response = client.delete("/api/users/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_delete_user_removes_hosts_in_cascade(client, create_user, create_host):
    user = create_user()
    create_host(user_id=user["id"])
    assert len(client.get("/api/hosts").json()) == 1

    client.delete(f"/api/users/{user['id']}")

    assert client.get("/api/hosts").json() == []
