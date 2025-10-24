import json
from collections.abc import AsyncGenerator, Sequence
from dataclasses import dataclass

from flexai.capability import Capability
from flexai.message import AIMessage, Message, MessageContent, TextBlock, ToolCall


@dataclass
class LimitToolUse(Capability):
    """Force an agent to stop if there are too many tool use."""

    # The maximum number of tool uses allowed.
    max_tool_uses: int

    def is_tool_call(self, entry):
        return isinstance(entry, ToolCall) or (
            isinstance(entry, dict) and entry["type"] == "tool_use"
        )

    async def modify_response(
        self, messages: list[Message], response: AIMessage
    ) -> AsyncGenerator[MessageContent | AIMessage, None]:
        # There's nothing to modify
        if not (
            isinstance(response.content, Sequence)
            and not isinstance(response.content, str)
        ):
            yield response
            return

        # Initial: Number of tool uses that this current response requests.
        total_tool_uses = len(
            [entry for entry in response.content if self.is_tool_call(entry)]
        )

        for message in messages:
            try:
                if not isinstance(message.content, str):
                    raise TypeError("Content is not a string")
                content = json.loads(message.content)
            except Exception:
                content = message.content

            if not (isinstance(content, Sequence) and not isinstance(content, str)):
                continue

            # For each past message, add the number of tool uses it suggested to our total count.
            for entry in content:
                if self.is_tool_call(entry):
                    total_tool_uses += 1

        # If the total tool use count, including this response, is too much, we can't use one more
        if total_tool_uses > self.max_tool_uses:
            response.content = [
                TextBlock(
                    text=f"Exceeded tool usage limit: {self.max_tool_uses}",
                ),
            ]

        yield response
