"""Load my artwork catalog from a CSV file."""

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Artwork:
    title: str
    medium: str
    surface: str
    width_in: float
    height_in: float
    year: int
    price: float
    sold: bool


def load_artworks(path: Path) -> list[Artwork]:
    artworks: list[Artwork] = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            artwork = Artwork(
                title=row["title"],
                medium=row["medium"],
                surface=row["surface"],
                width_in=float(row["width_in"]),
                height_in=float(row["height_in"]),
                year=int(row["year"]),
                price=float(row["price"]),
                sold=row["sold"] == "yes",
            )
            artworks.append(artwork)
    return artworks
