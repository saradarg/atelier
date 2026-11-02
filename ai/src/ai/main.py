"""Atelier AI service: HTTP endpoints for describing paintings."""

from fastapi import FastAPI, HTTPException, UploadFile

from ai.describe import SUPPORTED_TYPES, Description, PaletteColor

app = FastAPI(title="Atelier AI")


@app.get("/hello")
def hello() -> dict[str, str]:
    return {"message": "Hello from Atelier AI"}


@app.post("/describe")
def describe(image: UploadFile) -> Description:
    """Accept a painting photo. For now, return a dummy description."""
    if image.content_type not in SUPPORTED_TYPES:
        raise HTTPException(
            status_code=415, detail="Upload a .jpg, .png or .webp image"
        )
    data = image.file.read()
    return Description(
        titles=["Dummy Title"],
        description=(
            f"Received {image.filename} ({len(data):,} bytes). "
            "Claude isn't connected yet."
        ),
        palette=[
            PaletteColor(hex="#1B3A5C", name="deep blue", pigment="Prussian Blue")
        ],
    )
