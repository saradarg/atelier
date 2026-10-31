from decimal import Decimal
from pathlib import Path

import pytest

from ai.catalog import Artwork, load_artworks

HEADER = "title,medium,surface,width_in,height_in,year,price,sold\n"


def write_csv(tmp_path: Path, text: str) -> Path:
    csv_file = tmp_path / "artworks.csv"
    csv_file.write_text(text, encoding="utf-8")
    return csv_file


def make_row(**changes: str) -> dict[str, str]:
    row = {
        "title": "Lotus Pond",
        "medium": "watercolor",
        "surface": "hot-press paper",
        "width_in": "11",
        "height_in": "14",
        "year": "2025",
        "price": "380",
        "sold": "no",
    }
    row.update(changes)
    return row


def test_load_artworks_converts_each_column(tmp_path: Path) -> None:
    csv_file = write_csv(
        tmp_path,
        HEADER
        + '"Harbor, at Dusk",watercolor,cold-press paper,12,16,2024,450,no\n'
        + "Morning Pears,colored_pencil,toned paper,9,12,2023,300,yes\n",
    )

    artworks = load_artworks(csv_file)

    assert len(artworks) == 2
    assert artworks[0] == Artwork(
        title="Harbor, at Dusk",
        medium="watercolor",
        surface="cold-press paper",
        width_in=12.0,
        height_in=16.0,
        year=2024,
        price=Decimal(450),
        sold=False,
    )
    assert artworks[1].sold is True


def test_load_artworks_handles_excel_bom(tmp_path: Path) -> None:
    csv_file = tmp_path / "artworks.csv"
    csv_file.write_text(
        HEADER + "Lotus Pond,watercolor,hot-press paper,11,14,2025,380,no\n",
        encoding="utf-8-sig",
    )

    artworks = load_artworks(csv_file)

    assert artworks[0].title == "Lotus Pond"


def test_load_artworks_with_only_a_header_is_empty(tmp_path: Path) -> None:
    assert load_artworks(write_csv(tmp_path, HEADER)) == []


def test_load_artworks_names_the_row_with_a_bad_number(tmp_path: Path) -> None:
    csv_file = write_csv(
        tmp_path,
        HEADER
        + "Lotus Pond,watercolor,hot-press paper,11,14,2025,380,no\n"
        + "Quiet Creek,watercolor,rough paper,15,22,20x5,700,no\n",
    )

    with pytest.raises(ValueError, match="row 3"):
        load_artworks(csv_file)


def test_load_artworks_names_a_missing_column(tmp_path: Path) -> None:
    csv_file = write_csv(
        tmp_path,
        "title,medium,surface,width_in,height_in,year,price\n"
        "Lotus Pond,watercolor,hot-press paper,11,14,2025,380\n",
    )

    with pytest.raises(ValueError, match="missing column 'sold'"):
        load_artworks(csv_file)


def test_load_artworks_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_artworks(tmp_path / "no-such-file.csv")


@pytest.mark.parametrize(
    ("text", "expected"),
    [("yes", True), ("no", False), ("Yes", True), (" NO ", False)],
)
def test_from_row_reads_sold(text: str, expected: bool) -> None:
    assert Artwork.from_row(make_row(sold=text)).sold is expected


@pytest.mark.parametrize("text", ["", "true", "sold", "y"])
def test_from_row_rejects_unknown_sold_values(text: str) -> None:
    with pytest.raises(ValueError, match="sold must be 'yes' or 'no'"):
        Artwork.from_row(make_row(sold=text))


def test_from_row_keeps_exact_cents() -> None:
    assert Artwork.from_row(make_row(price="19.99")).price == Decimal("19.99")


def test_from_row_rejects_a_bad_price() -> None:
    with pytest.raises(ValueError, match="price must be a number"):
        Artwork.from_row(make_row(price="cheap"))