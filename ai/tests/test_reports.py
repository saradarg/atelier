from ai.catalog import Artwork
from ai.reports import count_by_medium, total_value, unsold


def make_artwork(
    medium: str = "watercolor", price: float = 100.0, sold: bool = False
) -> Artwork:
    return Artwork(
        title="Test piece",
        medium=medium,
        surface="paper",
        width_in=10.0,
        height_in=10.0,
        year=2025,
        price=price,
        sold=sold,
    )


def test_unsold_keeps_only_unsold_artworks() -> None:
    artworks = [
        make_artwork(sold=False),
        make_artwork(sold=True),
        make_artwork(sold=False),
    ]

    assert len(unsold(artworks)) == 2


def test_total_value_adds_prices() -> None:
    artworks = [make_artwork(price=450), make_artwork(price=300)]

    assert total_value(artworks) == 750


def test_total_value_of_no_artworks_is_zero() -> None:
    assert total_value([]) == 0


def test_count_by_medium() -> None:
    artworks = [
        make_artwork("pastel"),
        make_artwork("watercolor"),
        make_artwork("pastel"),
    ]

    assert count_by_medium(artworks) == {"pastel": 2, "watercolor": 1}
