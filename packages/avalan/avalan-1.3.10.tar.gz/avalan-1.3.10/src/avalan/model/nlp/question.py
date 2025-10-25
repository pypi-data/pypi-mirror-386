from ...compat import override
from ...entities import Input
from ...model.engine import Engine
from ...model.nlp import BaseNLPModel
from ...model.vendor import TextGenerationVendor

from typing import Literal

from diffusers import DiffusionPipeline
from torch import argmax, inference_mode
from transformers import AutoModelForQuestionAnswering, PreTrainedModel
from transformers.tokenization_utils_base import BatchEncoding


class QuestionAnsweringModel(BaseNLPModel):
    @property
    def supports_sample_generation(self) -> bool:
        return False

    @property
    def supports_token_streaming(self) -> bool:
        return False

    def _load_model(
        self,
    ) -> PreTrainedModel | TextGenerationVendor | DiffusionPipeline:
        model = AutoModelForQuestionAnswering.from_pretrained(
            self._model_id,
            cache_dir=self._settings.cache_dir,
            subfolder=self._settings.subfolder or "",
            attn_implementation=self._settings.attention,
            trust_remote_code=self._settings.trust_remote_code,
            torch_dtype=Engine.weight(self._settings.weight_type),
            state_dict=self._settings.state_dict,
            local_files_only=self._settings.local_files_only,
            token=self._settings.access_token,
            device_map=self._device,
            tp_plan=Engine._get_tp_plan(self._settings.parallel),
            distributed_config=Engine._get_distributed_config(
                self._settings.distributed_config
            ),
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
        assert not system_prompt and not developer_prompt, (
            "Token classification model "
            + f"{self._model_id} does not support chat "
            + "templates"
        )
        _l = self._log
        _l(f"Tokenizing input {input}")
        inputs = self._tokenizer(input, context, return_tensors=tensor_format)
        inputs = inputs.to(self._model.device)
        return inputs

    @override
    async def __call__(
        self,
        input: Input,
        *,
        context: str,
        system_prompt: str | None = None,
        developer_prompt: str | None = None,
        skip_special_tokens: bool = True,
    ) -> str:
        assert self._tokenizer, (
            f"Model {self._model} can't be executed "
            + "without a tokenizer loaded first"
        )
        assert self._model, (
            f"Model {self._model} can't be executed, it "
            + "needs to be loaded first"
        )
        inputs = self._tokenize_input(
            input,
            system_prompt=system_prompt,
            developer_prompt=developer_prompt,
            context=context,
        )
        with inference_mode():
            outputs = self._model(**inputs)
        start_answer_logits = outputs.start_logits
        end_answer_logits = outputs.end_logits
        start = argmax(start_answer_logits)
        end = argmax(end_answer_logits)
        answer_ids = inputs["input_ids"][0, start : end + 1]
        answer = self._tokenizer.decode(
            answer_ids, skip_special_tokens=skip_special_tokens
        )
        return answer
