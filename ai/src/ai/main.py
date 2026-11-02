"""Atelier AI service: HTTP endpoints for describing paintings."""

import logging
from functools import cache
from typing import Annotated

import anthropic
from fastapi import Depends, FastAPI, HTTPException, UploadFile

from ai.claude_client import SUPPORTED_TYPES, describe_image, image_block_from_bytes
from ai.models import Description

logger = logging.getLogger(__name__)

app = FastAPI(title="Atelier AI")


@cache
def get_client() -> anthropic.Anthropic:
    """Create one Claude client and reuse it for every request."""
    return anthropic.Anthropic()


@app.get("/hello")
def hello() -> dict[str, str]:
    return {"message": "Hello from Atelier AI"}


@app.post("/describe")
def describe(
    image: UploadFile,
    client: Annotated[anthropic.Anthropic, Depends(get_client)],
) -> Description:
    """Describe an uploaded painting photo with Claude."""
    if image.content_type not in SUPPORTED_TYPES:
        raise HTTPException(
            status_code=415, detail="Upload a .jpg, .png or .webp image"
        )
    try:
        block = image_block_from_bytes(image.file.read(), image.content_type)
    except ValueError as e:
        # The type was checked above, so this means the image is too big.
        raise HTTPException(status_code=413, detail=str(e)) from e

    try:
        response = describe_image(client, block)
    except anthropic.APIError as e:
        logger.exception("Claude request failed")
        raise HTTPException(status_code=502, detail="Claude request failed") from e

    if response.parsed_output is None:
        raise HTTPException(
            status_code=502,
            detail=f"Claude returned no description ({response.stop_reason})",
        )
    return response.parsed_output
