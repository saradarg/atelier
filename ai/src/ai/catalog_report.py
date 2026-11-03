"""Command line: a summary of my artwork catalog."""

from pathlib import Path

from ai.catalog import load_artworks
from ai.reports import count_by_medium, total_value, unsold

# This file is ai/src/ai/catalog_report.py, so parents[2] is the ai/ folder.
CATALOG = Path(__file__).resolve().parents[2] / "data" / "artworks.csv"


def main() -> None:
    artworks = load_artworks(CATALOG)
    print(f"Catalog: {len(artworks)} artworks, worth ${total_value(artworks):,.0f}")

    print("\nBy medium")
    for medium, count in count_by_medium(artworks).items():
        print(f"  {medium:<16}{count}")

    available = unsold(artworks)
    print(f"\nUnsold: {len(available)} artworks worth ${total_value(available):,.0f}")
    for art in available:
        print(f"  {art.title} ({art.medium}, {art.year}) ${art.price:,.0f}")


if __name__ == "__main__":
    main()
