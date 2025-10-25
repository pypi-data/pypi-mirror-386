from ...entities import (
    EngineMessage as EngineMessage,
)
from ...entities import (
    Input,
    Message,
    MessageContentText,
    MessageRole,
)
from ...entities import Modality as Modality
from ...event import Event, EventType
from ...event.manager import EventManager
from ...memory.manager import MemoryManager
from ...model.call import ModelCallContext
from ...model.engine import Engine
from ...model.manager import ModelManager
from ...tool.manager import ToolManager
from .. import (
    AgentOperation,
    EngineEnvironment,
    InputType,
    NoOperationAvailableException,
    Specification,
)
from ..engine import EngineAgent
from ..renderer import Renderer, TemplateEngineAgent
from .response.orchestrator_response import OrchestratorResponse

from contextlib import ExitStack
from dataclasses import asdict
from json import dumps
from logging import Logger
from time import perf_counter
from typing import Any
from uuid import UUID, uuid4


class Orchestrator:
    _id: UUID
    _name: str | None
    _operations: list[AgentOperation]
    _renderer: Renderer
    _total_operations: int
    _logger: Logger
    _model_manager: ModelManager
    _memory: MemoryManager
    _tool: ToolManager
    _event_manager: EventManager
    _engine_agents: dict[EngineEnvironment, EngineAgent] = {}
    _engines_stack: ExitStack = ExitStack()
    _operation_step: int | None = None
    _model_ids: set[str] = set()
    _call_options: dict | None = None
    _last_engine_agent: EngineAgent | None = None
    _exit_memory: bool = True
    _user: str | None
    _user_template: str | None

    def __init__(
        self,
        logger: Logger,
        model_manager: ModelManager,
        memory: MemoryManager,
        tool: ToolManager,
        event_manager: EventManager,
        operations: AgentOperation | list[AgentOperation],
        *,
        call_options: dict | None = None,
        exit_memory: bool = True,
        id: UUID | None = None,
        name: str | None = None,
        renderer: Renderer | None = None,
        user: str | None = None,
        user_template: str | None = None,
    ):
        assert not (user and user_template)
        self._logger = logger
        self._model_manager = model_manager
        self._memory = memory
        self._tool = tool
        self._event_manager = event_manager
        self._operations = (
            [operations]
            if isinstance(operations, AgentOperation)
            else operations
        )
        self._id = id or uuid4()
        self._exit_memory = exit_memory
        self._name = name
        self._renderer = renderer or Renderer()
        self._total_operations = len(self._operations)
        self._call_options = call_options
        self._user = user
        self._user_template = user_template

    @property
    def engine_agent(self) -> EngineAgent | None:
        return self._last_engine_agent

    @property
    def engine(self) -> Engine | None:
        return (
            self._last_engine_agent.engine if self._last_engine_agent else None
        )

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def input_token_count(self) -> int | None:
        return (
            self._last_engine_agent.input_token_count
            if self._last_engine_agent
            else None
        )

    @property
    def is_finished(self) -> bool:
        return (
            self._operation_step is not None
            and self._operation_step == self._total_operations - 1
        )

    @property
    def memory(self) -> MemoryManager:
        return self._memory

    @property
    def model_ids(self) -> set[str]:
        return self._model_ids

    @property
    def name(self) -> str | None:
        return self._name

    @property
    def operations(self) -> list[AgentOperation]:
        return self._operations

    @property
    def tool(self) -> ToolManager:
        return self._tool

    @property
    def event_manager(self) -> EventManager:
        return self._event_manager

    @property
    def renderer(self) -> Renderer:
        """Return the renderer used by the orchestrator."""
        return self._renderer

    async def __call__(self, input: Input, **kwargs) -> OrchestratorResponse:
        tool_confirm = kwargs.pop("tool_confirm", None)
        if self.is_finished:
            self._operation_step = 0

        # Pick next operation step
        operation_step = (
            self._operation_step + 1
            if self._operation_step
            and self._operation_step < self._total_operations
            else 0 if not self._operation_step else None
        )
        self._operation_step = operation_step
        if self._operation_step is None:
            raise NoOperationAvailableException()

        # Load engine agent
        operation = self._operations[self._operation_step]
        environment_hash = dumps(asdict(operation.environment))
        assert self._engine_agents and environment_hash in self._engine_agents
        engine_agent = self._engine_agents[environment_hash]

        # Adapt tool manager
        if (
            engine_agent.engine.tokenizer
            and engine_agent.engine.tokenizer.eos_token
        ):
            self._tool.set_eos_token(engine_agent.engine.tokenizer.eos_token)

        await self._event_manager.trigger(
            Event(type=EventType.START, payload={"step": self._operation_step})
        )

        messages = self._input_messages(operation.specification, input)

        participant_id = getattr(self._memory, "participant_id", None)
        session_id = (
            self._memory.permanent_message.session_id
            if self._memory.permanent_message
            else None
        )

        # Execute operation
        engine_args = {**(self._call_options or {}), **kwargs}
        start = perf_counter()
        await self._event_manager.trigger(
            Event(
                type=EventType.ENGINE_RUN_BEFORE,
                payload={
                    "input": messages,
                    "specification": operation.specification,
                },
                started=start,
            )
        )

        self._logger.info(
            "Orchestrator calling engine agent %s", str(engine_agent)
        )
        context = ModelCallContext(
            specification=operation.specification,
            input=messages,
            engine_args=dict(engine_args),
            agent_id=self._id,
            participant_id=participant_id,
            session_id=session_id,
        )
        result = await engine_agent(context)
        self._logger.info(
            "Engine agent %s responded to orchestrator", str(engine_agent)
        )

        end = perf_counter()
        await self._event_manager.trigger(
            Event(
                type=EventType.ENGINE_RUN_AFTER,
                payload={
                    "result": result,
                    "input": messages,
                    "specification": operation.specification,
                    "context": context,
                },
                started=start,
                finished=end,
                elapsed=end - start,
            )
        )

        self._last_engine_agent = engine_agent

        return OrchestratorResponse(
            messages,
            result,
            engine_agent,
            operation,
            engine_args,
            context,
            event_manager=self._event_manager,
            tool=self._tool,
            tool_confirm=tool_confirm,
            agent_id=self._id,
            participant_id=participant_id,
            session_id=session_id,
        )

    async def __aenter__(self):
        first_agent: TemplateEngineAgent | None = None
        model_ids: list[str] = []
        for operation in self._operations:
            # Load engine with environment
            environment = operation.environment
            environment_hash = dumps(asdict(environment))
            if environment_hash not in self._engine_agents:
                model_ids.append(environment.engine_uri.model_id)
                engine = self._model_manager.load_engine(
                    environment.engine_uri,
                    environment.settings,
                    operation.modality,
                )
                if not engine:
                    raise NotImplementedError()

                self._engines_stack.enter_context(engine)
                agent = TemplateEngineAgent(
                    engine,
                    self._memory,
                    self._tool,
                    self._event_manager,
                    self._model_manager,
                    self._renderer,
                    environment.engine_uri,
                    name=self._name,
                    id=self._id,
                )
                self._engine_agents[environment_hash] = agent
                if not first_agent:
                    first_agent = agent

        self._last_engine_agent = first_agent
        self._model_ids = set(model_ids)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any | None,
    ):
        await self.sync_messages()

        if self._exit_memory:
            self._memory.__exit__(exc_type, exc_value, traceback)

        return self._engines_stack.__exit__(exc_type, exc_value, traceback)

    async def sync_messages(self) -> None:
        if self._last_engine_agent:
            await self._last_engine_agent.sync_messages()

    def _input_messages(
        self, specification: Specification, input: Input
    ) -> Message | list[Message]:
        input_type = specification.input_type
        assert (
            input_type != InputType.TEXT
            or isinstance(input, str)
            or isinstance(input, Message)
            or isinstance(input, list)
        )

        if input_type == InputType.TEXT and isinstance(input, str):
            input = Message(role=MessageRole.USER, content=input)

        if self._user_template or self._user:
            message = (
                input
                if isinstance(input, Message)
                else (
                    input[-1]
                    if (
                        isinstance(input, list)
                        and input
                        and isinstance(input[-1], Message)
                    )
                    else None
                )
            )

            if message and (
                isinstance(message.content, str)
                or isinstance(message.content, MessageContentText)
            ):
                render_vars = (
                    specification.template_vars.copy()
                    if specification.template_vars
                    else {}
                )
                if (
                    specification.settings
                    and specification.settings.template_vars
                ):
                    render_vars.update(specification.settings.template_vars)
                message_content = (
                    message.content.text
                    if isinstance(message.content, MessageContentText)
                    else message.content
                )
                render_vars.update({"input": message_content})
                content = (
                    self._renderer(self._user_template, **render_vars)
                    if self._user_template
                    else self._renderer.from_string(
                        self._user, template_vars=render_vars
                    )
                )
                message = Message(role=message.role, content=content)

                if isinstance(input, list):
                    input[-1] = message
                else:
                    input = message

        return input
