from ....cli import CommandAbortException
from ....entities import (
    Input,
    Message,
    MessageRole,
    MessageToolCall,
    Token,
    TokenDetail,
    ToolCall,
    ToolCallContext,
    ToolCallError,
    ToolCallResult,
    ToolCallToken,
)
from ....event import Event, EventType
from ....event.manager import EventManager
from ....model.call import ModelCallContext
from ....model.response.parsers.tool import ToolCallResponseParser
from ....model.response.text import TextGenerationResponse
from ....tool.manager import ToolManager
from ... import AgentOperation
from ...engine import EngineAgent

from base64 import b64encode
from dataclasses import asdict, is_dataclass
from inspect import iscoroutine
from json import dumps
from queue import Queue
from time import perf_counter
from typing import Any, AsyncIterator, Callable
from uuid import UUID


class OrchestratorResponse(AsyncIterator[Token | TokenDetail | Event]):
    """Async iterator handling tool execution during streaming."""

    _response: TextGenerationResponse
    _response_iterator: AsyncIterator[Token | TokenDetail | Event] | None
    _engine_agent: EngineAgent
    _operation: AgentOperation
    _engine_args: dict
    _event_manager: EventManager | None
    _tool_manager: ToolManager | None
    _calls: Queue[ToolCall]
    _tool_call_events: Queue[Event]
    _tool_process_events: Queue[Event]
    _tool_result_events: Queue[Event]
    _input: Input
    _context: ModelCallContext
    _tool_context: ToolCallContext | None
    _call_history: list[ToolCall]
    _agent_id: UUID | None
    _participant_id: UUID | None
    _session_id: UUID | None
    _parser_queue: Queue[Token | TokenDetail | Event] | None
    _tool_parser: ToolCallResponseParser | None

    def __init__(
        self,
        input: Input,
        response: TextGenerationResponse,
        engine_agent: EngineAgent,
        operation: AgentOperation,
        engine_args: dict,
        context: ModelCallContext,
        event_manager: EventManager | None = None,
        tool: ToolManager | None = None,
        *,
        agent_id: UUID | None = None,
        participant_id: UUID | None = None,
        session_id: UUID | None = None,
        tool_confirm: Callable[[ToolCall], str | None] | None = None,
        enable_tool_parsing: bool = True,
    ) -> None:
        assert input and response and engine_agent and operation
        self._input = input
        self._response = response
        self._engine_agent = engine_agent
        self._operation = operation
        self._engine_args = engine_args
        self._event_manager = event_manager
        self._tool_manager = None if tool and tool.is_empty else tool
        self._context = context
        self._finished = False
        self._step = 0
        self._tool_context = None
        self._call_history = []
        self._agent_id = agent_id
        self._participant_id = participant_id
        self._session_id = session_id
        self._tool_confirm = tool_confirm
        self._tool_confirm_all = False
        self._parser_queue = Queue()
        self._tool_parser = (
            ToolCallResponseParser(self._tool_manager, self._event_manager)
            if enable_tool_parsing and self._tool_manager
            else None
        )

    @property
    def input_token_count(self) -> int:
        return self._response.input_token_count

    @property
    def output_token_count(self) -> int:
        return self._response.output_token_count

    @property
    def can_think(self) -> bool:
        return self._response.can_think

    @property
    def is_thinking(self) -> bool:
        return self._response.is_thinking

    def set_thinking(self, thinking: bool) -> None:
        self._response.set_thinking(thinking)

    async def to_str(self) -> str:
        output = await self._react(self._response)
        return output

    async def to_json(self) -> str:
        await self._react(self._response)
        return await self._response.to_json()

    async def to(self, entity_class: type) -> Any:
        await self._react(self._response)
        return await self._response.to(entity_class)

    def __aiter__(self) -> "OrchestratorResponse":
        if self._event_manager:
            self._response.add_done_callback(self._on_consumed)
        self._response_iterator = self._response.__aiter__()
        self._calls = Queue()
        self._parser_queue = Queue()
        self._tool_context = ToolCallContext(
            input=self._input,
            agent_id=self._agent_id,
            participant_id=self._participant_id,
            session_id=self._session_id,
            calls=list(self._call_history),
        )
        self._tool_call_events = Queue()
        self._tool_process_events = Queue()
        self._tool_result_events = Queue()
        self._step = 0
        return self

    async def __anext__(self) -> Token | TokenDetail | Event:
        assert self._response_iterator

        if not self._parser_queue.empty():
            return self._parser_queue.get()

        if not self._tool_process_events.empty():
            event = self._tool_process_events.get()
            assert event.type == EventType.TOOL_PROCESS
            self._tool_call_events.put(event)
            return event

        if not self._tool_call_events.empty():
            event = self._tool_call_events.get()
            assert event.type == EventType.TOOL_PROCESS
            await self._event_manager.trigger(event)

            calls: list[ToolCall] = event.payload or []
            if calls:
                for call in calls:
                    assert isinstance(call, ToolCall)
                    self._calls.put(call)

        if not self._calls.empty():
            call = self._calls.get()

            if self._tool_confirm and not self._tool_confirm_all:
                action = self._tool_confirm(call)
                if iscoroutine(action):
                    action = await action
                if action == "a":
                    self._tool_confirm_all = True
                elif action != "y":
                    raise CommandAbortException()

            start = perf_counter()
            execute_event = Event(
                type=EventType.TOOL_EXECUTE,
                payload={"call": call},
                started=start,
            )
            if self._event_manager:
                await self._event_manager.trigger(execute_event)

            context = ToolCallContext(
                input=self._tool_context.input,
                agent_id=self._agent_id,
                participant_id=self._participant_id,
                session_id=self._session_id,
                calls=list(self._call_history),
            )

            result = (
                await self._tool_manager(call, context)
                if self._tool_manager
                else None
            )

            self._call_history.append(call)
            self._tool_context = context

            end = perf_counter()
            result_event = Event(
                type=EventType.TOOL_RESULT,
                payload={"result": result},
                started=start,
                finished=end,
                elapsed=end - start,
            )
            if self._event_manager:
                await self._event_manager.trigger(result_event)

            self._tool_result_events.put(result_event)

            return result_event

        # Wait until all results are collected
        if (
            self._tool_call_events.empty()
            and self._calls.empty()
            and not self._tool_result_events.empty()
        ):
            result_events: list[Event] = []
            while not self._tool_result_events.empty():
                result_event = self._tool_result_events.get()
                result_events.append(result_event)

            tool_messages = []
            for e in result_events:
                tool_result = e.payload["result"]
                tool_output = (
                    tool_result.message
                    if isinstance(tool_result, ToolCallError)
                    else tool_result.result
                )
                tool_messages.append(
                    Message(
                        role=MessageRole.ASSISTANT,
                        tool_calls=[
                            MessageToolCall(
                                id=tool_result.call.id,
                                name=tool_result.name,
                                arguments=tool_result.arguments,
                            )
                        ],
                    )
                )
                tool_result_output = dumps(
                    (
                        asdict(tool_output)
                        if is_dataclass(tool_output)
                        else tool_output
                    ),
                    default=lambda o: (
                        b64encode(o).decode()
                        if isinstance(o, (bytes, bytearray))
                        else str(o)
                    ),
                )
                tool_messages.append(
                    Message(
                        role=MessageRole.TOOL,
                        name=tool_result.name,
                        arguments=tool_result.arguments,
                        content=tool_result_output,
                        tool_call_result=(
                            tool_result
                            if isinstance(tool_result, ToolCallResult)
                            else None
                        ),
                        tool_call_error=(
                            tool_result
                            if isinstance(tool_result, ToolCallError)
                            else None
                        ),
                    )
                )

            assert self._input and (
                (
                    isinstance(self._input, list)
                    and isinstance(self._input[0], Message)
                )
                or isinstance(self._input, Message)
            )

            messages = list(
                self._input if isinstance(self._input, list) else [self._input]
            )

            messages.extend(tool_messages)

            event_tool_model_run = Event(
                type=EventType.TOOL_MODEL_RUN,
                payload={
                    "model_id": self._engine_agent.engine.model_id,
                    "messages": messages,
                    "engine_args": self._engine_args,
                },
            )
            await self._event_manager.trigger(event_tool_model_run)

            context = self._make_child_context(messages)
            inner_response = await self._engine_agent(context)
            assert inner_response

            self._response = inner_response
            self.__aiter__()

            event_tool_model_response = Event(
                type=EventType.TOOL_MODEL_RESPONSE,
                payload={
                    "response": inner_response,
                    "model_id": self._engine_agent.engine.model_id,
                    "messages": messages,
                    "engine_args": self._engine_args,
                },
            )
            await self._event_manager.trigger(event_tool_model_response)

            return event_tool_model_response

        try:
            token = await self._response_iterator.__anext__()
            if isinstance(token, ToolCallToken) and token.call:
                event = Event(
                    type=EventType.TOOL_PROCESS,
                    payload=[token.call],
                    started=perf_counter(),
                )
                self._tool_process_events.put(event)
        except StopAsyncIteration:
            if self._tool_parser:
                for item in await self._tool_parser.flush():
                    if isinstance(item, Event):
                        self._tool_process_events.put(item)
                    else:
                        self._parser_queue.put(item)
                if not self._parser_queue.empty():
                    return self._parser_queue.get()
            if self._event_manager and not self._finished:
                self._finished = True
                await self._event_manager.trigger(Event(type=EventType.END))

            raise

        return await self._emit(token)

    async def _react(
        self, response: TextGenerationResponse, output: str | None = None
    ) -> str:
        if self._event_manager:
            response.add_done_callback(self._on_consumed)

        text = output or await response.to_str()

        if self._tool_context is None:
            self._tool_context = ToolCallContext(
                input=self._input,
                agent_id=self._agent_id,
                participant_id=self._participant_id,
                session_id=self._session_id,
                calls=list(self._call_history),
            )

        if not self._tool_manager:
            self._response = response
            return text

        current_response = response
        previous_text = text
        delta = text
        while True:
            if self._event_manager:
                await self._event_manager.trigger(
                    Event(type=EventType.TOOL_DETECT)
                )

            calls = (
                self._tool_manager.get_calls(delta)
                if self._tool_manager
                else None
            )
            if not calls:
                break

            results: list[ToolCallResult | ToolCallError] = []
            for call in calls:
                if self._event_manager:
                    start = perf_counter()
                    execute_event = Event(
                        type=EventType.TOOL_EXECUTE,
                        payload={"call": call},
                        started=start,
                    )
                    await self._event_manager.trigger(execute_event)

                context = ToolCallContext(
                    input=self._tool_context.input,
                    agent_id=self._agent_id,
                    participant_id=self._participant_id,
                    session_id=self._session_id,
                    calls=list(self._call_history),
                )

                result = (
                    await self._tool_manager(call, context)
                    if self._tool_manager
                    else None
                )
                self._call_history.append(call)
                self._tool_context = context
                results.append(result)

                if self._event_manager:
                    end = perf_counter()
                    result_event = Event(
                        type=EventType.TOOL_RESULT,
                        payload={"result": result},
                        started=start,
                        finished=end,
                        elapsed=end - start,
                    )
                    await self._event_manager.trigger(result_event)

            current_response = await self._react_process(delta, results)
            new_text = await current_response.to_str()
            delta = new_text.replace(previous_text, "")
            previous_text = new_text

        self._response = current_response
        return delta

    async def _react_process(
        self, output: str, results: list[ToolCallResult | ToolCallError]
    ) -> TextGenerationResponse:
        tool_messages = [
            Message(
                role=MessageRole.TOOL,
                name=result.name,
                arguments=result.arguments,
                content=(
                    result.message
                    if isinstance(result, ToolCallError)
                    else (
                        result.result
                        if isinstance(result.result, str)
                        else (
                            dumps(result.result)
                            if result.result is not None
                            else ""
                        )
                    )
                ),
                tool_call_result=(
                    result if isinstance(result, ToolCallResult) else None
                ),
                tool_call_error=(
                    result if isinstance(result, ToolCallError) else None
                ),
            )
            for result in results
        ]

        assert self._input and (
            (
                isinstance(self._input, list)
                and isinstance(self._input[0], Message)
            )
            or isinstance(self._input, Message)
        )

        messages = list(
            self._input if isinstance(self._input, list) else [self._input]
        )
        messages.extend(tool_messages)

        self._input = messages
        self._tool_context = ToolCallContext(
            input=self._input,
            agent_id=self._agent_id,
            participant_id=self._participant_id,
            session_id=self._session_id,
            calls=list(self._call_history),
        )

        event_tool_model_run = Event(
            type=EventType.TOOL_MODEL_RUN,
            payload={
                "model_id": self._engine_agent.engine.model_id,
                "messages": messages,
                "engine_args": self._engine_args,
            },
        )
        await self._event_manager.trigger(event_tool_model_run)

        context = self._make_child_context(messages)
        response = await self._engine_agent(context)
        assert response
        return response

    async def _emit(
        self, item: Token | TokenDetail | Event | str
    ) -> Token | TokenDetail | Event:
        if self._event_manager and not isinstance(item, Event):
            token_str = item.token if hasattr(item, "token") else str(item)
            token_id = getattr(item, "id", None)
            tokenizer = (
                self._engine_agent.engine.tokenizer
                if self._engine_agent.engine
                else None
            )
            if token_id is None and tokenizer:
                ids = tokenizer.encode(token_str, add_special_tokens=False)
                token_id = ids[0] if ids else None

            await self._event_manager.trigger(
                Event(
                    type=EventType.TOKEN_GENERATED,
                    payload={
                        "token_id": token_id,
                        "model_id": self._engine_agent.engine.model_id,
                        "token": token_str,
                        "token_type": type(item).__qualname__,
                        "step": self._step,
                    },
                )
            )

        self._step += 1

        if isinstance(item, Event):
            if item.type == EventType.TOOL_PROCESS:
                self._tool_process_events.put(item)
                return await self.__anext__()
            return item

        if isinstance(item, str) and self._tool_parser:
            items = await self._tool_parser.push(item)
            if not items:
                return await self.__anext__()
        else:
            items = [item]

        for it in items:
            if isinstance(it, Event):
                if it.type == EventType.TOOL_PROCESS:
                    self._tool_process_events.put(it)
                else:
                    self._parser_queue.put(it)
            else:
                self._parser_queue.put(it)

        return self._parser_queue.get()

    async def _on_consumed(self) -> None:
        assert self._event_manager
        await self._event_manager.trigger(Event(type=EventType.STREAM_END))

    def _make_child_context(self, messages: Input) -> ModelCallContext:
        parent_context = self._context
        root_parent = (
            parent_context.root_parent or parent_context
            if parent_context
            else None
        )
        context = ModelCallContext(
            specification=self._operation.specification,
            input=messages,
            engine_args=dict(self._engine_args),
            parent=parent_context,
            root_parent=root_parent,
            agent_id=(
                parent_context.agent_id if parent_context else self._agent_id
            ),
            participant_id=(
                parent_context.participant_id
                if parent_context
                else self._participant_id
            ),
            session_id=(
                parent_context.session_id
                if parent_context
                else self._session_id
            ),
        )
        self._context = context
        return context
