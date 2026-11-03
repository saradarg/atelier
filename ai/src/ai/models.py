"""Data shapes shared by the Claude client, the API and the command line."""

from pydantic import BaseModel, Field


class PaletteColor(BaseModel):
    hex: str = Field(
        pattern=r"^#[0-9A-Fa-f]{6}$",
        description="The color as a 6-digit hex code, like #1B3A5C",
    )
    name: str = Field(description="A plain name for the color, like 'deep blue'")
    pigment: str = Field(description="The likely pigment, like 'Prussian Blue'")


class Description(BaseModel):
    titles: list[str] = Field(
        min_length=3,
        max_length=3,
        description="Exactly 3 title ideas, 2 to 5 words each",
    )
    description: str = Field(description="Two sentences in the artist's voice")
    palette: list[PaletteColor] = Field(
        min_length=5,
        max_length=5,
        description="The painting's 5 main colors",
    )
