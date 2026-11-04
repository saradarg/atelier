from io import BytesIO
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, create_autospec

import anthropic
import pytest
from anthropic.resources.messages import Messages
from anthropic.types import TextBlock, ToolUseBlock
from PIL import Image

from ai.agent import MAX_TURNS, TOOLS, PalettePal
from ai.claude_client import MODEL
from ai.models import Description

DRAFT = {
    "titles": ["Harbor at Dusk", "Boats at Rest", "Evening Tide"],
    "description": "I painted this on the quay. I left the paper bare for the light.",
    "palette": [
        {"hex": "#1B3A5C", "name": "deep blue", "pigment": "Prussian Blue"},
        {"hex": "#E8D5B0", "name": "warm cream", "pigment": "Yellow Ochre"},
        {"hex": "#B5562D", "name": "rust", "pigment": "Burnt Sienna"},
        {"hex": "#5B6B3A", "name": "olive green", "pigment": "Sap Green"},
        {"hex": "#2E2A28", "name": "near black", "pigment": "Payne's Gray"},
    ],
}

DONE = TextBlock(type="text", text="I saved your draft.")


def blue_png() -> bytes:
    """A small all-blue PNG, so get_palette has something real to measure."""
    buffer = BytesIO()
    Image.new("RGB", (20, 20), (0x1B, 0x3A, 0x5C)).save(buffer, format="PNG")
    return buffer.getvalue()


def reply(stop_reason: str, *blocks: Any) -> SimpleNamespace:
    """A fake Claude response with the given blocks."""
    usage = SimpleNamespace(input_tokens=1000, output_tokens=100)
    return SimpleNamespace(stop_reason=stop_reason, content=list(blocks), usage=usage)


def tool_call(name: str, **tool_input: Any) -> ToolUseBlock:
    """A block where Claude asks us to run a tool."""
    return ToolUseBlock(
        type="tool_use", id=f"toolu_{name}", name=name, input=tool_input
    )


@pytest.fixture
def fake_claude() -> MagicMock:
    fake = MagicMock(spec=anthropic.Anthropic)
    fake.messages = create_autospec(Messages, instance=True)
    return fake


def test_agent_measures_colors_then_saves_a_draft(fake_claude: MagicMock) -> None:
    fake_claude.messages.create.side_effect = [
        reply("tool_use", tool_call("get_palette", count=5)),
        reply("tool_use", tool_call("save_draft", **DRAFT)),
        reply("end_turn", DONE),
    ]
    agent = PalettePal(blue_png(), "image/png")

    draft = agent.run(fake_claude)

    assert draft == Description.model_validate(DRAFT)
    assert fake_claude.messages.create.call_count == 3
    assert agent.input_tokens == 3000

    call = fake_claude.messages.create.call_args.kwargs
    assert call["model"] == MODEL
    assert call["tools"] is TOOLS
    # The whole conversation: my prompt, then Claude and my code taking turns.
    messages = call["messages"]
    roles = [message["role"] for message in messages]
    assert roles == ["user", "assistant", "user", "assistant", "user", "assistant"]
    palette_result = messages[2]["content"][0]
    assert palette_result["tool_use_id"] == "toolu_get_palette"
    assert palette_result["content"] == "#1B3A5C covers 100.0%"


def test_a_bad_draft_goes_back_to_claude_as_an_error(fake_claude: MagicMock) -> None:
    one_title = {**DRAFT, "titles": ["Harbor at Dusk"]}
    fake_claude.messages.create.side_effect = [
        reply("tool_use", tool_call("save_draft", **one_title)),
        reply("tool_use", tool_call("save_draft", **DRAFT)),
        reply("end_turn", DONE),
    ]
    agent = PalettePal(blue_png(), "image/png")

    draft = agent.run(fake_claude)

    assert draft.titles == DRAFT["titles"]
    messages = fake_claude.messages.create.call_args.kwargs["messages"]
    error = messages[2]["content"][0]
    assert error["is_error"] is True
    assert "titles" in error["content"]


def test_an_unknown_tool_goes_back_to_claude_as_an_error(
    fake_claude: MagicMock,
) -> None:
    fake_claude.messages.create.side_effect = [
        reply("tool_use", tool_call("delete_everything")),
        reply("tool_use", tool_call("save_draft", **DRAFT)),
        reply("end_turn", DONE),
    ]
    agent = PalettePal(blue_png(), "image/png")

    agent.run(fake_claude)

    messages = fake_claude.messages.create.call_args.kwargs["messages"]
    error = messages[2]["content"][0]
    assert error["is_error"] is True
    assert "no tool called 'delete_everything'" in error["content"]


def test_the_agent_stops_after_max_turns(fake_claude: MagicMock) -> None:
    fake_claude.messages.create.return_value = reply(
        "tool_use", tool_call("get_palette", count=5)
    )
    agent = PalettePal(blue_png(), "image/png")

    with pytest.raises(RuntimeError, match="didn't finish"):
        agent.run(fake_claude)

    assert fake_claude.messages.create.call_count == MAX_TURNS


def test_finishing_without_a_draft_is_an_error(fake_claude: MagicMock) -> None:
    fake_claude.messages.create.side_effect = [reply("end_turn", DONE)]
    agent = PalettePal(blue_png(), "image/png")

    with pytest.raises(RuntimeError, match="without saving a draft"):
        agent.run(fake_claude)
