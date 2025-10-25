from ...agent.loader import OrchestratorLoader
from ...agent.orchestrator import Orchestrator
from ...agent.orchestrator.response.orchestrator_response import (
    OrchestratorResponse,
)
from ...cli import confirm_tool_call, get_input, has_input
from ...cli.commands.model import token_generation
from ...entities import (
    Backend,
    GenerationCacheStrategy,
    OrchestratorSettings,
    PermanentMemoryStoreSettings,
    ToolCall,
    ToolFormat,
)
from ...event import EventStats
from ...model.hubs.huggingface import HuggingfaceHub
from ...model.nlp.text.vendor import TextGenerationVendorModel
from ...server import agents_server
from ...tool.browser import BrowserToolSettings
from ...tool.context import ToolSettingsContext
from ...tool.database.settings import DatabaseToolSettings

from argparse import Namespace
from contextlib import AsyncExitStack
from dataclasses import fields
from logging import Logger
from os.path import dirname, getmtime, join
from typing import Iterable, Mapping
from uuid import UUID, uuid4

from jinja2 import Environment, FileSystemLoader
from rich.console import Console
from rich.live import Live
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.theme import Theme


def _parse_permanent_memory_items(
    items: Iterable[str],
) -> dict[str, PermanentMemoryStoreSettings]:
    stores: dict[str, PermanentMemoryStoreSettings] = {}
    for item in items:
        namespace, value = item.split("@", 1)
        namespace = namespace.strip()
        assert namespace, "Permanent memory namespace must be provided"
        stores[namespace] = OrchestratorLoader.parse_permanent_store_value(
            value
        )
    return stores


def get_orchestrator_settings(
    args: Namespace,
    *,
    agent_id: UUID,
    name: str | None = None,
    role: str | None = None,
    task: str | None = None,
    instructions: str | None = None,
    system: str | None = None,
    developer: str | None = None,
    user: str | None = None,
    user_template: str | None = None,
    engine_uri: str | None = None,
    memory_recent: bool | None = None,
    memory_permanent_message: str | None = None,
    memory_permanent: list[str] | None = None,
    max_new_tokens: int | None = None,
    temperature: float | None = None,
    tools: list[str] | None = None,
    top_k: int | None = None,
    top_p: float | None = None,
    use_cache: bool | None = None,
    cache_strategy: GenerationCacheStrategy | None = None,
) -> OrchestratorSettings:
    """Create ``OrchestratorSettings`` from CLI arguments."""
    assert not (
        (user or getattr(args, "user", None))
        and (user_template or getattr(args, "user_template", None))
    )
    memory_recent = (
        memory_recent
        if memory_recent is not None
        else (
            args.memory_recent
            if args.memory_recent is not None
            else not getattr(args, "no_session", False)
        )
    )
    engine_uri = engine_uri or args.engine_uri
    call_tokens = (
        max_new_tokens
        if max_new_tokens is not None
        else args.run_max_new_tokens
    )

    chat_settings = {
        k[len("run_chat_") :]: v
        for k, v in vars(args).items()
        if k.startswith("run_chat_") and v is not None
    }
    call_options = {
        "max_new_tokens": call_tokens,
        "skip_special_tokens": args.run_skip_special_tokens,
        "temperature": temperature,
        "top_k": top_k,
        "top_p": top_p,
        **({"chat_settings": chat_settings} if chat_settings else {}),
    }
    if use_cache is not None:
        call_options["use_cache"] = use_cache
    if cache_strategy is not None:
        call_options["cache_strategy"] = cache_strategy

    return OrchestratorSettings(
        agent_id=agent_id,
        orchestrator_type=None,
        agent_config={
            k: v
            for k, v in {
                "name": name if name is not None else args.name,
                "role": role if role is not None else args.role,
                "task": task if task is not None else args.task,
                "instructions": (
                    instructions
                    if instructions is not None
                    else getattr(args, "instructions", None)
                ),
                "system": (
                    system
                    if system is not None
                    else getattr(args, "system", None)
                ),
                "developer": (
                    developer
                    if developer is not None
                    else getattr(args, "developer", None)
                ),
                "user": (
                    user if user is not None else getattr(args, "user", None)
                ),
                "user_template": (
                    user_template
                    if user_template is not None
                    else getattr(args, "user_template", None)
                ),
            }.items()
            if v is not None
        },
        uri=engine_uri,
        engine_config={
            "backend": getattr(args, "backend", Backend.TRANSFORMERS.value)
        },
        call_options=call_options,
        template_vars=None,
        memory_permanent_message=(
            memory_permanent_message
            if memory_permanent_message is not None
            else args.memory_permanent_message
        ),
        permanent_memory=(
            _parse_permanent_memory_items(memory_permanent)
            if memory_permanent is not None
            else (
                _parse_permanent_memory_items(args.memory_permanent)
                if args.memory_permanent
                else None
            )
        ),
        memory_recent=memory_recent,
        sentence_model_id=(
            args.memory_engine_model_id
            or OrchestratorLoader.DEFAULT_SENTENCE_MODEL_ID
        ),
        sentence_model_engine_config=None,
        sentence_model_max_tokens=args.memory_engine_max_tokens,
        sentence_model_overlap_size=args.memory_engine_overlap,
        sentence_model_window_size=args.memory_engine_window,
        json_config=None,
        tools=(
            tools
            if tools is not None
            else (args.tool or []) + (getattr(args, "tools", None) or [])
        ),
        log_events=True,
    )


def _tool_settings_from_mapping(
    mapping: Mapping[str, object] | Namespace,
    *,
    prefix: str | None = None,
    settings_cls: type,
    open_files: bool = True,
) -> object:
    """Return tool settings from a mapping using dataclass ``settings_cls``."""
    values: dict[str, object] = {}
    for field in fields(settings_cls):
        key = f"tool_{prefix}_{field.name}" if prefix else field.name
        if isinstance(mapping, Namespace):
            if hasattr(mapping, key):
                value = getattr(mapping, key)
            else:
                continue
        else:
            if key in mapping:
                value = mapping[key]
            elif prefix and field.name in mapping:
                value = mapping[field.name]
            else:
                continue

        if value is not None:
            if (
                field.name == "debug_source"
                and open_files
                and isinstance(value, str)
            ):
                value = open(value)
            values[field.name] = value

    if not values:
        return None

    return settings_cls(**values)


def get_tool_settings(
    args: Namespace,
    *,
    prefix: str,
    settings_cls: type,
    open_files: bool = True,
) -> object:
    return _tool_settings_from_mapping(
        args, prefix=prefix, settings_cls=settings_cls, open_files=open_files
    )


async def agent_message_search(
    args: Namespace,
    console: Console,
    theme: Theme,
    hub: HuggingfaceHub,
    logger: Logger,
    refresh_per_second: int,
) -> None:
    _, _i = theme._, theme.icons

    specs_path = args.specifications_file
    engine_uri = getattr(args, "engine_uri", None)
    assert not (
        specs_path and engine_uri
    ), "specifications file and --engine-uri are mutually exclusive"
    assert (
        specs_path or engine_uri
    ), "specifications file or --engine-uri must be specified"
    agent_id = args.id
    participant_id = args.participant
    session_id = args.session

    assert agent_id and participant_id and session_id

    tty_path = getattr(args, "tty", "/dev/tty") or "/dev/tty"

    input_string = get_input(
        console,
        _i["user_input"] + " ",
        echo_stdin=not args.no_repl,
        is_quiet=args.quiet,
        tty_path=tty_path,
    )
    if not input_string:
        return

    limit = args.limit

    async with AsyncExitStack() as stack:
        loader = OrchestratorLoader(
            hub=hub,
            logger=logger,
            participant_id=participant_id,
            stack=stack,
        )
        with console.status(
            _("Loading agent..."),
            spinner=theme.get_spinner("agent_loading"),
            refresh_per_second=refresh_per_second,
        ):
            if specs_path:
                logger.debug(
                    "Loading agent from %s for participant %s",
                    specs_path,
                    participant_id,
                )

                orchestrator = await loader.from_file(
                    specs_path,
                    agent_id=agent_id,
                )
            else:
                assert (
                    args.engine_uri
                ), "--engine-uri required when no specifications file"
                logger.debug("Loading agent from inline settings")
                memory_recent = (
                    args.memory_recent
                    if args.memory_recent is not None
                    else True
                )
                settings = get_orchestrator_settings(
                    args,
                    agent_id=agent_id,
                    memory_recent=memory_recent,
                    tools=(args.tool or [])
                    + (getattr(args, "tools", None) or []),
                )
                browser_settings = get_tool_settings(
                    args, prefix="browser", settings_cls=BrowserToolSettings
                )
                database_settings = get_tool_settings(
                    args, prefix="database", settings_cls=DatabaseToolSettings
                )
                tool_settings = ToolSettingsContext(
                    browser=browser_settings, database=database_settings
                )
                orchestrator = await loader.from_settings(
                    settings, tool_settings=tool_settings
                )
            orchestrator = await stack.enter_async_context(orchestrator)

            assert orchestrator.engine_agent and orchestrator.engine.model_id

            can_access = args.skip_hub_access_check or hub.can_access(
                orchestrator.engine.model_id
            )
            is_local = not isinstance(
                orchestrator.engine, TextGenerationVendorModel
            )
            models = [
                hub.model(model_id) if is_local else model_id
                for model_id in orchestrator.model_ids
            ]

            console.print(
                theme.agent(orchestrator, models=models, can_access=can_access)
            )

            logger.debug(
                'Searching for "%s" across messages on session %s between '
                "agent %s and participant %s",
                input_string,
                session_id,
                agent_id,
                participant_id,
            )
            messages = await orchestrator.memory.search_messages(
                search=input_string,
                agent_id=agent_id,
                search_user_messages=False,
                session_id=session_id,
                participant_id=participant_id,
                function=args.function,
                limit=limit,
            )
            console.print(
                theme.search_message_matches(
                    participant_id, orchestrator, messages
                )
            )


async def agent_run(
    args: Namespace,
    console: Console,
    theme: Theme,
    hub: HuggingfaceHub,
    logger: Logger,
    refresh_per_second: int,
) -> None:
    _, _i = theme._, theme.icons

    specs_path = args.specifications_file
    engine_uri = getattr(args, "engine_uri", None)
    assert not (
        specs_path and engine_uri
    ), "specifications file and --engine-uri are mutually exclusive"
    assert (
        specs_path or engine_uri
    ), "specifications file or --engine-uri must be specified"
    use_async_generator = not args.use_sync_generator
    display_tokens = args.display_tokens or 0
    dtokens_pick = 10 if display_tokens > 0 else 0
    with_stats = args.stats and not args.quiet
    agent_id = args.id
    participant_id = args.participant
    session_id = args.session if not args.no_session else None
    load_recent_messages = (
        not args.skip_load_recent_messages and not args.no_session
    )
    load_recent_messages_limit = args.load_recent_messages_limit

    event_stats = EventStats()
    tty_path = getattr(args, "tty", "/dev/tty") or "/dev/tty"
    live_container: dict[str, Live | None] = {"live": None}

    def _confirm_call(call: ToolCall) -> str:
        return confirm_tool_call(
            console, call, tty_path=tty_path, live=live_container["live"]
        )

    async def _event_listener(event):
        nonlocal event_stats
        event_stats.total_triggers += 1
        if event.type not in event_stats.triggers:
            event_stats.triggers[event.type] = 1
        else:
            event_stats.triggers[event.type] += 1

    async def _init_orchestrator() -> Orchestrator:
        loader = OrchestratorLoader(
            hub=hub,
            logger=logger,
            participant_id=participant_id,
            stack=stack,
        )
        if specs_path:
            logger.debug(
                "Loading agent from %s for participant %s",
                specs_path,
                participant_id,
            )

            orchestrator = await loader.from_file(
                specs_path,
                agent_id=agent_id,
                disable_memory=args.no_session,
            )
        else:
            assert (
                args.engine_uri
            ), "--engine-uri required when no specifications file"
            assert not args.specifications_file or not args.engine_uri
            memory_recent = (
                args.memory_recent
                if args.memory_recent is not None
                else not args.no_session
            )
            settings = get_orchestrator_settings(
                args,
                agent_id=agent_id or uuid4(),
                memory_recent=memory_recent,
                tools=(args.tool or []) + (getattr(args, "tools", None) or []),
                max_new_tokens=getattr(args, "run_max_new_tokens", None),
                temperature=getattr(args, "run_temperature", None),
                top_k=getattr(args, "run_top_k", None),
                top_p=getattr(args, "run_top_p", None),
                use_cache=getattr(args, "run_use_cache", None),
                cache_strategy=getattr(args, "run_cache_strategy", None),
            )
            logger.debug("Loading agent from inline settings")
            browser_settings = get_tool_settings(
                args, prefix="browser", settings_cls=BrowserToolSettings
            )
            database_settings = get_tool_settings(
                args, prefix="database", settings_cls=DatabaseToolSettings
            )
            tool_settings = ToolSettingsContext(
                browser=browser_settings, database=database_settings
            )
            tool_format = (
                ToolFormat(args.tool_format) if args.tool_format else None
            )
            orchestrator = await loader.from_settings(
                settings, tool_settings=tool_settings, tool_format=tool_format
            )
        orchestrator.event_manager.add_listener(_event_listener)

        orchestrator = await stack.enter_async_context(orchestrator)

        if args.tools_confirm:
            assert (
                not orchestrator.tool.is_empty
            ), "--tools-confirm requires tools"

        logger.debug(
            "Agent loaded from %s, models used: %s, with recent message "
            "memory: %s, with permanent message memory: %s",
            specs_path,
            orchestrator.model_ids,
            "yes" if orchestrator.memory.has_recent_message else "no",
            (
                "yes, with session #"
                + str(orchestrator.memory.permanent_message.session_id)
                if orchestrator.memory.has_permanent_message
                else "no"
            ),
        )

        if not args.quiet:
            assert orchestrator.engine_agent and orchestrator.engine.model_id

            is_local = not isinstance(
                orchestrator.engine, TextGenerationVendorModel
            )

            can_access = (
                args.skip_hub_access_check
                or not is_local
                or hub.can_access(orchestrator.engine.model_id)
            )
            models = [
                hub.model(model_id) if is_local else model_id
                for model_id in orchestrator.model_ids
            ]

            console.print(
                theme.agent(orchestrator, models=models, can_access=can_access)
            )

        if not args.no_session:
            if session_id:
                await orchestrator.memory.continue_session(
                    session_id=session_id,
                    load_recent_messages=load_recent_messages,
                    load_recent_messages_limit=load_recent_messages_limit,
                )
            else:
                await orchestrator.memory.start_session()

        if (
            load_recent_messages
            and orchestrator.memory.has_recent_message
            and not orchestrator.memory.recent_message.is_empty
            and not args.quiet
        ):
            console.print(
                theme.recent_messages(
                    participant_id,
                    orchestrator,
                    orchestrator.memory.recent_message.data,
                )
            )

        return orchestrator

    async with AsyncExitStack() as stack:
        with console.status(
            _("Loading agent..."),
            spinner=theme.get_spinner("agent_loading"),
            refresh_per_second=refresh_per_second,
        ):
            orchestrator = await _init_orchestrator()

        watch_spec = bool(specs_path and args.conversation and args.watch)
        if watch_spec:
            specs_mtime = getmtime(specs_path)

        input_string: str | None = None
        in_conversation = False
        while not input_string or in_conversation:
            if watch_spec and not has_input(console):
                new_mtime = getmtime(specs_path)
                if new_mtime != specs_mtime:
                    logger.debug("Reloading agent from %s", specs_path)
                    orchestrator = await _init_orchestrator()
                    specs_mtime = new_mtime
                    in_conversation = False
                    continue
            logger.debug(
                "Waiting for new message to add to orchestrator's existing "
                + str(orchestrator.memory.recent_message.size)
                if orchestrator.memory
                and orchestrator.memory.has_recent_message
                else "0" + " messages"
            )
            input_string = get_input(
                console,
                _i["user_input"] + " ",
                echo_stdin=not args.no_repl,
                force_prompt=in_conversation,
                is_quiet=args.quiet,
                tty_path=tty_path,
            )
            if not input_string:
                logger.debug("Finishing session with orchestrator")
                return

            logger.debug('Agent about to process input "%s"', input_string)
            output = await orchestrator(
                input_string,
                use_async_generator=use_async_generator,
                tool_confirm=_confirm_call if args.tools_confirm else None,
            )

            if not args.quiet and not args.stats:
                console.print(_i["agent_output"] + " ", end="")

            if args.quiet:
                console.print(await output.to_str())
                return

            assert isinstance(output, OrchestratorResponse)

            await token_generation(
                args=args,
                console=console,
                theme=theme,
                logger=logger,
                orchestrator=orchestrator,
                event_stats=event_stats,
                lm=orchestrator.engine,
                input_string=input_string,
                refresh_per_second=refresh_per_second,
                response=output,
                dtokens_pick=dtokens_pick,
                display_tokens=display_tokens,
                tool_events_limit=args.display_tools_events,
                with_stats=with_stats,
                live_container=live_container,
            )

            if args.conversation:
                console.print("")
                if not in_conversation:
                    in_conversation = True
            else:
                break


async def agent_serve(
    args: Namespace,
    hub: HuggingfaceHub,
    logger: Logger,
    name: str,
    version: str,
) -> None:
    assert args.host and args.port
    specs_path = args.specifications_file
    agent_id = getattr(args, "id", None)
    participant_id = args.participant
    engine_uri = getattr(args, "engine_uri", None)
    assert not (
        specs_path and engine_uri
    ), "specifications file and --engine-uri are mutually exclusive"
    assert (
        specs_path or engine_uri
    ), "specifications file or --engine-uri must be specified"

    settings: OrchestratorSettings | None = None
    browser_settings: BrowserToolSettings | None = None
    database_settings: DatabaseToolSettings | None = None

    protocols = OrchestratorLoader.resolve_serve_protocols(
        specs_path=specs_path,
        cli_protocols=getattr(args, "protocol", None),
    )

    if not specs_path:
        memory_recent = (
            args.memory_recent if args.memory_recent is not None else True
        )
        settings = get_orchestrator_settings(
            args,
            agent_id=agent_id or uuid4(),
            memory_recent=memory_recent,
            tools=(args.tool or []) + (getattr(args, "tools", None) or []),
        )
        browser_settings = get_tool_settings(
            args, prefix="browser", settings_cls=BrowserToolSettings
        )
        database_settings = get_tool_settings(
            args, prefix="database", settings_cls=DatabaseToolSettings
        )

    tool_settings = ToolSettingsContext(
        browser=browser_settings, database=database_settings
    )

    server = agents_server(
        hub=hub,
        name=name,
        version=version,
        mcp_prefix=getattr(args, "mcp_prefix", "/mcp") or "/mcp",
        openai_prefix=args.openai_prefix,
        a2a_prefix=getattr(args, "a2a_prefix", "/a2a") or "/a2a",
        mcp_name=getattr(args, "mcp_name", "run") or "run",
        mcp_description=getattr(args, "mcp_description", None),
        a2a_tool_name=getattr(args, "a2a_name", "run") or "run",
        a2a_tool_description=getattr(args, "a2a_description", None),
        specs_path=specs_path,
        settings=settings,
        tool_settings=tool_settings,
        host=args.host,
        port=args.port,
        reload=args.reload,
        logger=logger,
        agent_id=agent_id,
        participant_id=participant_id,
        allow_origins=args.cors_origin,
        allow_origin_regex=args.cors_origin_regex,
        allow_methods=args.cors_method,
        allow_headers=args.cors_header,
        allow_credentials=args.cors_credentials,
        protocols=protocols,
    )
    await server.serve()


async def agent_proxy(
    args: Namespace,
    hub: HuggingfaceHub,
    logger: Logger,
    name: str,
    version: str,
) -> None:
    args.name = getattr(args, "name", "Proxy") or "Proxy"
    args.memory_recent = getattr(args, "memory_recent", True) or True
    args.memory_permanent_message = (
        getattr(args, "memory_permanent_message", None)
        or "postgresql://avalan:password@localhost:5432/avalan"
    )
    args.specifications_file = None

    assert getattr(args, "engine_uri", None), "--engine-uri is required"

    await agent_serve(args, hub, logger, name, version)


async def agent_init(args: Namespace, console: Console, theme: Theme) -> None:
    _ = theme._
    tty_path = getattr(args, "tty", "/dev/tty") or "/dev/tty"

    name = args.name or Prompt.ask(_("Agent name"))
    role = args.role or get_input(
        console,
        _("Agent role") + " ",
        echo_stdin=not args.no_repl,
        is_quiet=args.quiet,
        tty_path=tty_path,
    )

    task = args.task or get_input(
        console,
        _("Agent task") + " ",
        echo_stdin=not args.no_repl,
        is_quiet=args.quiet,
        tty_path=tty_path,
    )
    instructions = args.instructions or get_input(
        console,
        _("Agent instructions") + " ",
        echo_stdin=not args.no_repl,
        is_quiet=args.quiet,
        tty_path=tty_path,
    )

    memory_recent = (
        args.memory_recent
        if args.memory_recent is not None
        else Confirm.ask(_("Use recent message memory?"))
    )
    memory_permanent_message = (
        args.memory_permanent_message
        if args.memory_permanent_message is not None
        else Prompt.ask(_("Permanent memory DSN"), default="")
    )
    engine_uri = args.engine_uri or Prompt.ask(
        _("Engine URI"),
        default="microsoft/Phi-4-mini-instruct",
    )

    settings = get_orchestrator_settings(
        args,
        agent_id=uuid4(),
        name=name,
        role=role,
        task=task,
        instructions=instructions,
        engine_uri=engine_uri,
        memory_recent=memory_recent,
        memory_permanent_message=memory_permanent_message,
        max_new_tokens=(
            args.run_max_new_tokens
            if args.run_max_new_tokens is not None
            else 1024
        ),
        tools=(args.tool or []) + (getattr(args, "tools", None) or []),
        temperature=getattr(args, "run_temperature", None),
        top_k=getattr(args, "run_top_k", None),
        top_p=getattr(args, "run_top_p", None),
        use_cache=getattr(args, "run_use_cache", None),
        cache_strategy=getattr(args, "run_cache_strategy", None),
    )

    browser_tool = get_tool_settings(
        args,
        prefix="browser",
        settings_cls=BrowserToolSettings,
        open_files=False,
    )
    database_tool = get_tool_settings(
        args,
        prefix="database",
        settings_cls=DatabaseToolSettings,
        open_files=False,
    )

    env = Environment(
        loader=FileSystemLoader(
            join(dirname(__file__), "..", "..", "agent", "templates")
        ),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("blueprint.toml")
    tool_format = getattr(args, "tool_format", None)
    rendered = template.render(
        orchestrator=settings,
        browser_tool=browser_tool,
        database_tool=database_tool,
        tool_format=tool_format,
    )
    console.print(Syntax(rendered, "toml"))
