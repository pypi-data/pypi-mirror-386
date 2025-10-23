from ...entities import GenerationSettings
from ...entities import WeightType as WeightType
from ...model.transformer import TransformerModel

from abc import ABC
from contextlib import nullcontext

from torch import (
    Tensor,
    inference_mode,
)
from transformers import AsyncTextIteratorStreamer
from transformers.generation import StoppingCriteria
from transformers.tokenization_utils_base import BatchEncoding


class BaseNLPModel(TransformerModel, ABC):
    def _generate_output(
        self,
        inputs: dict[str, Tensor] | Tensor,
        settings: GenerationSettings,
        stopping_criterias: list[StoppingCriteria] | None = None,
        streamer: AsyncTextIteratorStreamer | None = None,
    ):
        eos_token_id = (
            settings.eos_token_id
            if settings.eos_token_id
            else (
                self._tokenizer.eos_token_id
                if not settings.forced_eos_token_id and self._tokenizer
                else None
            )
        )
        generation_kwargs = {
            "bos_token_id": settings.bos_token_id,
            "diversity_penalty": settings.diversity_penalty,
            "do_sample": settings.do_sample,
            "early_stopping": settings.early_stopping,
            "eos_token_id": eos_token_id,
            "forced_bos_token_id": settings.forced_bos_token_id,
            "forced_eos_token_id": settings.forced_eos_token_id,
            "max_length": settings.max_length,
            "max_new_tokens": settings.max_new_tokens,
            "max_time": settings.max_time,
            "min_length": settings.min_length,
            "min_new_tokens": settings.min_new_tokens,
            "min_p": settings.min_p,
            "num_beams": settings.num_beams,
            "num_beam_groups": settings.num_beam_groups,
            "num_return_sequences": settings.num_return_sequences,
            "output_attentions": settings.output_attentions,
            "output_hidden_states": settings.output_hidden_states,
            "output_logits": settings.output_logits,
            "output_scores": settings.output_scores,
            "pad_token_id": (
                settings.pad_token_id or self._tokenizer.eos_token_id
            ),
            "penalty_alpha": settings.penalty_alpha,
            "prompt_lookup_num_tokens": settings.prompt_lookup_num_tokens,
            "repetition_penalty": settings.repetition_penalty,
            "return_dict_in_generate": settings.return_dict_in_generate,
            "stop_strings": settings.stop_strings,
            "stopping_criteria": stopping_criterias,
            "streamer": streamer,
            "temperature": settings.temperature,
            "top_k": settings.top_k,
            "top_p": settings.top_p,
            "use_cache": settings.use_cache,
            "cache_implementation": settings.cache_strategy,
        }

        attention_mask: Tensor | None = None
        if settings.use_inputs_attention_mask:
            attention_mask = (
                inputs.get("attention_mask", None)
                if isinstance(inputs, BatchEncoding)
                else getattr(inputs, "attention_mask", None)
            )
            if attention_mask is not None:
                assert isinstance(attention_mask, Tensor)
                assert attention_mask.shape == inputs["input_ids"].shape
                generation_kwargs["attention_mask"] = attention_mask

        if (
            not settings.use_inputs_attention_mask
            or attention_mask is not None
        ):
            inputs.pop("attention_mask", None)

        if settings.forced_bos_token_id or settings.forced_eos_token_id:
            del generation_kwargs["bos_token_id"]
            del generation_kwargs["eos_token_id"]

        with (
            inference_mode()
            if not settings.enable_gradient_calculation
            else nullcontext()
        ):
            outputs = (
                self._model.generate(
                    inputs, tokenizer=self._tokenizer, **generation_kwargs
                )
                if isinstance(inputs, Tensor)
                else self._model.generate(
                    **inputs, tokenizer=self._tokenizer, **generation_kwargs
                )
            )
        return outputs
