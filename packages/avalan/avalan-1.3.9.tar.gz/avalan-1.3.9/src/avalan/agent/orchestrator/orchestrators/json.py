from ....agent import (
    AgentOperation,
    EngineEnvironment,
    EngineUri,
    Goal,
    OutputType,
    Role,
    Specification,
)
from ....agent.orchestrator import Orchestrator
from ....entities import Input, Modality, TransformerEngineSettings
from ....event.manager import EventManager
from ....memory.manager import MemoryManager
from ....model.manager import ModelManager
from ....tool.manager import ToolManager

from dataclasses import dataclass
from logging import Logger
from typing import Annotated, get_args, get_origin


@dataclass(frozen=True, kw_only=True, slots=True)
class Property:
    TYPE_MAP = {
        int: int.__name__,
        float: float.__name__,
        str: "string",
        bool: "boolean",
        list: "array",
        dict: "object",
        type(None): "null",
    }
    name: str
    data_type: str
    description: str | None = None


class JsonSpecification(Specification):
    def __init__(
        self, output: type | list[Property], role: str | None = None, **kwargs
    ):
        if not isinstance(output, list):
            annotations = getattr(output, "__annotations__", None)
            assert annotations

            # Read annotated properties from output_class
            properties: list[Property] = []
            for name, type_info in annotations.items():
                if get_origin(type_info) is Annotated:
                    data_class, *metadata = get_args(type_info)
                    data_type = Property.TYPE_MAP.get(
                        data_class, data_class.__name__
                    )
                    description = metadata[0] if metadata else None
                    properties.append(
                        Property(
                            name=name,
                            data_type=data_type,
                            description=description.strip(),
                        )
                    )
        else:
            properties = output

        # Set specification defaults
        assert properties
        template_vars = {
            **(
                kwargs["template_vars"]
                if "template_vars" in kwargs and kwargs["template_vars"]
                else {}
            ),
            **{"output_properties": properties},
        }

        if role is not None:
            kwargs.setdefault("role", Role(persona=[role]))
        kwargs.setdefault("output_type", OutputType.JSON)
        kwargs.setdefault("template_vars", template_vars)
        super().__init__(**kwargs)


class JsonOrchestrator(Orchestrator):
    DEFAULT_FILE_NAME = "agent_json.md"

    def __init__(
        self,
        engine_uri: EngineUri,
        logger: Logger,
        model_manager: ModelManager,
        memory: MemoryManager,
        tool: ToolManager,
        event_manager: EventManager,
        output: type | list[Property],
        *,
        role: str | None = None,
        task: str | None = None,
        instructions: str | None = None,
        name: str | None = None,
        rules: list[str] | None = [],
        system: str | None = None,
        developer: str | None = None,
        user: str | None = None,
        user_template: str | None = None,
        template_id: str | None = None,
        settings: TransformerEngineSettings | None = None,
        call_options: dict | None = None,
        template_vars: dict | None = None,
    ):
        if system is not None or developer is not None:
            specification = JsonSpecification(
                output=output,
                goal=None,
                rules=rules,
                system_prompt=system,
                developer_prompt=developer,
                template_id=template_id or JsonOrchestrator.DEFAULT_FILE_NAME,
                template_vars=template_vars,
            )
        else:
            assert task is not None and instructions is not None
            specification = JsonSpecification(
                output=output,
                role=role,
                goal=Goal(task=task, instructions=[instructions]),
                rules=rules,
                template_id=template_id or JsonOrchestrator.DEFAULT_FILE_NAME,
                template_vars=template_vars,
            )
        super().__init__(
            logger,
            model_manager,
            memory,
            tool,
            event_manager,
            AgentOperation(
                specification=specification,
                environment=EngineEnvironment(
                    engine_uri=engine_uri, settings=settings
                ),
                modality=Modality.TEXT_GENERATION,
            ),
            call_options=call_options,
            user=user,
            user_template=user_template,
        )

    async def __call__(self, input: Input, **kwargs) -> str:
        text_response = await super().__call__(input, **kwargs)
        return await text_response.to_json()
