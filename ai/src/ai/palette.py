"""Find the main colors of an image with Pillow. Plain code, no AI."""

import sys
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from PIL import Image

# Shrink the image first: 200 x 200 is plenty to find the main colors, and fast.
SAMPLE_SIZE = (200, 200)


@dataclass(frozen=True)
class Swatch:
    hex: str  # like "#1B3A5C"
    share: float  # how much of the image is this color, from 0 to 1


def get_palette(image_bytes: bytes, count: int = 5) -> list[Swatch]:
    """Return the image's main colors, the most common first."""
    if not 1 <= count <= 10:
        raise ValueError(f"count must be from 1 to 10, not {count}")

    with Image.open(BytesIO(image_bytes)) as image:
        image.thumbnail(SAMPLE_SIZE)
        rgb = image.convert("RGB")

    # Reduce the image to `count` colors, then count the pixels of each one.
    reduced = rgb.quantize(colors=count, method=Image.Quantize.MEDIANCUT)
    colors = reduced.getpalette()  # flat list: [r0, g0, b0, r1, g1, b1, ...]
    pixel_counts = reduced.getcolors()  # [(pixels, color_index), ...]
    total = reduced.width * reduced.height

    swatches = []
    for pixels, index in sorted(pixel_counts, reverse=True):    
        red, green, blue = colors[index * 3 : index * 3 + 3]
        swatches.append(
            Swatch(hex=f"#{red:02X}{green:02X}{blue:02X}", share=pixels / total)
        )
    return swatches


def main() -> None:
    paths = [Path(arg) for arg in sys.argv[1:]]
    if not paths:
        print("Usage: uv run python -m ai.palette <image> [<image> ...]")
        return

    for path in paths:
        print(f"\n{path.name}")
        for swatch in get_palette(path.read_bytes()):
            print(f"  {swatch.hex}  {swatch.share:6.1%}")


if __name__ == "__main__":
    main()
