import time
from typing import Any, Literal, TypeAlias
from uuid import uuid4

from litellm.types.utils import ChoiceLogprobs as LiteLLMChoiceLogprobs
from openai.types.chat.chat_completion import ChoiceLogprobs as OpenAIChoiceLogprobs
from pydantic import BaseModel, Field, NonNegativeFloat, NonNegativeInt

from .message import AssistantMessage

FinishReason: TypeAlias = Literal[
    "stop", "length", "tool_calls", "content_filter", "function_call"
]


class Usage(BaseModel):
    input_tokens: NonNegativeInt = 0
    output_tokens: NonNegativeInt = 0
    reasoning_tokens: NonNegativeInt | None = None
    cached_tokens: NonNegativeInt | None = None
    cost: NonNegativeFloat | None = None

    def __add__(self, add_usage: "Usage") -> "Usage":
        input_tokens = self.input_tokens + add_usage.input_tokens
        output_tokens = self.output_tokens + add_usage.output_tokens

        if self.reasoning_tokens is not None or add_usage.reasoning_tokens is not None:
            reasoning_tokens = (self.reasoning_tokens or 0) + (
                add_usage.reasoning_tokens or 0
            )
        else:
            reasoning_tokens = None

        if self.cached_tokens is not None or add_usage.cached_tokens is not None:
            cached_tokens = (self.cached_tokens or 0) + (add_usage.cached_tokens or 0)
        else:
            cached_tokens = None

        if self.cost is not None or add_usage.cost is not None:
            cost = (self.cost or 0.0) + (add_usage.cost or 0.0)
        else:
            cost = None

        return Usage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            reasoning_tokens=reasoning_tokens,
            cached_tokens=cached_tokens,
            cost=cost,
        )


class CompletionError(BaseModel):
    message: str
    metadata: dict[str, str | None] | None = None
    code: int


class Completion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str | None
    name: str | None = None
    system_fingerprint: str | None = None
    error: CompletionError | None = None
    usage: Usage | None = None

    # Removed choices to add message directly to Completion
    message: AssistantMessage
    finish_reason: FinishReason | None
    logprobs: OpenAIChoiceLogprobs | LiteLLMChoiceLogprobs | Any | None = None
    # LiteLLM-specific fields
    provider_specific_fields: dict[str, Any] | None = None

    # LiteLLM-specific fields
    response_ms: float | None = None
    hidden_params: dict[str, Any] | None = None
