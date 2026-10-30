from pathlib import Path

from ai.catalog import load_artworks
from ai.reports import count_by_medium, total_value, unsold


def main() -> None:

    artworks = load_artworks(Path("data/artworks.csv"))
    print(f"Catalog: {len(artworks)} artworks")

    print("\nBy medium")
    for medium, count in count_by_medium(artworks).items():
        print(f" {medium:<16}{count}")

    available = unsold(artworks)
    print(f"\nUnsold: {len(available)} artworks worth ${total_value(available):,.0f}")

    for art in available:
        print(f"  {art.title} ({art.medium}, {art.year}) ${art.price:,.0f}")

    print(f"\n\nTotal value of all 10 artworks --> ${total_value(artworks):,.0f}")

    print("\n Pastel works --> ")

    pastels = [art for art in artworks if art.medium == "pastel"]
    for art in pastels:
        print(f"{art.title} ({art.medium}, {art.year}) ${art.price:,.0f}")

    prices = {art.title: art.price for art in artworks}
    print(f"\nPrices --> \n {prices}")
    print(prices["Lotus Pond"])
