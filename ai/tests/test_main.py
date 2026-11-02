from fastapi.testclient import TestClient

from ai.describe import MAX_IMAGE_BYTES
from ai.main import app

client = TestClient(app)


def test_hello() -> None:
    response = client.get("/hello")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello from Atelier AI"}


def test_describe_rejects_a_text_file() -> None:
    files = {"image": ("notes.txt", b"not an image", "text/plain")}

    response = client.post("/describe", files=files)

    assert response.status_code == 415


def test_describe_rejects_an_image_over_5_mb() -> None:
    files = {"image": ("huge.jpg", b"x" * (MAX_IMAGE_BYTES + 1), "image/jpeg")}

    response = client.post("/describe", files=files)

    assert response.status_code == 413
    assert "the limit is 5 MB" in response.json()["detail"]
