from ..entities import (
    EngineSettings,
    Input,
    ModelConfig,
    ParallelStrategy,
    SentenceTransformerModelConfig,
    TokenizerConfig,
    WeightType,
)
from ..model import (
    EngineResponse,
    ModelAlreadyLoadedException,
    TokenizerAlreadyLoadedException,
    TokenizerNotSupportedException,
)
from ..model.vendor import TextGenerationVendor

import asyncio
from abc import ABC, abstractmethod
from contextlib import AsyncExitStack
from importlib.util import find_spec
from logging import ERROR, Logger, getLogger
from typing import Any, Final, Literal

from diffusers import DiffusionPipeline
from torch import (
    bfloat16,
    cuda,
    dtype,
    float16,
    float32,
    float64,
    int8,
    int16,
    int32,
    int64,
    uint8,
)
from torch import (
    bool as tbool,
)
from torch.backends import mps
from transformers import (
    PreTrainedModel,
    PreTrainedTokenizer,
    PreTrainedTokenizerFast,
)
from transformers import logging as transformers_logging
from transformers.utils.logging import (
    disable_progress_bar,
    enable_progress_bar,
)


class Engine(ABC):
    _device: str
    _logger: Logger
    _model_id: str | None
    _settings: EngineSettings
    _transformers_logging_logger: Logger
    _transformers_logging_level: int
    _loaded_model: bool = False
    _loaded_tokenizer: bool = False
    _tokenizer: PreTrainedTokenizer | PreTrainedTokenizerFast | None = None
    _model: (
        PreTrainedModel | TextGenerationVendor | DiffusionPipeline | None
    ) = None
    _config: ModelConfig | SentenceTransformerModelConfig | None = None
    _tokenizer_config: TokenizerConfig | None = None
    _parameter_types: set[str] | None = None
    _parameter_count: int | None = None
    _exit_stack: AsyncExitStack = AsyncExitStack()

    DTYPE_SIZES: dict[str, int] = {
        "bool": 1,
        "bfloat16": 2,
        "float16": 2,
        "float32": 4,
        "float64": 8,
        "int8": 1,
        "int16": 2,
        "i32": 4,
        "i64": 8,
        "ui8": 1,
    }

    _WEIGHTS: Final[dict[str, Literal["auto"] | dtype]] = {
        "bool": tbool,
        "bf16": bfloat16,
        "f16": float16,
        "fp16": float16,
        "f32": float32,
        "fp32": float32,
        "f64": float64,
        "fp64": float64,
        "i8": int8,
        "i16": int16,
        "i32": int32,
        "i64": int64,
        "ui8": uint8,
        "auto": "auto",
    }

    @staticmethod
    def _get_tp_plan(
        parallel: ParallelStrategy | dict[str, ParallelStrategy] | None,
    ) -> str | dict[str, str] | None:
        if parallel is None:
            return None
        if isinstance(parallel, dict):
            return {k: v.value for k, v in parallel.items()}
        return parallel.value

    @staticmethod
    def _get_distributed_config(
        distributed_config: dict[str, object] | None,
    ) -> dict[str, object] | None:
        if distributed_config is None:
            return None
        config = {"enable_expert_parallel": False}
        config.update(distributed_config)
        return config

    @staticmethod
    def weight(weight_type: WeightType) -> Literal["auto"] | dtype:
        return Engine._WEIGHTS.get(weight_type, "auto")

    def __init__(
        self,
        model_id: str | None,
        settings: EngineSettings | None = None,
        logger: Logger = getLogger(__name__),
    ):
        self._logger = logger
        self._model_id = model_id
        self._settings = settings if settings else EngineSettings()
        self._device = (
            self._settings.device
            if self._settings.device
            else Engine.get_default_device()
        )
        self._transformers_logging_logger = (
            transformers_logging.get_logger()
            if self._settings.change_transformers_logging_level
            else None
        )
        self._transformers_logging_level = (
            self._transformers_logging_logger.level
            if self._settings.change_transformers_logging_level
            else None
        )

        auto_load_tokenizer = (
            self.uses_tokenizer and self._settings.auto_load_tokenizer
        )
        if self._settings.auto_load_model or auto_load_tokenizer:
            self._load(
                load_tokenizer=auto_load_tokenizer,
                tokenizer_name_or_path=(
                    self._settings.tokenizer_name_or_path
                    if auto_load_tokenizer
                    else None
                ),
            )

    @property
    def uses_tokenizer(self) -> bool:
        return False

    @property
    def config(
        self,
    ) -> ModelConfig | SentenceTransformerModelConfig | None:
        return self._config

    @property
    def model(
        self,
    ) -> PreTrainedModel | TextGenerationVendor | DiffusionPipeline | None:
        return self._model

    @property
    def model_type(self) -> str:
        return type(self).__name__

    @property
    def model_id(self) -> str | None:
        return self._model_id

    @property
    def parameter_count(self) -> int | None:
        return self._parameter_count

    @property
    def parameter_types(self) -> set[str] | None:
        return self._parameter_types

    @property
    def tokenizer_config(self) -> TokenizerConfig | None:
        return self._tokenizer_config

    @property
    def tokenizer(
        self,
    ) -> PreTrainedTokenizer | PreTrainedTokenizerFast | None:
        return self._tokenizer

    @abstractmethod
    async def __call__(self, input: Input, **kwargs) -> EngineResponse:
        raise NotImplementedError()

    @abstractmethod
    def _load_model(
        self,
    ) -> PreTrainedModel | TextGenerationVendor | DiffusionPipeline:
        raise NotImplementedError()

    def is_runnable(self, device: str | None = None) -> bool | None:
        if (
            self._parameter_types is None
            or not self._parameter_types
            or self._parameter_count is None
            or self._parameter_count <= 0
        ):
            return None

        if not device:
            device = Engine.get_default_device()

        available = Engine._get_device_memory(device)
        if not available:
            return False

        dtype = next(iter(self._parameter_types))
        bytes_per_param = self.DTYPE_SIZES.get(dtype, 4)
        required = self._parameter_count * bytes_per_param
        return required <= available

    def _load_tokenizer_with_tokens(
        self, tokenizer_name_or_path: str | None, use_fast: bool = True
    ) -> PreTrainedTokenizer | PreTrainedTokenizerFast:
        raise (
            TokenizerNotSupportedException()
            if not self.uses_tokenizer()
            else NotImplementedError()
        )

    def __enter__(self):
        _l = self._log
        if (
            self._transformers_logging_logger
            and self._transformers_logging_level != ERROR
        ):
            transformers_logging.set_verbosity_error()
            _l(
                "Changed transformers logging level from %s to %s",
                self._transformers_logging_level,
                self._transformers_logging_logger.level,
            )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any | None,
    ):
        _l = self._log
        if (
            self._transformers_logging_logger
            and self._transformers_logging_level
            and self._transformers_logging_level != ERROR
        ):
            self._transformers_logging_logger.setLevel(
                self._transformers_logging_level
            )
            _l(
                "Restored transformers logging level to %s",
                self._transformers_logging_level,
            )
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(self._exit_stack.aclose())
        else:
            loop.create_task(self._exit_stack.aclose())
        return False

    def _load(
        self, *args, load_tokenizer: bool, tokenizer_name_or_path: str | None
    ) -> None:
        if (
            self._settings.auto_load_model
            and hasattr(self, "_loaded_model")
            and self._loaded_model
        ):
            raise ModelAlreadyLoadedException()
        elif (
            load_tokenizer
            and hasattr(self, "_loaded_tokenizer")
            and self._loaded_tokenizer
        ):
            raise TokenizerAlreadyLoadedException()

        _l = self._log

        if self._settings.disable_loading_progress_bar:
            disable_progress_bar()

        if load_tokenizer and self._model_id:
            _l(
                "Loading tokenizer %s",
                tokenizer_name_or_path or self._model_id,
            )
            self._tokenizer = self._load_tokenizer_with_tokens(
                tokenizer_name_or_path or self._model_id, use_fast=True
            )
            assert isinstance(
                self._tokenizer, PreTrainedTokenizer
            ) or isinstance(self._tokenizer, PreTrainedTokenizerFast), (
                "Unexpected pretrained tokenizer type: "
                + f"{type(self._tokenizer)}"
            )
            _l("Loaded tokenizer %s", self._tokenizer.name_or_path)

            self._loaded_tokenizer = True

        is_mlx = False
        is_sentence_transformer = False

        if self._settings.auto_load_model:
            _l(
                "Loading pretrained model %s from cache %s",
                self._model_id or str(self._model),
                self._settings.cache_dir,
            )
            self._model = self._load_model()

            if not isinstance(self._model, PreTrainedModel) and not isinstance(
                self._model, TextGenerationVendor
            ):
                if find_spec("mlx"):
                    from mlx.nn import Module

                    is_mlx = isinstance(self._model, Module)

                if find_spec("sentence_transformers"):
                    from sentence_transformers import SentenceTransformer

                    is_sentence_transformer = isinstance(
                        self._model, SentenceTransformer
                    )

            assert (
                isinstance(self._model, PreTrainedModel)
                or isinstance(self._model, TextGenerationVendor)
                or isinstance(self._model, DiffusionPipeline)
                or is_mlx
                or is_sentence_transformer
            ), f"Unexpected pretrained model type: {type(self._model)}"

            _l(
                "Loaded pretrained model %s from cache %s",
                self._model_id,
                self._settings.cache_dir,
            )

            if self._settings.enable_eval:
                _l("Setting model %s in eval mode", self._model_id)
                self._model.eval()

            if self._tokenizer and (
                self._settings.tokens or self._settings.special_tokens
            ):
                total_tokens = len(self._tokenizer)
                _l(
                    "Resizing embedding matrix to %s tokens for model %s",
                    total_tokens,
                    self._model_id,
                )
                self._model.resize_token_embeddings(total_tokens)
                _l(
                    "Resized embedding matrix to %s tokens for model %s",
                    total_tokens,
                    self._model_id,
                )

            self._loaded_model = True

        self._parameter_types = (
            {
                str(param.dtype).replace("torch.", "")
                for param in self._model.parameters()
            }
            if not is_mlx
            and self._model
            and hasattr(self._model, "parameters")
            else None
        )
        self._parameter_count = (
            sum(p.numel() for p in self._model.parameters())
            if not is_mlx
            and self._model
            and hasattr(self._model, "parameters")
            else None
        )

        if self._model and not self._config:
            config: ModelConfig | SentenceTransformerModelConfig | None = None
            mc = (
                self._model.config
                if hasattr(self._model, "config")
                else (
                    self._model[0].auto_model.config
                    if is_sentence_transformer
                    else None
                )
            )

            if mc:
                config = ModelConfig(
                    architectures=getattr(mc, "architectures", None),
                    attribute_map=getattr(mc, "attribute_map", None),
                    bos_token_id=getattr(mc, "bos_token_id", None),
                    bos_token=(
                        self._tokenizer.decode(mc.bos_token_id)
                        if self._tokenizer
                        and hasattr(mc, "bos_token_id")
                        and mc.bos_token_id
                        else None
                    ),
                    decoder_start_token_id=getattr(
                        mc, "decoder_start_token_id", None
                    ),
                    eos_token_id=getattr(mc, "eos_token_id", None),
                    eos_token=(
                        self._tokenizer.decode(mc.eos_token_id)
                        if self._tokenizer and mc.eos_token_id
                        else None
                    ),
                    finetuning_task=getattr(mc, "finetuning_task", None),
                    hidden_size=(
                        mc.hidden_size if hasattr(mc, "hidden_size") else None
                    ),
                    hidden_sizes=(
                        mc.hidden_sizes
                        if hasattr(mc, "hidden_sizes")
                        else None
                    ),
                    keys_to_ignore_at_inference=(
                        mc.keys_to_ignore_at_inference
                        if hasattr(mc, "keys_to_ignore_at_inference")
                        else None
                    ),
                    loss_type=(
                        mc.loss_type if hasattr(mc, "loss_type") else None
                    ),
                    max_position_embeddings=(
                        mc.max_position_embeddings
                        if hasattr(mc, "max_position_embeddings")
                        else None
                    ),
                    model_type=getattr(mc, "model_type", None),
                    num_attention_heads=(
                        mc.num_attention_heads
                        if hasattr(mc, "num_attention_heads")
                        else None
                    ),
                    num_hidden_layers=(
                        mc.num_hidden_layers
                        if hasattr(mc, "num_hidden_layers")
                        else None
                    ),
                    num_labels=getattr(mc, "num_labels", None),
                    output_attentions=getattr(mc, "output_attentions", None),
                    output_hidden_states=getattr(
                        mc, "output_hidden_states", None
                    ),
                    pad_token_id=getattr(mc, "pad_token_id", None),
                    pad_token=(
                        self._tokenizer.decode(mc.pad_token_id)
                        if self._tokenizer and mc.pad_token_id
                        else None
                    ),
                    prefix=getattr(mc, "prefix", None),
                    sep_token_id=getattr(mc, "sep_token_id", None),
                    sep_token=(
                        self._tokenizer.decode(mc.sep_token_id)
                        if self._tokenizer and mc.sep_token_id
                        else None
                    ),
                    state_size=(
                        len(self._model.state_dict().keys())
                        if hasattr(self._model, "state_dict")
                        and self._model.state_dict
                        else 0
                    ),
                    task_specific_params=getattr(
                        mc, "task_specific_params", None
                    ),
                    torch_dtype=(
                        str(mc.torch_dtype)
                        if hasattr(mc, "torch_dtype")
                        else None
                    ),
                    vocab_size=(
                        mc.vocab_size if hasattr(mc, "vocab_size") else None
                    ),
                    tokenizer_class=getattr(mc, "tokenizer_class", None),
                )

            if is_sentence_transformer and config:
                config = SentenceTransformerModelConfig(
                    backend=self._model.backend,
                    similarity_function=self._model.similarity_fn_name,
                    truncate_dimension=self._model.truncate_dim,
                    transformer_model_config=config,
                )

            self._config = config

        if self._tokenizer and not self._tokenizer_config:
            self._tokenizer_config = TokenizerConfig(
                name_or_path=self._tokenizer.name_or_path,
                tokens=self._settings.tokens,
                special_tokens=self._tokenizer.all_special_tokens,
                tokenizer_model_max_length=getattr(
                    self._tokenizer, "model_max_length", 0
                ),
                fast=isinstance(self._tokenizer, PreTrainedTokenizerFast),
            )

        if self._settings.disable_loading_progress_bar:
            enable_progress_bar()

    @staticmethod
    def get_default_device() -> str:
        return (
            "cuda"
            if cuda.is_available()
            else "mps" if mps.is_available() else "cpu"
        )

    @staticmethod
    def _get_device_memory(device: str) -> int:
        """Return available memory for device in bytes."""
        if device.startswith("cuda") or device == "cuda":
            if not cuda.is_available():
                return 0
            index = (
                int(device.split(":", 1)[1])
                if ":" in device
                else cuda.current_device()
            )
            return cuda.get_device_properties(index).total_memory

        from psutil import virtual_memory

        if device == "mps" and mps.is_available():
            return virtual_memory().total
        return virtual_memory().total

    def _log(self, message: str, *args: object) -> None:
        self._logger.debug(
            f"<Engine %s (%s)> {message}",
            type(self).__name__,
            self._model_id,
            *args,
        )
