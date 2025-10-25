from ...agent import Specification
from ...agent.orchestrator import Orchestrator
from ...cli import confirm, get_input, has_input
from ...cli.commands.cache import cache_delete, cache_download
from ...entities import (
    GenerationSettings,  # noqa: F401
    Modality,
    Model,
    ReasoningToken,
    Token,
    ToolCallToken,
)
from ...event import TOOL_TYPES, Event, EventStats, EventType
from ...model.call import ModelCall, ModelCallContext
from ...model.criteria import KeywordStoppingCriteria  # noqa: F401
from ...model.hubs.huggingface import HuggingfaceHub
from ...model.manager import ModelManager
from ...model.nlp.sentence import SentenceTransformerModel
from ...model.nlp.text.generation import TextGenerationModel
from ...model.response.text import TextGenerationResponse
from ...secrets import KeyringSecrets
from . import get_model_settings

from argparse import Namespace
from asyncio import (
    Event as EventSignal,
)
from asyncio import (
    as_completed,
    create_task,
    gather,
    sleep,
    to_thread,
)
from dataclasses import replace
from datetime import datetime, timezone
from logging import Logger
from time import perf_counter

from rich.console import Console, Group, RenderableType
from rich.live import Live
from rich.padding import Padding
from rich.prompt import Prompt
from rich.spinner import Spinner
from rich.theme import Theme


def model_display(
    args: Namespace,
    console: Console,
    theme: Theme,
    hub: HuggingfaceHub,
    logger: Logger,
    *vargs,
    modality: Modality | None = None,
    load: bool | None = None,
    model: SentenceTransformerModel | TextGenerationModel | None = None,
    summary: bool | None = None,
) -> None:
    assert args.model
    _ = theme._

    with ModelManager(hub, logger) as manager:
        engine_uri = manager.parse_uri(args.model)
        model_id = args.model
        can_access = args.skip_hub_access_check or hub.can_access(model_id)
        hub_model = hub.model(model_id)
        console.print(
            theme.model(
                hub_model,
                can_access=can_access,
                expand=(summary is not None and not summary)
                or (summary is None and not args.summary),
                summary=False,
            )
        )

        is_runnable = not engine_uri.is_local
        if not model and (
            (load is not None and load) or (load is None and args.load)
        ):
            model_settings = get_model_settings(
                args,
                hub,
                logger,
                engine_uri,
                modality=modality,
            )
            with manager.load(**model_settings) as lm:
                logger.debug("Loaded model %s", lm.config.__repr__())
                is_runnable = lm.is_runnable(getattr(args, "device", None))
                console.print(
                    Padding(
                        theme.model_display(
                            lm.config,
                            lm.tokenizer_config,
                            is_runnable=is_runnable,
                            summary=summary or False,
                        ),
                        pad=(0, 0, 0, 0),
                    )
                )
        elif model:
            console.print(
                Padding(
                    theme.model_display(
                        model.config,
                        model.tokenizer_config,
                        is_runnable=is_runnable,
                        summary=summary or False,
                    ),
                    pad=(0, 0, 0, 0),
                )
            )


def model_install(
    args: Namespace, console: Console, theme: Theme, hub: HuggingfaceHub
) -> None:
    assert args.model
    engine_uri = ModelManager.parse_uri(args.model)
    if (
        engine_uri.vendor
        and engine_uri.password
        and engine_uri.user == "secret"
    ):
        secrets = KeyringSecrets()
        token = secrets.read(engine_uri.password)
        if token is None:
            secret_value = Prompt.ask(
                theme.ask_secret_password(engine_uri.password)
            )
            secrets.write(engine_uri.password, secret_value)
        elif confirm(console, theme.ask_override_secret(engine_uri.password)):
            secret_value = Prompt.ask(
                theme.ask_secret_password(engine_uri.password)
            )
            secrets.write(engine_uri.password, secret_value)

    cache_download(args, console, theme, hub)


async def model_run(
    args: Namespace,
    console: Console,
    theme: Theme,
    hub: HuggingfaceHub,
    refresh_per_second: int,
    logger: Logger,
) -> None:
    assert args.model and args.device and args.max_new_tokens
    _, _i = theme._, theme.icons

    with ModelManager(hub, logger) as manager:
        engine_uri = manager.parse_uri(args.model)
        model_settings = get_model_settings(args, hub, logger, engine_uri)
        modality = model_settings["modality"]
        assert modality

        if not args.quiet:
            if engine_uri.is_local:
                can_access = (
                    args.quiet
                    or args.skip_hub_access_check
                    or hub.can_access(engine_uri.model_id)
                )

                model = hub.model(engine_uri.model_id)
                console.print(
                    Padding(
                        theme.model(
                            model, can_access=can_access, summary=True
                        ),
                        pad=(0, 0, 1, 0),
                    )
                )

        operation = ModelManager.get_operation_from_arguments(
            modality, args, None
        )

        with manager.load(**model_settings) as model:
            logger.debug("Loaded model %s", model.config.__repr__())

            tty_path = getattr(args, "tty", "/dev/tty") or "/dev/tty"

            if operation.requires_input or has_input(console):
                input_string = get_input(
                    console,
                    _i["user_input"] + " ",
                    echo_stdin=not args.no_repl,
                    is_quiet=args.quiet,
                    tty_path=tty_path,
                )
                if not input_string:
                    return

                operation = replace(operation, input=input_string)

            context = ModelCallContext(
                specification=Specification(role=None, goal=None),
                input=operation.input,
                engine_args={},
            )
            task = ModelCall(
                engine_uri=engine_uri,
                model=model,
                operation=operation,
                tool=None,
                context=context,
            )
            output = await manager(task)

            if operation.modality in {
                Modality.AUDIO_SPEECH_RECOGNITION,
                Modality.TEXT_QUESTION_ANSWERING,
                Modality.TEXT_SEQUENCE_CLASSIFICATION,
                Modality.TEXT_SEQUENCE_TO_SEQUENCE,
                Modality.TEXT_TRANSLATION,
                Modality.VISION_IMAGE_TO_TEXT,
                Modality.VISION_ENCODER_DECODER,
                Modality.VISION_IMAGE_TEXT_TO_TEXT,
            }:
                console.print(output)

            elif operation.modality == Modality.AUDIO_CLASSIFICATION:
                console.print(theme.display_audio_labels(output))

            elif operation.modality == Modality.AUDIO_TEXT_TO_SPEECH:
                console.print(f"Audio generated in {output}")

            elif operation.modality == Modality.AUDIO_GENERATION:
                console.print(f"Audio generated in {output}")

            elif operation.modality == Modality.TEXT_TOKEN_CLASSIFICATION:
                console.print(theme.display_token_labels([output]))

            elif operation.modality == Modality.TEXT_GENERATION:
                await token_generation(
                    args=args,
                    console=console,
                    theme=theme,
                    logger=logger,
                    orchestrator=None,
                    event_stats=None,
                    lm=model,
                    input_string=operation.input,
                    refresh_per_second=refresh_per_second,
                    response=output,
                    dtokens_pick=operation.parameters["text"].pick_tokens,
                    display_tokens=args.display_tokens or 0,
                    with_stats=not args.quiet,
                    tool_events_limit=args.display_tools_events,
                )

            elif operation.modality == Modality.VISION_IMAGE_CLASSIFICATION:
                console.print(theme.display_image_entity(output))

            elif operation.modality == Modality.VISION_OBJECT_DETECTION:
                console.print(theme.display_image_entities(output, sort=True))

            elif operation.modality == Modality.VISION_SEMANTIC_SEGMENTATION:
                console.print(theme.display_image_labels(output))

            elif operation.modality == Modality.VISION_TEXT_TO_IMAGE:
                console.print(output)

            elif operation.modality == Modality.VISION_TEXT_TO_ANIMATION:
                console.print(output)

            elif operation.modality == Modality.VISION_TEXT_TO_VIDEO:
                console.print(output)

            else:
                raise NotImplementedError(
                    f"Modality {operation.modality} not supported"
                )


async def model_search(
    args: Namespace,
    console: Console,
    theme: Theme,
    hub: HuggingfaceHub,
    refresh_per_second: int,
) -> None:
    assert args.limit
    _ = theme._

    models: list[Model] = []
    model_access: dict[str, bool] = {}

    # Fetch matching models
    with console.status(
        _("Loading models..."),
        spinner=theme.get_spinner("downloading"),
        refresh_per_second=refresh_per_second,
    ):
        models = [
            model
            for model in hub.models(
                filter=args.filter or None,
                search=args.search or None,
                library=args.library or None,
                author=args.author,
                gated=True if args.gated else False if args.open else None,
                language=args.language or None,
                name=args.name or None,
                task=args.task or None,
                tags=args.tag or None,
                limit=args.limit,
            )
        ]

    # Tasks to check model access
    tasks = [
        create_task(to_thread(lambda id=model.id: (id, hub.can_access(id))))
        for model in models
    ]

    def _render(
        models: list[Model], model_access: dict[str, bool]
    ) -> list[RenderableType]:
        return [
            theme.model(
                model,
                can_access=(
                    model_access[model.id]
                    if model.id in model_access
                    else None
                ),
            )
            for model in models
        ]

    # Keep list of models updated as tasks are completed
    with Live(
        Group(*_render(models, model_access)),
        console=console,
        refresh_per_second=refresh_per_second,
    ) as live:
        for completed_task in as_completed(tasks):
            model_id, can_access = await completed_task
            model_access[model_id] = can_access

            live.update(Group(*_render(models, model_access)))

        await gather(*tasks)


def model_uninstall(
    args: Namespace, console: Console, theme: Theme, hub: HuggingfaceHub
) -> None:
    assert args.model
    engine_uri = ModelManager.parse_uri(args.model)
    if (
        engine_uri.vendor
        and engine_uri.password
        and engine_uri.user == "secret"
    ):
        secrets = KeyringSecrets()
        secrets.delete(engine_uri.password)

    cache_delete(args, console, theme, hub, is_full_deletion=True)


async def token_generation(
    args: Namespace,
    console: Console,
    theme: Theme,
    logger: Logger,
    orchestrator: Orchestrator | None,
    event_stats: EventStats | None,
    lm: TextGenerationModel,
    input_string: str,
    response: TextGenerationResponse,
    *,
    display_tokens: int,
    dtokens_pick: int,
    refresh_per_second: int,
    tool_events_limit: int | None,
    with_stats: bool = True,
    live_container: dict[str, Live | None] | None = None,
):
    # If no statistics needed, return as early as possible
    if not with_stats:
        async for token in response:
            if isinstance(token, Event):
                continue
            text_token = token.token if isinstance(token, Token) else token
            console.print(text_token, end="")
        return

    stop_signal = EventSignal()

    # From here on, display includes stats and may include token probabilities

    if not orchestrator or (
        not args.display_events and not args.display_tools
    ):
        with Live(
            refresh_per_second=refresh_per_second,
            screen=args.record,
            console=console,
        ) as live:
            if live_container is not None:
                live_container["live"] = live
            await _token_stream(
                args,
                console,
                live,
                None,
                None,
                theme,
                logger,
                orchestrator,
                event_stats,
                lm,
                input_string,
                response,
                display_tokens=display_tokens,
                dtokens_pick=dtokens_pick,
                refresh_per_second=refresh_per_second,
                stop_signal=stop_signal,
                tool_events_limit=tool_events_limit,
                with_stats=with_stats,
            )
        if live_container is not None:
            live_container["live"] = None
    else:
        events_height = 6
        tools_height = 10
        empty = ""
        group = Group(empty, empty, empty)
        events_group_index = 0
        tools_group_index = 1
        tokens_group_index = 2

        with Live(
            group,
            refresh_per_second=refresh_per_second,
            screen=args.record,
            console=console,
        ) as live:
            if live_container is not None:
                live_container["live"] = live
            await gather(
                _event_stream(
                    args,
                    console,
                    live,
                    group,
                    events_group_index,
                    tools_group_index,
                    orchestrator,
                    theme,
                    events_height=events_height,
                    tools_height=tools_height,
                    stop_signal=stop_signal,
                ),
                _token_stream(
                    args,
                    console,
                    live,
                    group,
                    tokens_group_index,
                    theme,
                    logger,
                    orchestrator,
                    event_stats,
                    lm,
                    input_string,
                    response,
                    display_tokens=display_tokens,
                    dtokens_pick=dtokens_pick,
                    refresh_per_second=refresh_per_second,
                    stop_signal=stop_signal,
                    tool_events_limit=tool_events_limit,
                    with_stats=with_stats,
                ),
            )
        if live_container is not None:
            live_container["live"] = None


async def _event_stream(
    args: Namespace,
    console: Console,
    live: Live,
    group: Group,
    events_group_index: int,
    tools_group_index: int,
    orchestrator: Orchestrator,
    theme: Theme,
    *,
    events_height: int = 6,
    tools_height: int = 10,
    stop_signal: EventSignal,
) -> None:
    event_manager = orchestrator.event_manager
    if not event_manager or (
        not args.display_events and not args.display_tools
    ):
        return

    async for e in event_manager.listen(stop_signal=stop_signal):
        tool_view = e.type in TOOL_TYPES
        if (tool_view and not args.display_tools) or (
            not tool_view and not args.display_events
        ):
            continue

        events_renderable = theme.events(
            event_manager.history,
            events_limit=6 if tool_view else 4,
            height=tools_height if tool_view else events_height,
            include_tokens=False,
            include_tools=tool_view,
            include_tool_detect=False,
            include_non_tools=not tool_view,
            tool_view=tool_view,
        )
        if not events_renderable:
            continue

        _render_frame(
            args,
            console,
            live,
            events_renderable,
            group,
            tools_group_index if tool_view else events_group_index,
        )


async def _token_stream(
    args: Namespace,
    console: Console,
    live: Live,
    group: Group | None,
    tokens_group_index: int | None,
    theme: Theme,
    logger: Logger,
    orchestrator: Orchestrator | None,
    event_stats: EventStats | None,
    lm: TextGenerationModel,
    input_string: str,
    response: TextGenerationResponse,
    *,
    display_tokens: int,
    dtokens_pick: int,
    refresh_per_second: int,
    stop_signal: EventSignal | None,
    tool_events_limit: int | None,
    with_stats: bool = True,
) -> None:
    display_time_to_n_token = args.display_time_to_n_token
    display_reasoning_time = not getattr(args, "skip_display_reasoning_time")
    display_pause = (
        args.display_pause
        if args.display_pause and args.display_pause > 0
        else 0
    )
    start_thinking = (
        args.start_thinking if hasattr(args, "start_thinking") else False
    )
    tokens = []
    answer_text_tokens: list[str] = []
    thinking_text_tokens: list[str] = []
    tool_text_tokens: list[str] = []
    tool_events: list[Event] = []
    tool_event_calls: list[Event] = []
    tool_event_results: list[Event] = []
    completed_call_ids: set[str] = set()
    total_tokens = 0
    frame_minimum_pause_ms = (
        100 if display_pause > 0 and display_tokens > 0 else 0
    )

    input_token_count = (
        response.input_token_count
        if response.input_token_count
        else (
            orchestrator.input_token_count
            if orchestrator
            else lm.input_token_count(input_string)
        )
    )
    ttft: float | None = None
    ttnt: float | None = None
    last_current_dtoken: Token | None = None
    tool_running_spinner: Spinner | None = None

    if start_thinking and response.can_think and not response.is_thinking:
        response.set_thinking(start_thinking)

    start = perf_counter()
    started_reasoning = perf_counter() if response.is_thinking else None
    reasoning_time = None

    async for token in response:
        is_reasoning_token = isinstance(token, ReasoningToken)

        if isinstance(token, Event):
            event = token
            tool_events.append(event)
            if event.type == EventType.TOOL_MODEL_RESPONSE:
                tokens = []
                answer_text_tokens = []
                tool_text_tokens = []
                thinking_text_tokens = []
                inner_response = event.payload["response"]
                assert isinstance(inner_response, TextGenerationResponse)
                if inner_response.input_token_count:
                    input_token_count = inner_response.input_token_count
            elif event.type == EventType.TOOL_RESULT:
                tool_event_results.append(event)
                if "call" in event.payload:
                    completed_call_ids.add(event.payload["call"].id)
            else:
                tool_event_calls.append(event)
        else:
            if (
                display_reasoning_time
                and not is_reasoning_token
                and started_reasoning is not None
            ):
                reasoning_time = perf_counter() - started_reasoning
                started_reasoning = None

            text_token = token.token if isinstance(token, Token) else token
            if isinstance(token, ToolCallToken):
                tool_text_tokens.append(text_token)
            elif is_reasoning_token:
                if not started_reasoning:
                    started_reasoning = perf_counter()
                thinking_text_tokens.append(text_token)
            else:
                answer_text_tokens.append(text_token)

        tool_running_spinner = None
        if tool_event_calls or tool_event_results:
            tool_calling_names = [
                c.name
                for e in tool_event_calls
                for c in e.payload
                if c.id not in completed_call_ids
            ]

            tool_running_spinner = (
                Spinner(
                    theme.get_spinner("tool_running"),
                    text="[cyan]"
                    + theme._n(
                        "Running tool {tool_names}...",
                        "Running tools {tool_names}...",
                        len(tool_calling_names),
                    ).format(tool_names=", ".join(tool_calling_names))
                    + "[/cyan]",
                    style="cyan",
                    speed=1.0,
                )
                if tool_calling_names
                else None
            )

        elapsed = perf_counter() - start
        total_tokens += 1

        if ttft is None:
            ttft = elapsed
        if (
            ttnt is None
            and display_time_to_n_token
            and total_tokens >= display_time_to_n_token
        ):
            ttnt = elapsed

        ttsr = None
        if display_reasoning_time and reasoning_time:
            ttsr = reasoning_time

        if display_tokens and isinstance(token, Token):
            tokens.append(token)
        limit_answer_height = not getattr(
            args, "display_answer_height_expand", False
        )
        answer_height = getattr(args, "display_answer_height", 12)

        token_frames_promise = theme.tokens(
            lm.model_id,
            lm.tokenizer_config.tokens if lm.tokenizer_config else None,
            (
                lm.tokenizer_config.special_tokens
                if lm.tokenizer_config
                else None
            ),
            display_tokens,
            args.display_probabilities if dtokens_pick > 0 else False,
            dtokens_pick,
            # Which tokens to mark as interesting
            lambda dtoken: (
                (
                    dtoken.probability < args.display_probabilities_maximum
                    or len(
                        [
                            t
                            for t in dtoken.tokens
                            if t.id != dtoken.id
                            and t.probability
                            >= args.display_probabilities_sample_minimum
                        ]
                    )
                    > 0
                )
                if display_tokens
                and args.display_probabilities
                and args.display_probabilities_maximum > 0
                and args.display_probabilities_maximum > 0
                else None
            ),
            thinking_text_tokens,
            tool_text_tokens,
            answer_text_tokens,
            tokens or None,
            input_token_count,
            total_tokens,
            tool_events,
            tool_event_calls,
            tool_event_results,
            tool_running_spinner,
            ttft,
            ttnt,
            ttsr,
            elapsed,
            console.width,
            logger,
            event_stats,
            height=answer_height,
            tool_events_limit=tool_events_limit,
            limit_answer_height=limit_answer_height,
            maximum_frames=1,
            start_thinking=start_thinking,
        )

        token_frame_list = [
            token_frame async for token_frame in token_frames_promise
        ]

        token_frames = [token_frame_list[0]]

        for current_dtoken, frame in token_frames:
            _render_frame(
                args, console, live, frame, group, tokens_group_index
            )

            if current_dtoken and current_dtoken != last_current_dtoken:
                last_current_dtoken = current_dtoken
                if display_pause > 0:
                    await sleep(display_pause / 1000)
                elif frame_minimum_pause_ms > 0:
                    await sleep(
                        frame_minimum_pause_ms / 1000
                    )  # pragma: no cover - unreachable
            elif (
                dtokens_pick > 0
                and not args.display_probabilities
                and display_pause > 0
            ):
                await sleep(display_pause / 1000)

        if (
            dtokens_pick > 0
            and args.display_probabilities
            and token_frame_list
            and len(token_frame_list) > 0
        ):
            for current_dtoken, frame in token_frame_list[1:]:
                _render_frame(
                    args, console, live, frame, group, tokens_group_index
                )

                if current_dtoken and display_pause > 0:
                    await sleep(display_pause / 1000)
                elif frame_minimum_pause_ms > 0:
                    await sleep(frame_minimum_pause_ms / 1000)

    if stop_signal:
        stop_signal.set()


def _render_frame(
    args: Namespace,
    console: Console,
    live: Live,
    frame: RenderableType,
    group: Group | None = None,
    group_index: int | None = None,
) -> None:
    if group and group_index is not None:
        group.renderables[group_index] = frame
        live.refresh()
    else:
        live.update(frame)

    if args.record:
        now = datetime.now(timezone.utc)
        ts = now.strftime("%Y%m%d%H%M%S")
        ms = now.microsecond // 1000
        filename = f"avalan-screenshot-{ts}-{ms:03d}.svg"
        console.save_svg(filename, clear=True)
