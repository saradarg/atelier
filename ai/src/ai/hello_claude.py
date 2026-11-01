"""Day 7: my first call to the Claude API."""

import os

import anthropic

MODEL = "claude-opus-5-5"
PROMPT = (
    "I'm an artist who works in watercolor, colored pencil and pastel. "
    "Say hello in one sentence, then suggest three titles for a watercolor "
    "of a harbor at dusk."
)


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY isn't set. Set it, then open a NEW terminal.")
        return

    client = anthropic.Anthropic()

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": PROMPT}],
        )
    except anthropic.AuthenticationError:
        print("The API key was rejected. Check ANTHROPIC_API_KEY.")
        return
    except anthropic.APIConnectionError:
        print("Couldn't reach the Claude API. Check your internet connection.")
        return

    if response.stop_reason == "refusal":
        print("Claude declined this request.")
        return

    for block in response.content:
        if block.type == "text":
            print(block.text)

    usage = response.usage
    print(f"\n[{MODEL}: {usage.input_tokens} tokens in, {usage.output_tokens} out]")


if __name__ == "__main__":
    main()
