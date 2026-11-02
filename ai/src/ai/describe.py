"""Day 8: describe one painting with Claude and get back a Description object."""

import base64
import mimetypes
import sys
from pathlib import Path

import anthropic
from anthropic.types import ImageBlockParam
from pydantic import BaseModel

MODEL = "claude-opus-5-5"
MAX_IMAGE_BYTES = 5 * 1024 * 1024
SUPPORTED_TYPES = ("image/jpeg", "image/png", "image/webp")
PROMPT = (
    "This is one of my paintings. Suggest 3 titles, a 2-sentence gallery "
    "description, and its 5 main colors with a likely pigment for each."
)


class PaletteColor(BaseModel):
    hex: str
    name: str
    pigment: str


class Description(BaseModel):
    titles: list[str]
    description: str
    palette: list[PaletteColor]


def image_block(path: Path) -> ImageBlockParam:
    """Read an image file and wrap it the way the Messages API expects."""
    media_type, _ = mimetypes.guess_type(path)
    if media_type not in SUPPORTED_TYPES:
        raise ValueError(f"{path.name}: use a .jpg, .png or .webp image")
    data = path.read_bytes()
    if len(data) > MAX_IMAGE_BYTES:
        size_mb = len(data) / 1024 / 1024
        raise ValueError(f"{path.name} is {size_mb:.1f} MB; the limit is 5 MB")
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": base64.standard_b64encode(data).decode("ascii"),
        },
    }


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: uv run python -m ai.describe <path to image>")
        return

    try:
        image = image_block(Path(sys.argv[1]))
    except (FileNotFoundError, ValueError) as e:
        print(f"Can't use that image: {e}")
        return

    client = anthropic.Anthropic()
    try:
        response = client.messages.parse(
            model=MODEL,
            max_tokens=16000,
            messages=[
                {
                    "role": "user",
                    "content": [image, {"type": "text", "text": PROMPT}],
                }
            ],
            output_format=Description,
        )
    except anthropic.AuthenticationError:
        print("The API key was rejected. Check ANTHROPIC_API_KEY.")
        return
    except anthropic.APIConnectionError:
        print("Couldn't reach the Claude API. Check your internet connection.")
        return

    print("Blocks:     ", [block.type for block in response.content])
    print("Stop reason:", response.stop_reason)
    usage = response.usage
    print(f"Tokens:      {usage.input_tokens} in, {usage.output_tokens} out")

    result = response.parsed_output
    if result is None:
        print("No description came back.")
        return

    print("\nTitles:")
    for title in result.titles:
        print(f"  - {title}")
    print(f"\nDescription:\n  {result.description}")
    print("\nPalette:")
    for color in result.palette:
        print(f"  {color.hex}  {color.name:<20} {color.pigment}")


if __name__ == "__main__":
    main()
