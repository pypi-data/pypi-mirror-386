from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Generic,
    Literal,
    TypeAlias,
    TypeVar,
)

from pydantic import BaseModel, PrivateAttr, TypeAdapter

from grasp_agents.tracing_decorators import tool

from ..generics_utils import AutoInstanceAttributesMixin

if TYPE_CHECKING:
    from ..run_context import CtxT, RunContext
    from .events import Event
else:
    CtxT = TypeVar("CtxT")


_InT = TypeVar("_InT", bound=BaseModel)
_OutT_co = TypeVar("_OutT_co", covariant=True)


class ToolCall(BaseModel):
    id: str
    tool_name: str
    tool_arguments: str


@tool(name="tool", method_name="__call__")  # type: ignore
class BaseTool(
    AutoInstanceAttributesMixin,
    BaseModel,
    ABC,
    Generic[_InT, _OutT_co, CtxT],
):
    _generic_arg_to_instance_attr_map: ClassVar[dict[int, str]] = {
        0: "_in_type",
        1: "_out_type",
    }

    name: str
    description: str

    _in_type: type[_InT] = PrivateAttr()
    _out_type: type[_OutT_co] = PrivateAttr()

    @property
    def in_type(self) -> type[_InT]:
        return self._in_type

    @property
    def out_type(self) -> type[_OutT_co]:
        return self._out_type

    @abstractmethod
    async def run(
        self,
        inp: _InT,
        *,
        ctx: RunContext[CtxT] | None = None,
        call_id: str | None = None,
    ) -> _OutT_co:
        pass

    async def run_stream(
        self,
        inp: _InT,
        *,
        ctx: RunContext[CtxT] | None = None,
        call_id: str | None = None,
    ) -> AsyncIterator[Event[Any]]:
        from .events import ToolOutputEvent

        out = await self.run(inp, ctx=ctx, call_id=call_id)
        yield ToolOutputEvent(data=out, src_name=self.name, call_id=call_id)

    async def __call__(
        self,
        *,
        ctx: RunContext[CtxT] | None = None,
        call_id: str | None = None,
        **kwargs: Any,
    ) -> _OutT_co:
        # NOTE: validation is probably redundant here when tool inputs have been
        # validated by the LLM already
        input_args = TypeAdapter(self._in_type).validate_python(kwargs)
        output = await self.run(input_args, ctx=ctx, call_id=call_id)

        return TypeAdapter(self._out_type).validate_python(output)


class NamedToolChoice(BaseModel):
    name: str


ToolChoice: TypeAlias = Literal["none", "auto", "required"] | NamedToolChoice
