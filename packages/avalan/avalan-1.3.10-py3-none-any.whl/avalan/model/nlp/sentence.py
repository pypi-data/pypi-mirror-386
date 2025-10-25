from ...compat import override
from ...entities import Input
from ...model.engine import Engine
from ...model.nlp import BaseNLPModel
from ...model.vendor import TextGenerationVendor

from contextlib import nullcontext
from typing import Literal

from diffusers import DiffusionPipeline
from numpy import ndarray
from torch import inference_mode
from transformers import PreTrainedModel
from transformers.tokenization_utils_base import BatchEncoding


class SentenceTransformerModel(BaseNLPModel):
    @property
    def supports_sample_generation(self) -> bool:
        return False

    @property
    def supports_token_streaming(self) -> bool:
        return False

    @property
    def uses_tokenizer(self) -> bool:
        return True

    def token_count(self, input: str) -> int:
        token_ids = self.tokenizer.encode(input, add_special_tokens=False)
        return len(token_ids)

    def _load_model(
        self,
    ) -> PreTrainedModel | TextGenerationVendor | DiffusionPipeline:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(
            self._model_id,
            cache_folder=self._settings.cache_dir,
            device=self._device,
            trust_remote_code=self._settings.trust_remote_code,
            local_files_only=self._settings.local_files_only,
            token=self._settings.access_token,
            model_kwargs={
                "attn_implementation": self._settings.attention,
                "torch_dtype": Engine.weight(self._settings.weight_type),
                "low_cpu_mem_usage": (
                    True if self._device else self._settings.low_cpu_mem_usage
                ),
                "device_map": self._device,
                "tp_plan": Engine._get_tp_plan(self._settings.parallel),
                "distributed_config": Engine._get_distributed_config(
                    self._settings.distributed_config
                ),
            },
            backend="torch",
            similarity_fn_name=None,
            truncate_dim=None,
        )
        return model

    def _tokenize_input(
        self,
        input: Input,
        system_prompt: str | None,
        developer_prompt: str | None = None,
        context: str | None = None,
        tensor_format: Literal["pt"] = "pt",
        chat_template_settings: dict[str, object] | None = None,
    ) -> BatchEncoding:
        raise NotImplementedError()

    @override
    async def __call__(
        self, input: Input, *args, enable_gradient_calculation: bool = False
    ) -> ndarray:
        assert self._model, (
            f"Model {self._model} can't be executed, it "
            + "needs to be loaded first"
        )
        assert isinstance(input, str) or isinstance(input, list)
        with (
            inference_mode()
            if not enable_gradient_calculation
            else nullcontext()
        ):
            embeddings = self._model.encode(
                input, convert_to_numpy=True, show_progress_bar=False
            )
        return embeddings
