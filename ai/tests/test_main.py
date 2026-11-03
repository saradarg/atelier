from collections.abc import Iterator
from types import SimpleNamespace
from unittest.mock import MagicMock, create_autospec

import anthropic
import httpx2
import pytest
from anthropic.resources.messages import Messages
from fastapi.testclient import TestClient
from pydantic import ValidationError

from ai.claude_client import EFFORT, MAX_IMAGE_BYTES, MODEL
from ai.main import app, get_client
from ai.models import Description, PaletteColor

api = TestClient(app)

JPEG_UPLOAD = {"image": ("harbor.jpg", b"fake jpeg bytes", "image/jpeg")}
CLAUDE_URL = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")

SAMPLE = Description(
    titles=["Harbor at Dusk", "Boats at Rest", "Evening Tide"],
    description="I painted this on the quay. I left the paper bare for the light.",
    palette=[
        PaletteColor(hex="#1B3A5C", name="deep blue", pigment="Prussian Blue"),
        PaletteColor(hex="#E8D5B0", name="warm cream", pigment="Yellow Ochre"),
        PaletteColor(hex="#B5562D", name="rust", pigment="Burnt Sienna"),
        PaletteColor(hex="#5B6B3A", name="olive green", pigment="Sap Green"),
        PaletteColor(hex="#2E2A28", name="near black", pigment="Payne's Gray"),
    ],
)


@pytest.fixture
def fake_claude() -> Iterator[MagicMock]:
    """Replace the real Claude client with a fake for one test."""
    fake = MagicMock(spec=anthropic.Anthropic)
    fake.messages = create_autospec(Messages, instance=True)
    app.dependency_overrides[get_client] = lambda: fake
    yield fake
    app.dependency_overrides.clear()


def test_hello() -> None:
    response = api.get("/hello")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello from Atelier AI"}


def test_describe_returns_claudes_description(fake_claude: MagicMock) -> None:
    fake_claude.messages.parse.return_value = SimpleNamespace(
        parsed_output=SAMPLE, stop_reason="end_turn"
    )

    response = api.post("/describe", files=JPEG_UPLOAD)

    assert response.status_code == 200
    assert response.json() == SAMPLE.model_dump()

    call = fake_claude.messages.parse.call_args.kwargs
    assert call["model"] == MODEL
    assert call["output_config"] == {"effort": EFFORT}
    assert call["output_format"] is Description
    image = call["messages"][0]["content"][0]
    assert image["source"]["media_type"] == "image/jpeg"


@pytest.mark.parametrize(
    ("error", "detail"),
    [
        (anthropic.APIConnectionError(request=CLAUDE_URL), "Claude request failed"),
        (
            anthropic.InternalServerError(
                "overloaded",
                response=httpx2.Response(500, request=CLAUDE_URL),
                body=None,
            ),
            "Claude request failed",
        ),
        (
            ValidationError.from_exception_data("Description", []),
            "Claude returned an invalid description",
        ),
    ],
)
def test_describe_returns_502_when_claude_fails(
    fake_claude: MagicMock, error: Exception, detail: str
) -> None:
    fake_claude.messages.parse.side_effect = error

    response = api.post("/describe", files=JPEG_UPLOAD)

    assert response.status_code == 502
    assert response.json() == {"detail": detail}


def test_describe_returns_502_when_no_description(fake_claude: MagicMock) -> None:
    fake_claude.messages.parse.return_value = SimpleNamespace(
        parsed_output=None, stop_reason="max_tokens"
    )

    response = api.post("/describe", files=JPEG_UPLOAD)

    assert response.status_code == 502
    assert "max_tokens" in response.json()["detail"]


def test_describe_rejects_a_text_file(fake_claude: MagicMock) -> None:
    files = {"image": ("notes.txt", b"not an image", "text/plain")}

    response = api.post("/describe", files=files)

    assert response.status_code == 415
    fake_claude.messages.parse.assert_not_called()


def test_describe_rejects_an_image_over_5_mb(fake_claude: MagicMock) -> None:
    files = {"image": ("huge.jpg", b"x" * (MAX_IMAGE_BYTES + 1), "image/jpeg")}

    response = api.post("/describe", files=files)

    assert response.status_code == 413
    assert response.json() == {"detail": "The image is over the 5 MB limit"}
    fake_claude.messages.parse.assert_not_called()
