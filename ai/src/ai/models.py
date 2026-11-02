"""Data shapes shared by the Claude client, the API and the command line."""

from pydantic import BaseModel


class PaletteColor(BaseModel):
    hex: str
    name: str
    pigment: str


class Description(BaseModel):
    titles: list[str]
    description: str
    palette: list[PaletteColor]
