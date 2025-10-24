from grasp_agents.errors import CompletionError
from grasp_agents.typing.completion import Usage

from ..openai.completion_converters import from_api_completion_usage
from ..typing.completion_chunk import (
    CompletionChunk,
    CompletionChunkDelta,
    CompletionChunkDeltaToolCall,
)
from . import LiteLLMCompletionChunk


def from_api_completion_chunk(
    api_completion_chunk: LiteLLMCompletionChunk, name: str | None = None
) -> CompletionChunk:
    if len(api_completion_chunk.choices) > 1:
        raise CompletionError("Multiple choices are not supported")
    api_choice = api_completion_chunk.choices[0]

    api_delta = api_choice.delta

    delta = CompletionChunkDelta(
        tool_calls=[
            CompletionChunkDeltaToolCall(
                id=tool_call.id,
                index=tool_call.index,
                tool_name=tool_call.function.name,
                tool_arguments=tool_call.function.arguments,
            )
            for tool_call in (api_delta.tool_calls or [])
            if tool_call.function
        ],
        content=api_delta.content,  # type: ignore[assignment, arg-type]
        role=api_delta.role,  # type: ignore[assignment, arg-type]
        thinking_blocks=getattr(api_delta, "thinking_blocks", None),
        annotations=getattr(api_delta, "annotations", None),
        reasoning_content=getattr(api_delta, "reasoning_content", None),
        provider_specific_fields=api_delta.provider_specific_fields,
        refusal=getattr(api_delta, "refusal", None),
    )

    usage: Usage | None = None
    api_usage = getattr(api_completion_chunk, "usage", None)
    if api_usage is not None:
        usage = from_api_completion_usage(api_usage)
        hidden_params = getattr(api_completion_chunk, "_hidden_params", {})
        usage.cost = getattr(hidden_params, "response_cost", None)

    return CompletionChunk(
        id=api_completion_chunk.id,
        model=api_completion_chunk.model,
        name=name,
        created=api_completion_chunk.created,
        system_fingerprint=api_completion_chunk.system_fingerprint,
        delta=delta,
        finish_reason=api_choice.finish_reason,  # type: ignore[assignment, arg-type]
        logprobs=getattr(api_choice, "logprobs", None),
        usage=usage,
        provider_specific_fields=api_completion_chunk.provider_specific_fields,
        hidden_params=api_completion_chunk._hidden_params,  # type: ignore[union-attr]
        response_ms=getattr(api_completion_chunk, "_response_ms", None),
    )
