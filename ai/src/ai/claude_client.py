"""Everything about talking to Claude: prompts, images, the call and its cost."""

import base64
import mimetypes
from decimal import Decimal
from pathlib import Path

import anthropic
from anthropic.types import ImageBlockParam, ParsedMessage

from ai.models import Description

MODEL = "claude-opus-5-5"
EFFORT = "medium"  # low | medium | high | xhigh | max
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


def image_block(path: Path) -> ImageBlockParam:
    """Read an image file and wrap it the way the Messages API expects."""
    media_type, _ = mimetypes.guess_type(path)
    return image_block_from_bytes(path.read_bytes(), media_type)


def image_block_from_bytes(data: bytes, media_type: str | None) -> ImageBlockParam:
    """Wrap image bytes (from a file or an upload) for the Messages API."""
    if media_type not in SUPPORTED_TYPES:
        raise ValueError("use a .jpg, .png or .webp image")
    if len(data) > MAX_IMAGE_BYTES:
        size_mb = len(data) / 1024 / 1024
        raise ValueError(f"the image is {size_mb:.1f} MB; the limit is 5 MB")
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
    """Send one painting file to Claude and return the parsed response."""
    return describe_image(client, image_block(path))


def describe_image(
    client: anthropic.Anthropic, image: ImageBlockParam
) -> ParsedMessage[Description]:
    """Send one image block to Claude and return the parsed response."""
    return client.messages.parse(
        model=MODEL,
        max_tokens=16000,
        output_config={"effort": EFFORT},
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [image, {"type": "text", "text": PROMPT}],
            }
        ],
        output_format=Description,
    )
