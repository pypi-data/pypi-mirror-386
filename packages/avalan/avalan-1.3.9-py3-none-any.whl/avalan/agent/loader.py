from ..agent.orchestrator import Orchestrator
from ..agent.orchestrator.orchestrators.default import DefaultOrchestrator
from ..agent.orchestrator.orchestrators.json import JsonOrchestrator, Property
from ..entities import (
    EngineUri,
    OrchestratorSettings,
    PermanentMemoryStoreSettings,
    ToolFormat,
    ToolManagerSettings,
    TransformerEngineSettings,
)
from ..event import Event, EventType
from ..event.manager import EventManager
from ..memory.manager import MemoryManager
from ..memory.partitioner.text import TextPartitioner
from ..memory.permanent.pgsql.raw import PgsqlRawMemory
from ..model.hubs.huggingface import HuggingfaceHub
from ..model.manager import ModelManager
from ..model.nlp.sentence import SentenceTransformerModel
from ..tool.browser import BrowserToolSet, BrowserToolSettings
from ..tool.code import CodeToolSet
from ..tool.context import ToolSettingsContext
from ..tool.database import DatabaseToolSet, DatabaseToolSettings
from ..tool.manager import ToolManager
from ..tool.math import MathToolSet
from ..tool.memory import MemoryToolSet

from contextlib import AsyncExitStack
from logging import DEBUG, INFO, Logger
from os import R_OK, access
from os.path import exists
from tomllib import load
from typing import Any, Callable
from uuid import UUID, uuid4


class OrchestratorLoader:
    DEFAULT_SENTENCE_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
    DEFAULT_SENTENCE_MODEL_MAX_TOKENS = 500
    DEFAULT_SENTENCE_MODEL_OVERLAP_SIZE = 125
    DEFAULT_SENTENCE_MODEL_WINDOW_SIZE = 250

    _ALLOWED_PROTOCOLS = frozenset({"a2a", "mcp", "openai"})
    _OPENAI_COMPLETION_ALIASES = frozenset(
        {
            "chat",
            "completion",
            "completions",
        }
    )
    _OPENAI_ENDPOINT_COMPLETIONS = "completions"
    _OPENAI_ENDPOINT_RESPONSES = "responses"
    _OPENAI_ENDPOINTS = frozenset(
        {
            _OPENAI_ENDPOINT_COMPLETIONS,
            _OPENAI_ENDPOINT_RESPONSES,
        }
    )
    _OPENAI_RESPONSES_ALIASES = frozenset({"response", "responses"})

    _hub: HuggingfaceHub
    _logger: Logger
    _participant_id: UUID
    _stack: AsyncExitStack

    def __init__(
        self,
        *,
        hub: HuggingfaceHub,
        logger: Logger,
        participant_id: UUID,
        stack: AsyncExitStack,
    ) -> None:
        self._hub = hub
        self._logger = logger
        self._participant_id = participant_id
        self._stack = stack

    @staticmethod
    def parse_permanent_store_value(
        value: str,
    ) -> PermanentMemoryStoreSettings:
        raw_value = value.strip()
        description: str | None = None
        if "," in raw_value:
            dsn, description_part = raw_value.split(",", 1)
            description = description_part.strip() or None
        else:
            dsn = raw_value
        dsn = dsn.strip()
        assert dsn, "Permanent memory store DSN must be provided"
        return PermanentMemoryStoreSettings(dsn=dsn, description=description)

    @classmethod
    def _parse_serve_protocols(
        cls, raw_protocols: list[str] | None
    ) -> dict[str, set[str]] | None:
        if not raw_protocols:
            return None

        selection: dict[str, set[str]] = {}
        for raw_protocol in raw_protocols:
            assert raw_protocol, "Protocol value cannot be empty"
            protocol_part, _, endpoints_part = raw_protocol.partition(":")
            protocol = protocol_part.strip().lower()
            assert protocol, "Protocol name cannot be empty"
            assert (
                protocol in cls._ALLOWED_PROTOCOLS
            ), f"Unsupported protocol '{protocol}'"

            endpoints_text = endpoints_part.strip()
            if endpoints_text:
                assert (
                    protocol == "openai"
                ), "Only the openai protocol accepts endpoint selection"
                endpoints = selection.setdefault(protocol, set())
                for endpoint in endpoints_text.split(","):
                    endpoint_name = endpoint.strip().lower()
                    assert (
                        endpoint_name
                    ), "OpenAI endpoint name cannot be empty"
                    if endpoint_name in cls._OPENAI_COMPLETION_ALIASES:
                        endpoints.add(cls._OPENAI_ENDPOINT_COMPLETIONS)
                    elif endpoint_name in cls._OPENAI_RESPONSES_ALIASES:
                        endpoints.add(cls._OPENAI_ENDPOINT_RESPONSES)
                    else:
                        raise AssertionError(
                            f"Unsupported OpenAI endpoint '{endpoint_name}'"
                        )
            else:
                if protocol == "openai":
                    selection[protocol] = set(cls._OPENAI_ENDPOINTS)
                else:
                    selection[protocol] = set()

        return selection

    @classmethod
    def _load_serve_protocol_strings(cls, path: str) -> list[str] | None:
        with open(path, "rb") as file:
            config = load(file)

        serve_section = config.get("serve")
        if serve_section is None:
            return None

        assert isinstance(serve_section, dict), "Serve section must be a table"

        raw_protocols = serve_section.get("protocols")
        if raw_protocols is None:
            return None

        assert isinstance(
            raw_protocols, list
        ), "Serve protocols must be defined as a list"

        parsed_protocols: list[str] = []
        for item in raw_protocols:
            assert isinstance(
                item, str
            ), "Serve protocol entries must be strings"
            value = item.strip()
            assert value, "Serve protocol entries cannot be empty"
            parsed_protocols.append(value)

        return parsed_protocols

    @classmethod
    def resolve_serve_protocols(
        cls,
        *,
        specs_path: str | None,
        cli_protocols: list[str] | None,
    ) -> dict[str, set[str]] | None:
        protocols = cls._parse_serve_protocols(cli_protocols)
        if protocols is not None:
            return protocols

        if not specs_path:
            return None

        config_protocols = cls._load_serve_protocol_strings(specs_path)
        return cls._parse_serve_protocols(config_protocols)

    @property
    def hub(self) -> HuggingfaceHub:
        return self._hub

    @property
    def participant_id(self) -> UUID:
        return self._participant_id

    async def from_file(
        self,
        path: str,
        *,
        agent_id: UUID | None,
        disable_memory: bool = False,
        uri: str | None = None,
        tool_settings: ToolSettingsContext | None = None,
    ) -> Orchestrator:
        _l = self._log_wrapper(self._logger)

        if not exists(path):
            raise FileNotFoundError(path)
        elif not access(path, R_OK):
            raise PermissionError(path)

        _l("Loading agent from %s", path, is_debug=False)

        with open(path, "rb") as file:
            config = load(file)

            # Validate settings

            assert "agent" in config, "No agent section in configuration"
            assert (
                "engine" in config
            ), "No engine section defined in configuration"
            assert (
                "uri" in config["engine"]
            ), "No uri defined in engine section of configuration"

            agent_config = config["agent"]
            assert not (
                "user" in agent_config and "user_template" in agent_config
            ), "user and user_template are mutually exclusive"

            assert (
                "engine" in config
            ), "No engine section defined in configuration"
            assert (
                "uri" in config["engine"]
            ), "No uri defined in engine section of configuration"

            uri = uri or config["engine"]["uri"]
            engine_config = config["engine"]
            assert "tools" not in engine_config, (
                "tools option in [engine] is no longer supported; "
                "configure tools under [tool.enable]"
            )
            tool_section = config.get("tool")
            if tool_section is None:
                tool_section = {}
            else:
                assert isinstance(
                    tool_section, dict
                ), "Tool section must be a mapping"

            enable_tools_config = tool_section.get("enable")
            enable_tools: list[str] | None = None
            if enable_tools_config is not None:
                if isinstance(enable_tools_config, str):
                    enable_tools = [enable_tools_config]
                else:
                    assert isinstance(
                        enable_tools_config, list
                    ), "tool.enable must be a string or a list of strings"
                    enable_tools = []
                    for tool_name in enable_tools_config:
                        assert isinstance(
                            tool_name, str
                        ), "tool.enable entries must be strings"
                        enable_tools.append(tool_name)
            engine_config.pop("uri", None)
            orchestrator_type = (
                config["agent"]["type"] if "type" in config["agent"] else None
            )
            agent_id = (
                agent_id
                if agent_id
                else (
                    config["agent"]["id"]
                    if "id" in config["agent"]
                    else uuid4()
                )
            )

            assert orchestrator_type is None or orchestrator_type in [
                "json"
            ], (
                f"Unknown type {config['agent']['type']} in agent section "
                + "of configuration"
            )

            call_options = config["run"] if "run" in config else None
            if call_options and "chat" in call_options:
                call_options["chat_settings"] = call_options.pop("chat")
            template_vars = (
                config["template"] if "template" in config else None
            )

            # Memory configuration

            memory_options = (
                config["memory"]
                if "memory" in config and not disable_memory
                else None
            )

            memory_permanent_message = (
                memory_options["permanent_message"]
                if memory_options and "permanent_message" in memory_options
                else None
            )

            memory_permanent: (
                dict[str, PermanentMemoryStoreSettings] | None
            ) = None
            if memory_options and "permanent" in memory_options:
                memory_permanent_option = memory_options["permanent"]
                assert isinstance(
                    memory_permanent_option, dict
                ), "Permanent memory should be a mapping"
                memory_permanent = {
                    str(ns): OrchestratorLoader.parse_permanent_store_value(
                        str(dsn)
                    )
                    for ns, dsn in memory_permanent_option.items()
                }
            memory_recent = (
                memory_options["recent"]
                if memory_options and "recent" in memory_options
                else False
            )
            assert isinstance(
                memory_recent, bool
            ), "Recent message memory can only be set or unset"

            sentence_model_id = (
                config["memory.engine"]["model_id"]
                if "memory.engine" in config
                and "model_id" in config["memory.engine"]
                else OrchestratorLoader.DEFAULT_SENTENCE_MODEL_ID
            )
            sentence_model_engine_config = (
                config["memory.engine"] if "memory.engine" in config else None
            )
            sentence_model_max_tokens = (
                config["memory.engine"]["max_tokens"]
                if sentence_model_engine_config
                and "max_tokens" in sentence_model_engine_config
                else OrchestratorLoader.DEFAULT_SENTENCE_MODEL_MAX_TOKENS
            )
            sentence_model_overlap_size = (
                config["memory.engine"]["overlap_size"]
                if sentence_model_engine_config
                and "overlap_size" in sentence_model_engine_config
                else OrchestratorLoader.DEFAULT_SENTENCE_MODEL_OVERLAP_SIZE
            )
            sentence_model_window_size = (
                config["memory.engine"]["window_size"]
                if sentence_model_engine_config
                and "window_size" in sentence_model_engine_config
                else OrchestratorLoader.DEFAULT_SENTENCE_MODEL_WINDOW_SIZE
            )

            if sentence_model_engine_config:
                sentence_model_engine_config.pop("model_id", None)
                sentence_model_engine_config.pop("max_tokens", None)
                sentence_model_engine_config.pop("overlap_size", None)
                sentence_model_engine_config.pop("window_size", None)

            settings = OrchestratorSettings(
                agent_id=agent_id,
                orchestrator_type=orchestrator_type,
                agent_config=agent_config,
                uri=uri,
                engine_config=engine_config,
                tools=enable_tools,
                call_options=call_options,
                template_vars=template_vars,
                memory_permanent_message=memory_permanent_message,
                permanent_memory=memory_permanent,
                memory_recent=memory_recent,
                sentence_model_id=sentence_model_id,
                sentence_model_engine_config=sentence_model_engine_config,
                sentence_model_max_tokens=sentence_model_max_tokens,
                sentence_model_overlap_size=sentence_model_overlap_size,
                sentence_model_window_size=sentence_model_window_size,
                json_config=(
                    config.get("json") if isinstance(config, dict) else None
                ),
                log_events=True,
            )

            browser_config = None
            browser_section = tool_section.get("browser")
            if browser_section is not None:
                assert isinstance(
                    browser_section, dict
                ), "tool.browser section must be a mapping"
                browser_open_section = browser_section.get("open")
                if browser_open_section is not None:
                    assert isinstance(
                        browser_open_section, dict
                    ), "tool.browser.open section must be a mapping"
                    browser_config = browser_open_section
                else:
                    browser_config = browser_section
            browser_settings = None
            if browser_config:
                if "debug_source" in browser_config and isinstance(
                    browser_config["debug_source"], str
                ):
                    browser_config["debug_source"] = open(
                        browser_config["debug_source"]
                    )
                browser_settings = BrowserToolSettings(**browser_config)

            database_settings = None
            database_config = tool_section.get("database")
            if database_config:
                assert isinstance(
                    database_config, dict
                ), "tool.database section must be a mapping"
                database_settings = DatabaseToolSettings(**database_config)

            if tool_settings:
                browser_settings = tool_settings.browser or browser_settings
                database_settings = tool_settings.database or database_settings
                extra = tool_settings.extra
            else:
                extra = None

            tool_settings = ToolSettingsContext(
                browser=browser_settings,
                database=database_settings,
                extra=extra,
            )

            tool_format = None
            tool_format_str = tool_section.get("format")
            if tool_format_str:
                tool_format = ToolFormat(tool_format_str)

            _l("Loaded agent from %s", path, is_debug=False)

            return await self.from_settings(
                settings, tool_settings=tool_settings, tool_format=tool_format
            )

    async def from_settings(
        self,
        settings: OrchestratorSettings,
        *,
        tool_settings: ToolSettingsContext | None = None,
        tool_format: ToolFormat | None = None,
    ) -> Orchestrator:
        _l = self._log_wrapper(self._logger)

        _l("Loading agent from settings", is_debug=False)

        sentence_model_engine_settings = (
            TransformerEngineSettings(**settings.sentence_model_engine_config)
            if settings.sentence_model_engine_config
            else TransformerEngineSettings()
        )

        _l(
            "Loading sentence transformer model %s for agent %s",
            settings.sentence_model_id,
            settings.agent_id,
        )

        sentence_model = SentenceTransformerModel(
            model_id=settings.sentence_model_id,
            settings=sentence_model_engine_settings,
            logger=self._logger,
        )
        sentence_model = self._stack.enter_context(sentence_model)

        _l(
            "Loading text partitioner for model %s for agent %s with settings"
            " (%s, %s, %s)",
            settings.sentence_model_id,
            settings.agent_id,
            settings.sentence_model_max_tokens,
            settings.sentence_model_overlap_size,
            settings.sentence_model_window_size,
        )

        text_partitioner = TextPartitioner(
            model=sentence_model,
            logger=self._logger,
            max_tokens=settings.sentence_model_max_tokens,
            overlap_size=settings.sentence_model_overlap_size,
            window_size=settings.sentence_model_window_size,
        )

        _l("Loading event manager")

        event_manager = EventManager()
        if settings.log_events:

            def _log_event(event: Event) -> None:
                is_info_event = event.type in (
                    EventType.TOOL_PROCESS,
                    EventType.TOOL_RESULT,
                )
                _l(
                    "%s",
                    event.payload,
                    inner_type=f"Event {event.type}",
                    is_debug=not is_info_event,
                )

            event_manager.add_listener(_log_event)

        _l("Loading memory manager for agent %s", settings.agent_id)

        memory = await MemoryManager.create_instance(
            agent_id=settings.agent_id,
            participant_id=self._participant_id,
            text_partitioner=text_partitioner,
            logger=self._logger,
            with_permanent_message_memory=settings.memory_permanent_message,
            with_recent_message_memory=settings.memory_recent,
            event_manager=event_manager,
        )

        for namespace, store_settings in (
            settings.permanent_memory or {}
        ).items():
            _l(
                "Loading permanent memory %s for agent %s",
                namespace,
                settings.agent_id,
            )
            store = await PgsqlRawMemory.create_instance(
                dsn=store_settings.dsn, logger=self._logger
            )
            memory.add_permanent_memory(
                namespace,
                store,
                description=store_settings.description,
            )

        _l(
            "Loading tool manager for agent %s with partitioner and a sentence"
            " model %s with settings (%s, %s, %s)",
            settings.agent_id,
            settings.sentence_model_id,
            settings.sentence_model_max_tokens,
            settings.sentence_model_overlap_size,
            settings.sentence_model_window_size,
        )

        browser_settings = tool_settings.browser if tool_settings else None
        database_settings = tool_settings.database if tool_settings else None

        _l(
            "Tool settings: browser=%s, database=%s",
            browser_settings,
            database_settings,
        )

        available_toolsets = [
            BrowserToolSet(
                settings=browser_settings or BrowserToolSettings(),
                partitioner=text_partitioner,
                namespace="browser",
            ),
            CodeToolSet(namespace="code"),
            MathToolSet(namespace="math"),
            MemoryToolSet(memory, namespace="memory"),
        ]
        if database_settings:
            available_toolsets.append(
                DatabaseToolSet(
                    settings=database_settings, namespace="database"
                )
            )

        tool = ToolManager.create_instance(
            available_toolsets=available_toolsets,
            enable_tools=settings.tools,
            settings=ToolManagerSettings(tool_format=tool_format),
        )
        tool = await self._stack.enter_async_context(tool)

        _l(
            "Creating orchestrator %s #%s",
            settings.orchestrator_type,
            settings.agent_id,
        )

        model_manager = ModelManager(
            self._hub, self._logger, event_manager=event_manager
        )
        model_manager = self._stack.enter_context(model_manager)

        engine_uri = model_manager.parse_uri(settings.uri)
        engine_settings = model_manager.get_engine_settings(
            engine_uri,
            settings=settings.engine_config,
        )

        assert settings.agent_id

        if settings.orchestrator_type == "json":
            assert settings.json_config is not None
            agent = self._load_json_orchestrator(
                agent_id=settings.agent_id,
                engine_uri=engine_uri,
                engine_settings=engine_settings,
                logger=self._logger,
                model_manager=model_manager,
                memory=memory,
                tool=tool,
                event_manager=event_manager,
                config={"json": settings.json_config},
                agent_config=settings.agent_config,
                call_options=settings.call_options,
                template_vars=settings.template_vars,
            )
        else:
            agent = DefaultOrchestrator(
                engine_uri,
                self._logger,
                model_manager,
                memory,
                tool,
                event_manager,
                id=settings.agent_id,
                name=settings.agent_config.get("name"),
                role=(
                    None
                    if "system" in settings.agent_config
                    or "developer" in settings.agent_config
                    else settings.agent_config.get("role")
                ),
                task=(
                    None
                    if "system" in settings.agent_config
                    or "developer" in settings.agent_config
                    else settings.agent_config.get("task")
                ),
                instructions=(
                    None
                    if "system" in settings.agent_config
                    or "developer" in settings.agent_config
                    else settings.agent_config.get("instructions")
                ),
                rules=settings.agent_config.get("rules"),
                system=settings.agent_config.get("system"),
                developer=settings.agent_config.get("developer"),
                user=settings.agent_config.get("user"),
                user_template=settings.agent_config.get("user_template"),
                settings=engine_settings,
                call_options=settings.call_options,
                template_vars=settings.template_vars,
            )

        _l("Loaded agent from settings", is_debug=False)

        return agent

    @staticmethod
    def _load_json_orchestrator(
        agent_id: UUID,
        engine_uri: EngineUri,
        engine_settings: TransformerEngineSettings,
        logger: Logger,
        model_manager: ModelManager,
        memory: MemoryManager,
        tool: ToolManager,
        event_manager: EventManager,
        config: dict,
        agent_config: dict,
        call_options: dict | None,
        template_vars: dict | None,
    ) -> JsonOrchestrator:
        assert "json" in config, "No json section in configuration"
        if "system" not in agent_config and "developer" not in agent_config:
            assert (
                "instructions" in agent_config
            ), "No instructions defined in agent section of configuration"
            assert (
                "task" in agent_config
            ), "No task defined in agent section of configuration"

        properties: list[Property] = []
        for property_name in config.get("json", []):
            output_property = config["json"][property_name]
            properties.append(
                Property(
                    name=property_name,
                    data_type=output_property["type"],
                    description=output_property["description"],
                )
            )

        assert properties, "No properties defined in configuration"

        agent = JsonOrchestrator(
            engine_uri,
            logger,
            model_manager,
            memory,
            tool,
            event_manager,
            properties,
            id=agent_id,
            name=agent_config["name"] if "name" in agent_config else None,
            role=(
                None
                if "system" in agent_config or "developer" in agent_config
                else agent_config.get("role")
            ),
            task=(
                None
                if "system" in agent_config or "developer" in agent_config
                else agent_config.get("task")
            ),
            instructions=(
                None
                if "system" in agent_config or "developer" in agent_config
                else agent_config.get("instructions")
            ),
            rules=agent_config.get("rules"),
            system=agent_config.get("system"),
            developer=agent_config.get("developer"),
            user=agent_config.get("user"),
            user_template=agent_config.get("user_template"),
            settings=engine_settings,
            call_options=call_options,
            template_vars=template_vars,
        )
        return agent

    @staticmethod
    def _log_wrapper(logger: Logger) -> Callable[..., Any]:
        def wrapper(
            message: str,
            *args: Any,
            inner_type: str | None = None,
            **kwargs: Any,
        ) -> Any:
            is_debug = kwargs.pop("is_debug", True)
            level = DEBUG if is_debug else INFO
            prefix = (
                f"<{inner_type} @ OrchestratorLoader> "
                if inner_type
                else "<OrchestratorLoader> "
            )
            return logger.log(level, prefix + message, *args, **kwargs)

        return wrapper
