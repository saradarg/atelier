"""Command line: describe painting files and show what each description costs."""

import sys
from decimal import Decimal
from pathlib import Path

import anthropic
from anthropic.types import ParsedMessage

from ai.claude_client import describe_painting, estimate_cost
from ai.models import Description


def print_description(response: ParsedMessage[Description], cost: Decimal) -> None:
    usage = response.usage
    print("Stop reason:", response.stop_reason)
    print(f"Tokens:      {usage.input_tokens} in, {usage.output_tokens} out")
    print(f"Cost:        ${cost:.4f}")

    result = response.parsed_output
    if result is None:
        print("No description came back.")
        return

    print("\nTitles:")
    for title in result.titles:
        print(f"  - {title}")
    print(f"\nDescription:\n  {result.description}")
    print("\nPalette:")
    for color in result.palette:
        print(f"  {color.hex}  {color.name:<20} {color.pigment}")


def main() -> None:
    paths = [Path(arg) for arg in sys.argv[1:]]
    if not paths:
        print("Usage: uv run python -m ai.describe <image> [<image> ...]")
        return

    client = anthropic.Anthropic()
    total = Decimal(0)
    described = 0

    for path in paths:
        print(f"\n===== {path.name} =====")
        try:
            response = describe_painting(client, path)
        except (FileNotFoundError, ValueError) as e:
            print(f"Can't use that image: {e}")
            continue
        except anthropic.AuthenticationError:
            print("The API key was rejected. Check ANTHROPIC_API_KEY.")
            return
        except anthropic.APIConnectionError:
            print("Couldn't reach the Claude API. Check your internet connection.")
            return

        usage = response.usage
        cost = estimate_cost(usage.input_tokens, usage.output_tokens)
        total += cost
        described += 1
        print_description(response, cost)

    if described:
        print(f"\nTotal for {described} paintings: ${total:.4f}")
        print(f"Average per painting:   ${total / described:.4f}")


if __name__ == "__main__":
    main()
