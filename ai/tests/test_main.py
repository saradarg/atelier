from collections.abc import Iterator
from types import SimpleNamespace
from unittest.mock import MagicMock

import anthropic
import httpx2
import pytest
from fastapi.testclient import TestClient

from ai.describe import MAX_IMAGE_BYTES, MODEL, Description, PaletteColor
from ai.main import app, get_client

client = TestClient(app)

JPEG_UPLOAD = {"image": ("harbor.jpg", b"fake jpeg bytes", "image/jpeg")}

SAMPLE = Description(
    titles=["Harbor at Dusk", "Boats at Rest", "Evening Tide"],
    description="I painted this on the quay. I left the paper bare for the light.",
    palette=[PaletteColor(hex="#1B3A5C", name="deep blue", pigment="Prussian Blue")],
)


@pytest.fixture
def fake_claude() -> Iterator[MagicMock]:
    """Replace the real Claude client with a fake for one test."""
    fake = MagicMock()
    app.dependency_overrides[get_client] = lambda: fake
    yield fake
    app.dependency_overrides.clear()


def test_hello() -> None:
    response = client.get("/hello")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello from Atelier AI"}


def test_describe_returns_claudes_description(fake_claude: MagicMock) -> None:
    fake_claude.messages.parse.return_value = SimpleNamespace(
        parsed_output=SAMPLE, stop_reason="end_turn"
    )

    response = client.post("/describe", files=JPEG_UPLOAD)

    assert response.status_code == 200
    assert response.json() == SAMPLE.model_dump()

    call = fake_claude.messages.parse.call_args.kwargs
    assert call["model"] == MODEL
    assert call["output_format"] is Description
    image = call["messages"][0]["content"][0]
    assert image["source"]["media_type"] == "image/jpeg"


def test_describe_returns_502_when_claude_fails(fake_claude: MagicMock) -> None:
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    fake_claude.messages.parse.side_effect = anthropic.APIConnectionError(
        request=request
    )

    response = client.post("/describe", files=JPEG_UPLOAD)

    assert response.status_code == 502
    assert response.json() == {"detail": "Claude request failed"}


def test_describe_returns_502_when_no_description(fake_claude: MagicMock) -> None:
    fake_claude.messages.parse.return_value = SimpleNamespace(
        parsed_output=None, stop_reason="max_tokens"
    )

    response = client.post("/describe", files=JPEG_UPLOAD)

    assert response.status_code == 502
    assert "max_tokens" in response.json()["detail"]


def test_describe_rejects_a_text_file(fake_claude: MagicMock) -> None:
    files = {"image": ("notes.txt", b"not an image", "text/plain")}

    response = client.post("/describe", files=files)

    assert response.status_code == 415
    fake_claude.messages.parse.assert_not_called()


def test_describe_rejects_an_image_over_5_mb(fake_claude: MagicMock) -> None:
    files = {"image": ("huge.jpg", b"x" * (MAX_IMAGE_BYTES + 1), "image/jpeg")}

    response = client.post("/describe", files=files)

    assert response.status_code == 413
    assert "the limit is 5 MB" in response.json()["detail"]
    fake_claude.messages.parse.assert_not_called()
