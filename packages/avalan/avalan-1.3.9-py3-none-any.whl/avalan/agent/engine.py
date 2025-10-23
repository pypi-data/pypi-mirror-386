from ..entities import (
    EngineMessage,
    EngineUri,
    GenerationSettings,
    Input,
    Message,
    MessageRole,
    Modality,
    Operation,
    OperationParameters,
    OperationTextParameters,
)
from ..event import Event, EventType
from ..event.manager import EventManager
from ..memory.manager import MemoryManager
from ..model.call import ModelCall, ModelCallContext
from ..model.engine import Engine
from ..model.manager import ModelManager
from ..model.response.text import TextGenerationResponse
from ..tool.manager import ToolManager

from abc import ABC, abstractmethod
from dataclasses import Field, fields, replace
from typing import Any
from uuid import UUID, uuid4


class EngineAgent(ABC):
    _GENERATION_FIELDS: dict[str, Field[Any]] = {
        field.name: field for field in fields(GenerationSettings)
    }
    _id: UUID
    _name: str | None
    _model: Engine
    _memory: MemoryManager
    _tool: ToolManager
    _event_manager: EventManager
    _model_manager: ModelManager
    _engine_uri: EngineUri
    _last_output: TextGenerationResponse | None = None
    _last_prompt: tuple[Input, str | None, str | None] | None = None

    @abstractmethod
    def _prepare_call(self, context: ModelCallContext) -> Any:
        raise NotImplementedError()

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def memory(self) -> MemoryManager:
        return self._memory

    @property
    def engine(self) -> Engine:
        return self._model

    @property
    def engine_uri(self) -> EngineUri:
        return self._engine_uri

    @property
    def output(self) -> TextGenerationResponse | None:
        return self._last_output

    async def input_token_count(self) -> int | None:
        if not self._last_prompt:
            return None
        await self._event_manager.trigger(
            Event(
                type=EventType.INPUT_TOKEN_COUNT_BEFORE,
                payload={
                    "model_type": self._model.model_type,
                    "model_id": self._model.model_id,
                },
            )
        )
        count = self._model.input_token_count(
            self._last_prompt[0],
            system_prompt=self._last_prompt[1],
            developer_prompt=self._last_prompt[2],
        )
        await self._event_manager.trigger(
            Event(
                type=EventType.INPUT_TOKEN_COUNT_AFTER,
                payload={
                    "model_type": self._model.model_type,
                    "model_id": self._model.model_id,
                    "count": count,
                },
            )
        )
        return count

    def __init__(
        self,
        model: Engine,
        memory: MemoryManager,
        tool: ToolManager,
        event_manager: EventManager,
        model_manager: ModelManager,
        engine_uri: EngineUri,
        *args,
        name: str | None = None,
        id: UUID | None = None,
    ):
        self._id = id or uuid4()
        self._name = name
        self._model = model
        self._memory = memory
        self._tool = tool
        self._event_manager = event_manager
        self._model_manager = model_manager
        self._engine_uri = engine_uri

    async def __call__(
        self,
        context: ModelCallContext,
    ) -> TextGenerationResponse | str:
        if context.parent and context.root_parent is None:
            root_parent_context = context.parent.root_parent or context.parent
            context = replace(context, root_parent=root_parent_context)

        await self._event_manager.trigger(
            Event(
                type=EventType.ENGINE_AGENT_CALL_BEFORE,
                payload={
                    "model_type": self._model.model_type,
                    "model_id": self._model.model_id,
                    "context": context,
                },
            )
        )

        await self._event_manager.trigger(
            Event(
                type=EventType.CALL_PREPARE_BEFORE,
                payload={
                    "model_type": self._model.model_type,
                    "model_id": self._model.model_id,
                    "specification": context.specification,
                    "input": context.input,
                    "context": context,
                },
            )
        )
        run_args = self._prepare_call(context)
        await self._event_manager.trigger(
            Event(
                type=EventType.CALL_PREPARE_AFTER,
                payload={
                    "model_type": self._model.model_type,
                    "model_id": self._model.model_id,
                    "specification": context.specification,
                    "input": context.input,
                    "context": context,
                },
            )
        )
        output = await self._run(context, context.input, **run_args)
        await self._event_manager.trigger(
            Event(
                type=EventType.ENGINE_AGENT_CALL_AFTER,
                payload={
                    "model_type": self._model.model_type,
                    "model_id": self._model.model_id,
                    "context": context,
                    "result": output,
                },
            )
        )
        return output

    async def _run(
        self,
        context: ModelCallContext,
        input: Input,
        *args,
        settings: GenerationSettings | None = None,
        system_prompt: str | None = None,
        developer_prompt: str | None = None,
        skip_special_tokens=True,
        **kwargs,
    ) -> TextGenerationResponse:
        input_value = input
        generation_fields = self._GENERATION_FIELDS
        uri_defaults = {
            k: v
            for k, v in self._engine_uri.params.items()
            if k in generation_fields
        }
        if settings:
            settings_dict = {
                name: getattr(settings, name) for name in generation_fields
            }
            field_defaults = {
                name: field.default
                for name, field in generation_fields.items()
            }
            for key, value in uri_defaults.items():
                if settings_dict.get(key) == field_defaults[key]:
                    settings_dict[key] = value
        else:
            settings_dict = {**uri_defaults}
            settings_dict.setdefault("temperature", None)
            settings_dict.setdefault("do_sample", False)
        settings_dict.update(kwargs)
        settings = GenerationSettings(**settings_dict)
        assert settings

        # Prepare memory
        assert (
            not self._memory.has_recent_message
            or self._memory.recent_message is not None
        ) and (
            not self._memory.has_permanent_message
            or self._memory.permanent_message is not None
        )

        # Should always be stored, with or without memory
        self._last_prompt = (input_value, system_prompt, developer_prompt)

        if isinstance(input_value, Message):
            input_value = [input_value]

        # Transform input (by adding memory, if necessary)
        if (
            self._memory.has_permanent_message
            or self._memory.has_recent_message
        ) and isinstance(input_value, list):
            # Handle last message if not already consumed

            previous_message: Message | None = None
            previous_output = self._last_output
            if previous_output and isinstance(
                previous_output, TextGenerationResponse
            ):
                previous_message = Message(
                    role=MessageRole.ASSISTANT,
                    content=await previous_output.to_str(),
                )

                # Append messages

                if previous_message:
                    await self.sync_message(previous_message)

            for current_message in input_value:
                await self.sync_message(current_message)

            # Make recent memory the new model input
            input_value = [rm.message for rm in self._memory.recent_messages]

        # Have model generate output from input

        operation = Operation(
            generation_settings=settings,
            input=input_value,
            modality=Modality.TEXT_GENERATION,
            parameters=OperationParameters(
                text=OperationTextParameters(
                    system_prompt=system_prompt,
                    developer_prompt=developer_prompt,
                    skip_special_tokens=skip_special_tokens,
                )
            ),
            requires_input=True,
        )

        await self._event_manager.trigger(
            Event(
                type=EventType.MODEL_EXECUTE_BEFORE,
                payload={
                    "model_type": self._model.model_type,
                    "model_id": self._model.model_id,
                    "input": input_value,
                    "system_prompt": system_prompt,
                    "developer_prompt": developer_prompt,
                    "settings": settings,
                    "context": context,
                },
            )
        )
        model_task = ModelCall(
            engine_uri=self._engine_uri,
            model=self._model,
            operation=operation,
            tool=self._tool,
            context=context,
        )
        output = await self._model_manager(model_task)
        await self._event_manager.trigger(
            Event(
                type=EventType.MODEL_EXECUTE_AFTER,
                payload={
                    "model_type": self._model.model_type,
                    "model_id": self._model.model_id,
                    "input": input_value,
                    "system_prompt": system_prompt,
                    "developer_prompt": developer_prompt,
                    "settings": settings,
                    "context": context,
                },
            )
        )

        # Update memory
        if self._memory.has_recent_message:
            self._last_output = output

        return output

    async def sync_messages(self) -> None:
        if self._last_output and (
            self._memory.has_permanent_message
            or self._memory.has_recent_message
        ):
            previous_message = Message(
                role=MessageRole.ASSISTANT,
                content=await self._last_output.to_str(),
            )
            await self.sync_message(previous_message)

    async def sync_message(self, message: Message) -> None:
        await self._event_manager.trigger(
            Event(
                type=EventType.MEMORY_APPEND_BEFORE,
                payload={
                    "model_type": self._model.model_type,
                    "model_id": self._model.model_id,
                    "message": message,
                    "participant_id": getattr(
                        self._memory, "participant_id", None
                    ),
                    "session_id": (
                        getattr(self._memory, "permanent_message", None)
                        and getattr(
                            self._memory.permanent_message,
                            "session_id",
                            None,
                        )
                    ),
                },
            )
        )
        await self._memory.append_message(
            EngineMessage(
                agent_id=self._id,
                model_id=self._model.model_id,
                message=message,
            )
        )
        await self._event_manager.trigger(
            Event(
                type=EventType.MEMORY_APPEND_AFTER,
                payload={
                    "model_type": self._model.model_type,
                    "model_id": self._model.model_id,
                    "message": message,
                    "participant_id": getattr(
                        self._memory, "participant_id", None
                    ),
                    "session_id": (
                        getattr(self._memory, "permanent_message", None)
                        and getattr(
                            self._memory.permanent_message,
                            "session_id",
                            None,
                        )
                    ),
                },
            )
        )
