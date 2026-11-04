"""Palette Pal: a Claude agent that measures a painting's colors, then saves a draft."""

import json
import mimetypes
import sys
from pathlib import Path
from typing import Any

import anthropic
from anthropic.types import (
    Message,
    MessageParam,
    ToolParam,
    ToolResultBlockParam,
    ToolUseBlock,
)

from ai.claude_client import (
    EFFORT,
    MODEL,
    SYSTEM_PROMPT,
    estimate_cost,
    image_block_from_bytes,
)
from ai.models import Description
from ai.palette import get_palette

MAX_TURNS = 10  # safety cap: a confused agent can't loop (and spend) forever

AGENT_PROMPT = (
    "Here is one of my paintings. First call get_palette to measure its 5 main "
    "colors. Then write 3 titles and a 2-sentence description, give each measured "
    "color a plain name and a likely pigment, and save everything with save_draft."
)

TOOLS: list[ToolParam] = [
    {
        "name": "get_palette",
        "description": (
            "Measure the painting's main colors from its pixels. Returns hex codes, "
            "most common first, with how much of the painting each one covers. "
            "Call this before you name any colors."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "count": {
                    "type": "integer",
                    "description": "How many colors to find, from 1 to 10",
                },
            },
            "required": ["count"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "name": "save_draft",
        "description": (
            "Save the finished titles, description and palette as a draft for me "
            "to review. Call this once, when everything is ready."
        ),
        "input_schema": anthropic.transform_schema(Description),
        "strict": True,
    },
]


class PalettePal:
    """One agent run for one painting: it holds the image and the saved draft."""

    def __init__(self, image_bytes: bytes, media_type: str | None) -> None:
        self.image = image_block_from_bytes(image_bytes, media_type)
        self.image_bytes = image_bytes
        self.draft: Description | None = None
        self.input_tokens = 0
        self.output_tokens = 0

    # The tools: plain methods that Claude can ask us to run.

    def get_palette(self, count: int) -> str:
        swatches = get_palette(self.image_bytes, count)
        return "\n".join(
            f"{swatch.hex} covers {swatch.share:.1%}" for swatch in swatches
        )

    def save_draft(self, **draft: Any) -> str:
        self.draft = Description.model_validate(draft)
        return "Draft saved."

    # The agent loop.

    def run(self, client: anthropic.Anthropic) -> Description:
        """Talk to Claude, running the tools it asks for, until it's done."""
        messages: list[MessageParam] = [
            {
                "role": "user",
                "content": [self.image, {"type": "text", "text": AGENT_PROMPT}],
            }
        ]

        for turn in range(1, MAX_TURNS + 1):
            response = client.messages.create(
                model=MODEL,
                max_tokens=16000,
                output_config={"effort": EFFORT},
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )
            self.input_tokens += response.usage.input_tokens
            self.output_tokens += response.usage.output_tokens
            print_turn(turn, response)

            messages.append({"role": "assistant", "content": response.content})
            if response.stop_reason != "tool_use":
                break
            results = [
                self.run_tool(block)
                for block in response.content
                if block.type == "tool_use"
            ]
            messages.append({"role": "user", "content": results})
        else:
            raise RuntimeError(f"The agent didn't finish within {MAX_TURNS} turns")

        if self.draft is None:
            raise RuntimeError(
                f"The agent stopped ({response.stop_reason}) without saving a draft"
            )
        return self.draft

    def run_tool(self, block: ToolUseBlock) -> ToolResultBlockParam:
        """Run the tool Claude asked for. Failures go back to Claude as errors."""
        tools = {"get_palette": self.get_palette, "save_draft": self.save_draft}
        tool = tools.get(block.name)
        try:
            if tool is None:
                raise ValueError(f"there is no tool called {block.name!r}")
            output = tool(**block.input)
        # ValueError: bad input (ValidationError is one). TypeError: wrong arguments.
        # OSError: Pillow couldn't read the image. Tell Claude instead of crashing.
        except (ValueError, TypeError, OSError) as e:
            print(f"  -> error: {e}")
            return {
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": f"Error: {e}",
                "is_error": True,
            }
        print(f"  -> {output}")
        return {"type": "tool_result", "tool_use_id": block.id, "content": output}


def print_turn(turn: int, response: Message) -> None:
    """Show what Claude sent back this turn, block by block."""
    print(f"\n--- Turn {turn}: stop_reason = {response.stop_reason} ---")
    for block in response.content:
        if block.type == "text":
            print(f"  [text] {block.text}")
        elif block.type == "tool_use":
            print(f"  [tool_use] {block.name} {json.dumps(block.input)[:150]}")
        else:
            print(f"  [{block.type}]")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: uv run python -m ai.agent <image>")
        return

    path = Path(sys.argv[1])
    media_type, _ = mimetypes.guess_type(path)
    agent = PalettePal(path.read_bytes(), media_type)
    draft = agent.run(anthropic.Anthropic())

    print("\n===== Saved draft =====")
    print(draft.model_dump_json(indent=2))
    cost = estimate_cost(agent.input_tokens, agent.output_tokens)
    print(
        f"\nAll turns: {agent.input_tokens} tokens in, "
        f"{agent.output_tokens} out, about ${cost:.4f}"
    )


if __name__ == "__main__":
    main()
