from decimal import Decimal

from ai.catalog import Artwork
from ai.reports import count_by_medium, total_value, unsold


def make_artwork(
    title: str = "Test piece",
    medium: str = "watercolor",
    price: str = "100",
    sold: bool = False,
) -> Artwork:
    return Artwork(
        title=title,
        medium=medium,
        surface="paper",
        width_in=10.0,
        height_in=10.0,
        year=2025,
        price=Decimal(price),
        sold=sold,
    )


def test_unsold_keeps_only_unsold_artworks_in_order() -> None:
    artworks = [
        make_artwork("First", sold=False),
        make_artwork("Second", sold=True),
        make_artwork("Third", sold=False),
    ]

    assert [art.title for art in unsold(artworks)] == ["First", "Third"]


def test_total_value_adds_prices() -> None:
    artworks = [make_artwork(price="450"), make_artwork(price="300")]

    assert total_value(artworks) == Decimal(750)


def test_total_value_keeps_exact_cents() -> None:
    artworks = [make_artwork(price="0.10"), make_artwork(price="0.20")]

    assert total_value(artworks) == Decimal("0.30")


def test_total_value_of_no_artworks_is_zero() -> None:
    assert total_value([]) == Decimal(0)


def test_count_by_medium() -> None:
    artworks = [
        make_artwork(medium="pastel"),
        make_artwork(medium="watercolor"),
        make_artwork(medium="pastel"),
    ]

    assert count_by_medium(artworks) == {"pastel": 2, "watercolor": 1}


def test_count_by_medium_of_no_artworks_is_empty() -> None:
    assert count_by_medium([]) == {}