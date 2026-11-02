from fastapi.testclient import TestClient

from ai.main import app

client = TestClient(app)


def test_hello() -> None:
    response = client.get("/hello")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello from Atelier AI"}


def test_describe_returns_a_dummy_description() -> None:
    files = {"image": ("harbor.jpg", b"fake jpeg bytes", "image/jpeg")}

    response = client.post("/describe", files=files)

    assert response.status_code == 200
    body = response.json()
    assert body["titles"] == ["Dummy Title"]
    assert "harbor.jpg" in body["description"]


def test_describe_rejects_a_text_file() -> None:
    files = {"image": ("notes.txt", b"not an image", "text/plain")}

    response = client.post("/describe", files=files)

    assert response.status_code == 415
