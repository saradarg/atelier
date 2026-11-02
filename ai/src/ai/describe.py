"""Describe my paintings with Claude, in my own voice, and estimate the cost."""

import base64
import mimetypes
import sys
from decimal import Decimal
from pathlib import Path

import anthropic
from anthropic.types import ImageBlockParam, ParsedMessage
from pydantic import BaseModel

MODEL = "claude-opus-5-5"
# EFFORT = "low"  # low | medium | high | xhigh | max
# US dollars per million tokens for MODEL. Check the pricing page if you change it.
PRICE_PER_MILLION_IN = Decimal(4)
PRICE_PER_MILLION_OUT = Decimal(20)
MAX_IMAGE_BYTES = 5 * 1024 * 1024
SUPPORTED_TYPES = ("image/jpeg", "image/png", "image/webp")

SYSTEM_PROMPT = """\
You help me, a working artist, describe my own paintings for my portfolio website.
I work in watercolor, colored pencil and pastel, and I paint everyday subjects:
fruit on the table, family objects, harbors, fields and weather.

Write the description in my voice: first person, warm and plain, as if I'm
talking to a visitor at a small local show. Use short sentences. Mention what
drew me to the scene and one thing about the technique or the paper.
Avoid gallery cliches such as "evocative", "masterful", "invites the viewer"
or "a testament to".

Titles: 2 to 5 words, concrete, no colons.
Palette: hex colors taken from the image, and pigment names a painter would
actually buy, such as "Ultramarine Blue" or "Burnt Sienna".
"""

PROMPT = (
    "Here is one of my paintings. Suggest 3 titles, a 2-sentence description, "
    "and its 5 main colors with a likely pigment for each."
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


def estimate_cost(input_tokens: int, output_tokens: int) -> Decimal:
    """Estimate the price of one call in US dollars."""
    cost_in = input_tokens * PRICE_PER_MILLION_IN
    cost_out = output_tokens * PRICE_PER_MILLION_OUT
    return (cost_in + cost_out) / 1_000_000


def describe_painting(
    client: anthropic.Anthropic, path: Path
) -> ParsedMessage[Description]:
    """Send one painting to Claude and return the parsed response."""
    return client.messages.parse(
        model=MODEL,
        max_tokens=16000,
        # output_config={"effort": EFFORT},
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [image_block(path), {"type": "text", "text": PROMPT}],
            }
        ],
        output_format=Description,
    )


def print_description(response: ParsedMessage[Description], cost: Decimal) -> None:
    usage = response.usage
    print("Stop reason:", response.stop_reason)
    print(f"Tokens:      {usage.input_tokens} in, {usage.output_tokens} out")
    print(f"Cost:        ${cost:.4f}")

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


def main() -> None:
    paths = [Path(arg) for arg in sys.argv[1:]]
    if not paths:
        print("Usage: uv run python -m ai.describe <image> [<image> ...]")
        return

    client = anthropic.Anthropic()
    total = Decimal(0)
    described = 0

    for path in paths:
        print(f"\n===== {path.name} =====")
        try:
            response = describe_painting(client, path)
        except (FileNotFoundError, ValueError) as e:
            print(f"Can't use that image: {e}")
            continue
        except anthropic.AuthenticationError:
            print("The API key was rejected. Check ANTHROPIC_API_KEY.")
            return
        except anthropic.APIConnectionError:
            print("Couldn't reach the Claude API. Check your internet connection.")
            return

        usage = response.usage
        cost = estimate_cost(usage.input_tokens, usage.output_tokens)
        total += cost
        described += 1
        print_description(response, cost)

    if described:
        print(f"\nTotal for {described} paintings: ${total:.4f}")
        print(f"Average per painting:   ${total / described:.4f}")


if __name__ == "__main__":
    main()
