from ..agent import Role
from ..agent.engine import EngineAgent
from ..entities import EngineUri
from ..event.manager import EventManager
from ..memory.manager import MemoryManager
from ..model.call import ModelCallContext
from ..model.engine import Engine
from ..model.manager import ModelManager
from ..tool.manager import ToolManager

from os import linesep
from os.path import dirname, join
from typing import Any
from uuid import UUID

from jinja2 import (
    Environment as TemplateEnvironment,
)
from jinja2 import (
    FileSystemLoader,
    Template,
)


class Renderer:
    _TEMPLATES_DIR = "templates"
    _environment: TemplateEnvironment
    _clean_spaces: bool
    _templates: dict[str, Template] = {}

    def __init__(
        self, templates_path: str | None = None, clean_spaces: bool = True
    ):
        self._clean_spaces = clean_spaces
        self._environment = TemplateEnvironment(
            loader=FileSystemLoader(
                templates_path or join(dirname(__file__), self._TEMPLATES_DIR)
            ),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def __call__(self, template_id: str, **kwargs) -> str:
        if template_id not in self._templates:
            self._templates[template_id] = self._environment.get_template(
                template_id
            )

        output = self._templates[template_id].render(**kwargs)

        if self._clean_spaces:
            output = linesep.join(line.strip() for line in output.splitlines())
        return output

    def from_string(
        self,
        template: str,
        template_vars: dict | None = None,
        encoding: str = "utf-8",
    ) -> str:
        return (
            Template(template).render(**template_vars).encode(encoding)
            if template_vars
            else template
        )


class TemplateEngineAgent(EngineAgent):
    _renderer: Renderer

    def __init__(
        self,
        model: Engine,
        memory: MemoryManager,
        tool: ToolManager,
        event_manager: EventManager,
        model_manager: ModelManager,
        renderer: Renderer,
        engine_uri: EngineUri,
        *args,
        name: str | None = None,
        id: UUID | None = None,
    ):
        super().__init__(
            model,
            memory,
            tool,
            event_manager,
            model_manager,
            engine_uri,
            name=name,
            id=id,
        )
        self._renderer = renderer

    def _prepare_call(self, context: ModelCallContext) -> Any:
        specification = context.specification
        kwargs = dict(context.engine_args)
        if specification.system_prompt is not None:
            kwargs.setdefault("settings", specification.settings)
            kwargs.setdefault("system_prompt", specification.system_prompt)
            if specification.developer_prompt is not None:
                kwargs.setdefault(
                    "developer_prompt", specification.developer_prompt
                )
            return kwargs

        template_id = specification.template_id or "agent.md"
        template_vars = (
            specification.template_vars.copy()
            if specification.template_vars
            else {}
        )
        if specification.settings and specification.settings.template_vars:
            template_vars.update(specification.settings.template_vars)
        template_vars.setdefault("name", self._name)
        template_vars.setdefault(
            "roles",
            (
                (
                    [
                        self._renderer.from_string(persona, template_vars)
                        for persona in specification.role.persona
                    ]
                    if isinstance(specification.role, Role)
                    else (
                        [specification.role]
                        if isinstance(specification.role, str)
                        else specification.role
                    )
                )
                if template_vars
                else specification.role
            ),
        )
        template_vars.setdefault(
            "task",
            (
                self._renderer.from_string(
                    specification.goal.task, template_vars
                )
                if specification.goal and template_vars
                else specification.goal.task if specification.goal else None
            ),
        )
        template_vars.setdefault(
            "instructions",
            (
                [
                    self._renderer.from_string(instruction, template_vars)
                    for instruction in specification.goal.instructions
                ]
                if specification.goal and template_vars
                else (
                    specification.goal.instructions
                    if specification.goal
                    else None
                )
            ),
        )
        template_vars.setdefault(
            "rules",
            (
                [
                    self._renderer.from_string(rule, template_vars)
                    for rule in specification.rules
                ]
                if template_vars and specification.rules
                else specification.rules
            ),
        )
        system_prompt = self._renderer(template_id, **template_vars)

        kwargs.setdefault("settings", specification.settings)
        kwargs.setdefault("system_prompt", system_prompt)
        if specification.developer_prompt is not None:
            kwargs.setdefault(
                "developer_prompt", specification.developer_prompt
            )
        return kwargs
