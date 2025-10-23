from ...cli import get_input
from ...entities import Token, TransformerEngineSettings
from ...model.hubs.huggingface import HuggingfaceHub
from ...model.nlp.text.generation import TextGenerationModel

from argparse import Namespace
from logging import Logger

from rich.console import Console
from rich.theme import Theme


async def tokenize(
    args: Namespace,
    console: Console,
    theme: Theme,
    hub: HuggingfaceHub,
    logger: Logger,
) -> list[Token] | None:
    assert args.tokenizer

    _, _i, _n = theme._, theme.icons, theme._n

    tokenizer_name_or_path = args.tokenizer
    with TextGenerationModel(
        tokenizer_name_or_path,
        settings=TransformerEngineSettings(
            device=args.device,
            cache_dir=hub.cache_dir,
            subfolder=getattr(args, "subfolder", None),
            tokenizer_subfolder=getattr(args, "tokenizer_subfolder", None),
            tokenizer_name_or_path=tokenizer_name_or_path,
            tokens=(
                args.token
                if args.token and isinstance(args.token, list)
                else None
            ),
            special_tokens=(
                args.special_token
                if args.special_token and isinstance(args.special_token, list)
                else None
            ),
            auto_load_model=False,
            auto_load_tokenizer=True,
            disable_loading_progress_bar=args.disable_loading_progress_bar,
            low_cpu_mem_usage=args.low_cpu_mem_usage,
            loader_class=args.loader_class,
            backend=args.backend,
            weight_type=args.weight_type,
        ),
        logger=logger,
    ) as lm:
        logger.debug("Loaded tokenizer %s", lm.tokenizer_config.__repr__())
        console.print(theme.tokenizer_config(lm.tokenizer_config))

        if args.save:
            paths = lm.save_tokenizer(args.save)
            total_files = len(paths)
            console.print(theme.saved_tokenizer_files(args.save, total_files))
            return

        tty_path = getattr(args, "tty", "/dev/tty") or "/dev/tty"

        input_string = get_input(
            console,
            _i["user_input"] + " ",
            echo_stdin=not args.no_repl,
            is_quiet=args.quiet,
            tty_path=tty_path,
        )
        if input_string:
            logger.debug("Loaded model %s", lm.config.__repr__())
            tokens = lm.tokenize(input_string)

            panel = theme.tokenizer_tokens(
                tokens,
                lm.tokenizer_config.tokens,
                lm.tokenizer_config.special_tokens,
                display_details=True,
            )
            console.print(panel)
