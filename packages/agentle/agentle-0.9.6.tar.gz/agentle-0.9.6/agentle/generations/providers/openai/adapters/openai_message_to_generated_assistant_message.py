from __future__ import annotations

import json
from collections.abc import MutableSequence
from typing import TYPE_CHECKING, cast

import ujson
from pydantic import BaseModel
from rsb.adapters.adapter import Adapter

from agentle.generations.models.message_parts.text import TextPart
from agentle.generations.models.message_parts.tool_execution_suggestion import (
    ToolExecutionSuggestion,
)
from agentle.generations.models.messages.generated_assistant_message import (
    GeneratedAssistantMessage,
)

if TYPE_CHECKING:
    from openai.types.chat.chat_completion_message import ChatCompletionMessage
    from openai.types.chat.parsed_chat_completion import ParsedChatCompletionMessage


class OpenAIMessageToGeneratedAssistantMessageAdapter[T](
    Adapter[
        "ChatCompletionMessage | ParsedChatCompletionMessage[T]",
        GeneratedAssistantMessage[T],
    ]
):
    def adapt(
        self, _f: ChatCompletionMessage | ParsedChatCompletionMessage[T]
    ) -> GeneratedAssistantMessage[T]:
        from openai.types.chat.chat_completion_message_tool_call import (
            ChatCompletionMessageToolCall,
        )
        from openai.types.chat.parsed_chat_completion import ParsedChatCompletionMessage

        if isinstance(_f, ParsedChatCompletionMessage):
            parsed = cast(T, _f.parsed)
            if parsed is None:
                raise ValueError(
                    "Could not get parsed response schema for chat completion."
                )

            return GeneratedAssistantMessage[T](
                role="assistant",
                parts=[
                    TextPart(text=ujson.dumps(cast(BaseModel, _f.parsed).model_dump()))
                ],
                parsed=parsed,
            )

        openai_message = _f
        if openai_message.content is None:
            raise ValueError("Contents of OpenAI message are none. Coudn't proceed.")

        tool_calls: MutableSequence[ChatCompletionMessageToolCall] = (
            openai_message.tool_calls or []
        )

        tool_parts = [
            ToolExecutionSuggestion(
                tool_name=tool_call.function.name,
                args=json.loads(tool_call.function.arguments or "{}"),
            )
            for tool_call in tool_calls
        ]

        return GeneratedAssistantMessage[T](
            parts=[TextPart(text=openai_message.content)] + tool_parts,
            parsed=cast(T, None),
        )
