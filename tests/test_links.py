import pytest
from sqlmodel import SQLModel, create_engine

import main


@pytest.fixture
def client(tmp_path, monkeypatch):
    database_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{database_path}")

    SQLModel.metadata.create_all(engine)

    monkeypatch.setattr(main, "get_engine", lambda: engine)
    monkeypatch.setenv("BASE_URL", "http://localhost:8080")

    main.app.config["TESTING"] = True

    with main.app.test_client() as test_client:
        yield test_client

    engine.dispose()

def test_get_empty_links(client):
    response = client.get("/api/links")

    assert response.status_code == 200
    assert response.json == []

def test_create_link(client):
    data = {
        "original_url": "https://example.com/long-url",
        "short_name": "exmpl",
    }

    response = client.post("/api/links", json=data)

    assert response.status_code == 201
    assert response.json["id"] is not None
    assert response.json["original_url"] == data["original_url"]
    assert response.json["short_name"] == data["short_name"]
    assert response.json["short_url"] == "http://localhost:8080/r/exmpl"

    links_response = client.get("/api/links")

    assert links_response.status_code == 200
    assert len(links_response.json) == 1

def test_create_link_validation(client):
    data = {
        "original_url": "https://example.com",
        "short_name": "",
    }

    response = client.post("/api/links", json=data)

    assert response.status_code == 422
    assert "detail" in response.json

    links_response = client.get("/api/links")

    assert links_response.json == []

def test_duplicate_short_name(client):
    data = {
        "original_url": "https://example.com",
        "short_name": "exmpl",
    }

    first_response = client.post("/api/links", json=data)

    assert first_response.status_code == 201

    second_response = client.post("/api/links", json=data)

    assert second_response.status_code == 422
    assert "detail" in second_response.json

    links_response = client.get("/api/links")

    assert len(links_response.json) == 1

def create_test_link(client, short_name="exmpl"):
    response = client.post(
        "/api/links",
        json={
            "original_url": "https://example.com/long-url",
            "short_name": short_name,
        },
    )

    assert response.status_code == 201

    return response.json["id"]

def test_get_link(client):
    link_id = create_test_link(client)

    response = client.get(f"/api/links/{link_id}")

    assert response.status_code == 200
    assert response.json["id"] == link_id
    assert response.json["short_name"] == "exmpl"

    missing_response = client.get("/api/links/999999")

    assert missing_response.status_code == 404
    assert "detail" in missing_response.json

def test_update_link(client):
    link_id = create_test_link(client)

    new_data = {
        "original_url": "https://example.com/updated",
        "short_name": "updated",
    }

    response = client.put(
        f"/api/links/{link_id}",
        json=new_data,
    )

    assert response.status_code == 200
    assert response.json["original_url"] == new_data["original_url"]
    assert response.json["short_name"] == "updated"

    invalid_response = client.put(
        f"/api/links/{link_id}",
        json={
            "original_url": "",
            "short_name": "invalid",
        },
    )

    assert invalid_response.status_code == 422

    saved_response = client.get(f"/api/links/{link_id}")

    assert saved_response.json["short_name"] == "updated"
    assert saved_response.json["original_url"] == new_data["original_url"]

    missing_response = client.put(
        "/api/links/999999",
        json=new_data,
    )

    assert missing_response.status_code == 404
    assert "detail" in missing_response.json

def test_update_duplicate_short_name(client):
    create_test_link(client, "first")
    second_id = create_test_link(client, "second")

    response = client.put(
        f"/api/links/{second_id}",
        json={
            "original_url": "https://example.com",
            "short_name": "first",
        },
    )

    assert response.status_code == 422
    assert "detail" in response.json

    saved_response = client.get(f"/api/links/{second_id}")

    assert saved_response.json["short_name"] == "second"

def test_delete_link(client):
    link_id = create_test_link(client)

    response = client.delete(f"/api/links/{link_id}")

    assert response.status_code == 204
    assert response.data == b""

    get_response = client.get(f"/api/links/{link_id}")

    assert get_response.status_code == 404

    delete_response = client.delete(f"/api/links/{link_id}")

    assert delete_response.status_code == 404
    assert "detail" in delete_response.json

def test_redirect_link(client):
    create_test_link(client, "go")

    response = client.get(
        "/r/go",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"] == (
        "https://example.com/long-url"
    )

    missing_response = client.get("/r/unknown")

    assert missing_response.status_code == 404
    assert "detail" in missing_response.json