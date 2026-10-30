from pathlib import Path
from ai.catalog import load_artworks

def main() -> None:
    # print("Hello from ai!")
    artworks = load_artworks(Path("data/artworks.csv"))

    for art in artworks:
        status = "sold" if art.sold else "available"
        if not art.sold:
            print(f"{art.title} | {art.medium} | ${art.price:,.0f} | {art.year} | {status} ")
        # print(art)
    print(f"Loaded {len(artworks)} artworks")
