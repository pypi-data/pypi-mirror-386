from .....compat import override
from .....entities import (
    GenerationSettings,
    Input,
    TransformerEngineSettings,
)
from .....model.nlp.text.generation import TextGenerationModel
from .....model.response.text import TextGenerationResponse
from .....model.vendor import TextGenerationVendor
from .....tool.manager import ToolManager

from abc import ABC, abstractmethod
from contextlib import AsyncExitStack
from dataclasses import replace
from logging import Logger, getLogger
from typing import Literal

from diffusers import DiffusionPipeline
from tiktoken import encoding_for_model, get_encoding
from torch import Tensor
from transformers import PreTrainedModel
from transformers.tokenization_utils_base import BatchEncoding


class TextGenerationVendorModel(TextGenerationModel, ABC):
    _TIKTOKEN_DEFAULT_MODEL = "cl100k_base"

    def __init__(
        self,
        model_id: str,
        settings: TransformerEngineSettings | None = None,
        logger: Logger = getLogger(__name__),
        *,
        exit_stack: AsyncExitStack | None = None,
    ) -> None:
        settings = settings or TransformerEngineSettings()
        assert (
            settings.base_url or settings.access_token
        ), "API key needed for vendor"
        settings = replace(settings, enable_eval=False)
        super().__init__(model_id, settings, logger)
        self._exit_stack = exit_stack or AsyncExitStack()

    @abstractmethod
    def _load_model(
        self,
    ) -> PreTrainedModel | TextGenerationVendor | DiffusionPipeline:
        raise NotImplementedError()

    @property
    def supports_sample_generation(self) -> bool:
        return False

    @property
    def supports_token_streaming(self) -> bool:
        return True

    @property
    def uses_tokenizer(self) -> bool:
        return False

    def _tokenize_input(
        self,
        input: Input,
        context: str | None = None,
        tensor_format: Literal["pt"] = "pt",
        **kwargs,
    ) -> dict[str, Tensor] | BatchEncoding | Tensor:
        raise NotImplementedError()

    def input_token_count(
        self,
        input: Input,
        system_prompt: str | None = None,
        developer_prompt: str | None = None,
    ) -> int:
        try:
            encoding = encoding_for_model(self._model_id)
        except KeyError:
            encoding = get_encoding(self._TIKTOKEN_DEFAULT_MODEL)

        messages = self._messages(
            input, system_prompt, developer_prompt, tool=None
        )

        total_tokens = 0
        for message in messages:
            total_tokens += len(encoding.encode(message.content or ""))
        return total_tokens

    @override
    async def __call__(
        self,
        input: Input,
        system_prompt: str | None = None,
        developer_prompt: str | None = None,
        settings: GenerationSettings | None = None,
        *,
        tool: ToolManager | None = None,
    ) -> TextGenerationResponse:
        messages = self._messages(input, system_prompt, developer_prompt, tool)
        streamer = await self._model(
            self._model_id,
            messages,
            settings,
            tool=tool,
            use_async_generator=settings.use_async_generator,
        )
        gen_settings = settings or GenerationSettings()
        return TextGenerationResponse(
            streamer,
            logger=self._logger,
            generation_settings=gen_settings,
            settings=gen_settings,
            use_async_generator=gen_settings.use_async_generator,
        )
