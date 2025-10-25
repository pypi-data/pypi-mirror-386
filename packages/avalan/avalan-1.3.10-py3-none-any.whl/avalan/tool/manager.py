from ..entities import (
    ToolCall,
    ToolCallContext,
    ToolCallError,
    ToolCallResult,
    ToolFilter,
    ToolFormat,
    ToolManagerSettings,
    ToolTransformer,
)
from . import Tool, ToolSet
from .parser import ToolCallParser

from collections.abc import Callable, Sequence
from contextlib import AsyncExitStack, ContextDecorator
from uuid import uuid4


class ToolManager(ContextDecorator):
    _parser: ToolCallParser
    _stack: AsyncExitStack
    _tools: dict[str, Callable] | None = None
    _toolsets: Sequence[ToolSet] | None = None

    @staticmethod
    def _matches_namespace(tool_name: str, namespace: str | None) -> bool:
        if not namespace:
            return True
        return tool_name == namespace or tool_name.startswith(f"{namespace}.")

    @classmethod
    def create_instance(
        cls,
        *,
        available_toolsets: Sequence[ToolSet] | None = None,
        enable_tools: list[str] | None = None,
        settings: ToolManagerSettings | None = None,
    ):
        parser = ToolCallParser(
            eos_token=settings.eos_token if settings else None,
            tool_format=settings.tool_format if settings else None,
        )
        return cls(
            available_toolsets=available_toolsets,
            enable_tools=enable_tools,
            parser=parser,
            settings=settings,
        )

    @property
    def is_empty(self) -> bool:
        return not bool(self._tools)

    @property
    def tools(self) -> list[Callable] | None:
        return list(self._tools.values()) if self._tools else None

    @property
    def tool_format(self) -> ToolFormat | None:
        """Return the tool format configured for this manager."""
        return self._parser.tool_format

    def json_schemas(self) -> list[dict] | None:
        schemas = []
        for toolset in self._toolsets:
            schemas.extend(toolset.json_schemas())
        return schemas

    def __init__(
        self,
        *,
        available_toolsets: Sequence[ToolSet] | None = None,
        enable_tools: list[str] | None = None,
        parser: ToolCallParser,
        settings: ToolManagerSettings | None = None,
    ):
        self._parser = parser
        self._settings = settings or ToolManagerSettings()
        self._stack = AsyncExitStack()

        enabled_toolsets = []
        if available_toolsets:
            for toolset in available_toolsets:
                if enable_tools is not None:
                    toolset = toolset.with_enabled_tools(enable_tools)
                if toolset.tools:
                    enabled_toolsets.append(toolset)

        self._tools = {}
        if enabled_toolsets:
            for i, toolset in enumerate(enabled_toolsets):
                prefix = f"{toolset.namespace}." if toolset.namespace else ""
                for tool in toolset.tools:
                    name = getattr(tool, "__name__", tool.__class__.__name__)
                    self._tools[f"{prefix}{name}"] = tool

        self._toolsets = enabled_toolsets

    def set_eos_token(self, eos_token: str) -> None:
        self._parser.set_eos_token(eos_token)

    def is_potential_tool_call(self, buffer: str, token_str: str) -> bool:
        """Proxy :meth:`ToolCallParser.is_potential_tool_call`."""
        return self._parser.is_potential_tool_call(buffer, token_str)

    def tool_call_status(
        self, buffer: str
    ) -> ToolCallParser.ToolCallBufferStatus:
        """Proxy :meth:`ToolCallParser.tool_call_status`."""
        return self._parser.tool_call_status(buffer)

    def get_calls(self, text: str) -> list[ToolCall] | None:
        return self._parser(text)

    async def __aenter__(self) -> "ToolManager":
        if self._toolsets:
            for i, toolset in enumerate(self._toolsets):
                toolset = await self._stack.enter_async_context(toolset)
                self._toolsets[i] = toolset
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: BaseException | None,
    ) -> bool:
        return await self._stack.__aexit__(exc_type, exc_value, traceback)

    async def __call__(
        self, call: ToolCall, context: ToolCallContext
    ) -> ToolCallResult | ToolCallError | None:
        """Execute a single tool call and return the result."""
        assert call

        history = context.calls or []

        if self._settings.avoid_repetition and history:
            last = history[-1]
            if last.name == call.name and last.arguments == call.arguments:
                return None

        if (
            self._settings.maximum_depth is not None
            and len(history) + 1 > self._settings.maximum_depth
        ):
            return None

        tool = self._tools.get(call.name, None) if self._tools else None

        if not tool:
            return None

        if self._settings.filters:
            for f in self._settings.filters:
                namespace = None
                func = f
                if isinstance(f, ToolFilter):
                    func = f.func
                    namespace = f.namespace
                if not self._matches_namespace(call.name, namespace):
                    continue
                modified = func(call, context)
                if modified is not None:
                    assert isinstance(modified, tuple) and len(modified) == 2
                    call, context = modified

        is_native_tool = isinstance(tool, Tool)

        try:
            result = (
                await tool(**call.arguments, context=context)
                if is_native_tool and call.arguments
                else (
                    await tool(context=context)
                    if is_native_tool
                    else (
                        await tool(*call.arguments.values())
                        if call.arguments
                        else tool()
                    )
                )
            )

            if self._settings.transformers:
                for t in self._settings.transformers:
                    namespace = None
                    func = t
                    if isinstance(t, ToolTransformer):
                        func = t.func
                        namespace = t.namespace
                    if not self._matches_namespace(call.name, namespace):
                        continue
                    transformed = func(call, context, result)
                    if transformed is not None:
                        result = transformed

            return ToolCallResult(
                id=uuid4(),
                call=call,
                name=call.name,
                arguments=call.arguments,
                result=result,
            )
        except BaseException as exc:
            return ToolCallError(
                id=uuid4(),
                call=call,
                name=call.name,
                arguments=call.arguments,
                error=exc,
                message=str(exc),
            )
