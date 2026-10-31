"""Load my artwork catalog from a CSV file."""

import csv
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Self


@dataclass(frozen=True)
class Artwork:
    title: str
    medium: str
    surface: str
    width_in: float
    height_in: float
    year: int
    price: Decimal
    sold: bool

    @classmethod
    def from_row(cls, row: dict[str, str]) -> Self:
        """Build an Artwork from one CSV row, where every value is text."""
        return cls(
            title=row["title"],
            medium=row["medium"],
            surface=row["surface"],
            width_in=float(row["width_in"]),
            height_in=float(row["height_in"]),
            year=int(row["year"]),
            price=_parse_price(row["price"]),
            sold=_parse_sold(row["sold"]),
        )


def _parse_price(value: str) -> Decimal:
    try:
        return Decimal(value)
    except InvalidOperation:
        raise ValueError(f"price must be a number, got {value!r}") from None


def _parse_sold(value: str) -> bool:
    cleaned = value.strip().lower()
    if cleaned == "yes":
        return True
    if cleaned == "no":
        return False
    raise ValueError(f"sold must be 'yes' or 'no', got {value!r}")


def load_artworks(path: Path) -> list[Artwork]:
    """Read every row of the catalog CSV into an Artwork.

    Raises ValueError naming the file and row when a row has bad data.
    """
    artworks: list[Artwork] = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row_number, row in enumerate(csv.DictReader(f), start=2):
            try:
                artworks.append(Artwork.from_row(row))
            except KeyError as e:
                raise ValueError(f"{path}, row {row_number}: missing column {e}") from e
            except ValueError as e:
                raise ValueError(f"{path}, row {row_number}: {e}") from e
    return artworks
