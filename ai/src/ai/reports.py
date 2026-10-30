"""Reports about my artwork catalog."""
from collections import Counter
from ai.catalog import Artwork

def unsold(artworks: list[Artwork]) -> list[Artwork]:
  return [art for art in artworks if not art.sold]

def total_value(artworks: list[Artwork]) -> float:
  return sum(art.price for art in artworks)

def count_by_medium(artworks: list[Artwork]) -> dict[str, int]:
  return dict(Counter(art.medium for art in artworks))


  