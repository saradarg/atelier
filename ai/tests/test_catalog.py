from pathlib import Path

from ai.catalog import Artwork, load_artworks


def test_load_artworks_converts_each_column(tmp_path: Path) -> None:
    csv_file = tmp_path / "artworks.csv"
    csv_file.write_text(
        "title,medium,surface,width_in,height_in,year,price,sold\n"
        '"Harbor, at Dusk",watercolor,cold-press paper,12,16,2024,450,no\n'
        "Morning Pears,colored_pencil,toned paper,9,12,2023,300,yes\n",
        encoding="utf-8",
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
        price=450.0,
        sold=False,
    )
    assert artworks[1].sold is True


def test_load_artworks_handles_excel_bom(tmp_path: Path) -> None:
    csv_file = tmp_path / "artworks.csv"
    csv_file.write_text(
        "title,medium,surface,width_in,height_in,year,price,sold\n"
        "Lotus Pond,watercolor,hot-press paper,11,14,2025,380,no\n",
        encoding="utf-8-sig",
    )

    artworks = load_artworks(csv_file)

    assert artworks[0].title == "Lotus Pond"
