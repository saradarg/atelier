import base64
from decimal import Decimal
from pathlib import Path

import pytest

from ai.describe import MAX_IMAGE_BYTES, Description, estimate_cost, image_block


def test_image_block_wraps_a_jpeg(tmp_path: Path) -> None:
    image = tmp_path / "harbor.jpg"
    image.write_bytes(b"fake jpeg bytes")

    block = image_block(image)

    assert block["type"] == "image"
    assert block["source"]["media_type"] == "image/jpeg"
    assert base64.b64decode(block["source"]["data"]) == b"fake jpeg bytes"


def test_image_block_rejects_other_file_types(tmp_path: Path) -> None:
    notes = tmp_path / "notes.txt"
    notes.write_text("not an image")

    with pytest.raises(ValueError, match="use a .jpg, .png or .webp"):
        image_block(notes)


def test_image_block_rejects_images_over_5_mb(tmp_path: Path) -> None:
    image = tmp_path / "huge.png"
    image.write_bytes(b"x" * (MAX_IMAGE_BYTES + 1))

    with pytest.raises(ValueError, match="the limit is 5 MB"):
        image_block(image)


def test_description_validates_claude_json() -> None:
    json_text = (
        '{"titles": ["Harbor at Dusk"], "description": "Boats at rest.", '
        '"palette": [{"hex": "#1B3A5C", "name": "deep blue", '
        '"pigment": "Prussian blue"}]}'
    )

    result = Description.model_validate_json(json_text)

    assert result.titles == ["Harbor at Dusk"]
    assert result.palette[0].pigment == "Prussian blue"


def test_estimate_cost_of_a_million_input_tokens() -> None:
    assert estimate_cost(1_000_000, 0) == Decimal(4)


def test_estimate_cost_adds_input_and_output() -> None:
    # (1,500 x $4 + 800 x $20) / 1,000,000 = $0.022
    assert estimate_cost(1_500, 800) == Decimal("0.022")
