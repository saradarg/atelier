import json

import pytest
from pydantic import ValidationError

from ai.models import Description

PALETTE = [
    {"hex": "#1B3A5C", "name": "deep blue", "pigment": "Prussian Blue"},
    {"hex": "#E8D5B0", "name": "warm cream", "pigment": "Yellow Ochre"},
    {"hex": "#B5562D", "name": "rust", "pigment": "Burnt Sienna"},
    {"hex": "#5B6B3A", "name": "olive green", "pigment": "Sap Green"},
    {"hex": "#2E2A28", "name": "near black", "pigment": "Payne's Gray"},
]

GOOD_ANSWER = {
    "titles": ["Harbor at Dusk", "Boats at Rest", "Evening Tide"],
    "description": "I painted this on the quay. I left the paper bare for the light.",
    "palette": PALETTE,
}


def test_description_accepts_a_good_answer() -> None:
    result = Description.model_validate_json(json.dumps(GOOD_ANSWER))

    assert result.titles[0] == "Harbor at Dusk"
    assert len(result.palette) == 5
    assert result.palette[0].pigment == "Prussian Blue"


def with_first_hex(hex_code: str) -> list[dict[str, str]]:
    """The good palette, with the first color's hex code swapped."""
    return [{**PALETTE[0], "hex": hex_code}, *PALETTE[1:]]


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        pytest.param("titles", ["Harbor at Dusk"], id="1 title"),
        pytest.param("titles", ["A", "B", "C", "D"], id="4 titles"),
        pytest.param("palette", PALETTE[:4], id="4 colors"),
        pytest.param("palette", with_first_hex("1B3A5C"), id="hex without #"),
        pytest.param("palette", with_first_hex("#1B3A5"), id="hex too short"),
        pytest.param("palette", with_first_hex("deep blue"), id="name, not hex"),
    ],
)
def test_description_rejects_a_bad_answer(field: str, bad_value: object) -> None:
    answer = {**GOOD_ANSWER, field: bad_value}

    with pytest.raises(ValidationError):
        Description.model_validate(answer)
