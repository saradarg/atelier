"""Reports about my artwork catalog."""

from collections import Counter
from collections.abc import Iterable
from decimal import Decimal

from ai.catalog import Artwork


def unsold(artworks: Iterable[Artwork]) -> list[Artwork]:
    """Return the artworks that haven't sold yet, in catalog order."""
    return [art for art in artworks if not art.sold]


def total_value(artworks: Iterable[Artwork]) -> Decimal:
    """Add up the prices. No artworks means a total of 0."""
    return sum((art.price for art in artworks), start=Decimal(0))


def count_by_medium(artworks: Iterable[Artwork]) -> dict[str, int]:
    """Count the artworks in each medium, for example {"pastel": 3}."""
    return dict(Counter(art.medium for art in artworks))
