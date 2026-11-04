from io import BytesIO

import pytest
from PIL import Image, UnidentifiedImageError

from ai.palette import Swatch, get_palette

DEEP_BLUE = (0x1B, 0x3A, 0x5C)
WHITE = (255, 255, 255)


def png_bytes(image: Image.Image) -> bytes:
    """Save an image as PNG in memory, the way an upload arrives."""
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_a_plain_image_has_one_color() -> None:
    image = Image.new("RGB", (100, 100), DEEP_BLUE)

    palette = get_palette(png_bytes(image))

    assert palette == [Swatch(hex="#1B3A5C", share=1.0)]


def test_colors_come_most_common_first() -> None:
    image = Image.new("RGB", (100, 100), DEEP_BLUE)
    image.paste(WHITE, (0, 0, 50, 50))  # a white square: a quarter of the image

    palette = get_palette(png_bytes(image))

    assert palette == [
        Swatch(hex="#1B3A5C", share=0.75),
        Swatch(hex="#FFFFFF", share=0.25),
    ]


def test_a_busy_image_gives_the_requested_number_of_colors() -> None:
    # A gradient: every column is a different shade.
    image = Image.new("RGB", (256, 10))
    for x in range(256):
        image.paste((x, 100, 255 - x), (x, 0, x + 1, 10))

    palette = get_palette(png_bytes(image), count=3)

    assert len(palette) == 3
    assert sum(swatch.share for swatch in palette) == pytest.approx(1.0)


def test_a_grayscale_image_still_gives_rgb_hex_codes() -> None:
    image = Image.new("L", (100, 100), 128)  # "L" means one gray channel

    palette = get_palette(png_bytes(image))

    assert palette == [Swatch(hex="#808080", share=1.0)]


@pytest.mark.parametrize("count", [0, 11])
def test_count_must_be_from_1_to_10(count: int) -> None:
    image = Image.new("RGB", (10, 10), DEEP_BLUE)

    with pytest.raises(ValueError, match="from 1 to 10"):
        get_palette(png_bytes(image), count=count)


def test_bytes_that_are_not_an_image_are_rejected() -> None:
    with pytest.raises(UnidentifiedImageError):
        get_palette(b"not an image")
