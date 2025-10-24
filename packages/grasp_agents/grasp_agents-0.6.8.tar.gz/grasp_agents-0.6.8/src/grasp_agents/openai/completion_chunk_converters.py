from typing import cast

from ..errors import CompletionError
from ..typing.completion_chunk import (
    CompletionChunk,
    CompletionChunkDelta,
    CompletionChunkDeltaToolCall,
)
from ..typing.message import Role
from . import OpenAICompletionChunk
from .completion_converters import from_api_completion_usage


def from_api_completion_chunk(
    api_completion_chunk: OpenAICompletionChunk, name: str | None = None
) -> CompletionChunk:
    if api_completion_chunk.choices is None:  # type: ignore
        raise CompletionError(
            f"Completion chunk API error: "
            f"{getattr(api_completion_chunk, 'error', None)}"
        )

    if len(api_completion_chunk.choices) > 1:
        raise CompletionError("Multiple choices are not supported")
    api_choice = api_completion_chunk.choices[0]

    # Some providers return None for the message when finish_reason is other than "stop"
    finish_reason = api_choice.finish_reason
    if api_choice.delta is None:  # type: ignore
        raise CompletionError(
            "API returned None for delta content in completion chunk "
            f"with finish_reason: {finish_reason}."
        )

    # if api_choice.delta.content is None:
    #     raise CompletionError(
    #         "API returned None for delta content in completion chunk "
    #         f"with finish_reason: {finish_reason}."
    #     )

    delta = CompletionChunkDelta(
        content=api_choice.delta.content,
        refusal=api_choice.delta.refusal,
        role=cast("Role", api_choice.delta.role),
        tool_calls=[
            CompletionChunkDeltaToolCall(
                id=tool_call.id,
                index=tool_call.index,
                tool_name=tool_call.function.name,
                tool_arguments=tool_call.function.arguments,
            )
            for tool_call in (api_choice.delta.tool_calls or [])
            if tool_call.function
        ],
    )

    usage = (
        from_api_completion_usage(api_completion_chunk.usage)
        if api_completion_chunk.usage
        else None
    )

    return CompletionChunk(
        id=api_completion_chunk.id,
        model=api_completion_chunk.model,
        name=name,
        created=api_completion_chunk.created,
        system_fingerprint=api_completion_chunk.system_fingerprint,
        delta=delta,
        finish_reason=finish_reason,
        logprobs=api_choice.logprobs,
        usage=usage,
    )
