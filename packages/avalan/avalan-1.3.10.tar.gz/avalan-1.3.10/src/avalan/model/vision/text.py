from ...compat import override
from ...entities import (
    GenerationSettings,
    ImageTextGenerationLoaderClass,
    Input,
    MessageRole,
)
from ...model.engine import Engine
from ...model.transformer import TransformerModel
from ...model.vendor import TextGenerationVendor
from ...model.vision import BaseVisionModel

from typing import Literal

from diffusers import DiffusionPipeline
from PIL import Image
from torch import Tensor, inference_mode
from transformers import (
    AutoImageProcessor,
    AutoModelForImageTextToText,
    AutoModelForVision2Seq,
    AutoProcessor,
    Gemma3ForConditionalGeneration,
    PreTrainedModel,
    Qwen2VLForConditionalGeneration,
)
from transformers.tokenization_utils_base import BatchEncoding


class ImageToTextModel(TransformerModel):
    _processor: AutoImageProcessor | AutoProcessor

    def _load_model(
        self,
    ) -> PreTrainedModel | TextGenerationVendor | DiffusionPipeline:
        self._processor = AutoImageProcessor.from_pretrained(
            self._model_id,
            # default behavior in transformers v4.48
            use_fast=True,
        )
        model = AutoModelForVision2Seq.from_pretrained(
            self._model_id,
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
        context: str | None = None,
        tensor_format: Literal["pt"] = "pt",
        **kwargs,
    ) -> dict[str, Tensor] | BatchEncoding | Tensor:
        raise NotImplementedError()

    @override
    async def __call__(
        self,
        image_source: str | Image.Image,
        *,
        skip_special_tokens: bool = True,
        tensor_format: Literal["pt"] = "pt",
    ) -> str:
        image = BaseVisionModel._get_image(image_source)

        inputs = self._processor(images=image, return_tensors=tensor_format)
        inputs.to(self._device)

        with inference_mode():
            output_ids = self._model.generate(**inputs)

        output = self._tokenizer.decode(
            output_ids[0], skip_special_tokens=skip_special_tokens
        )
        return output


class ImageTextToTextModel(ImageToTextModel):
    _loaders: dict[ImageTextGenerationLoaderClass, type[PreTrainedModel]] = {
        "auto": AutoModelForImageTextToText,
        "qwen2": Qwen2VLForConditionalGeneration,
        "gemma3": Gemma3ForConditionalGeneration,
    }

    def _load_model(
        self,
    ) -> PreTrainedModel | TextGenerationVendor | DiffusionPipeline:
        assert (
            self._settings.loader_class in self._loaders
        ), f"Unrecognized loader {self._settings.loader_class}"

        self._processor = AutoProcessor.from_pretrained(
            self._model_id,
            use_fast=True,
        )

        loader = self._loaders[self._settings.loader_class]
        model = loader.from_pretrained(
            self._model_id,
            torch_dtype=Engine.weight(self._settings.weight_type),
            device_map=self._device,
            tp_plan=Engine._get_tp_plan(self._settings.parallel),
            distributed_config=Engine._get_distributed_config(
                self._settings.distributed_config
            ),
        )
        return model

    @override
    async def __call__(
        self,
        image_source: str | Image.Image,
        prompt: str,
        system_prompt: str | None = None,
        developer_prompt: str | None = None,
        settings: GenerationSettings | None = None,
        width: int | None = None,
        *,
        skip_special_tokens: bool = True,
        tensor_format: Literal["pt"] = "pt",
    ) -> str:
        image = BaseVisionModel._get_image(image_source).convert("RGB")
        assert image.width

        if width:
            ratio = width / image.width
            height = int(ratio * image.height)
            image = image.resize((width, height), Image.Resampling.LANCZOS)

        messages = []
        if system_prompt:
            messages.append(
                {
                    "role": str(MessageRole.SYSTEM),
                    "content": [{"type": "text", "text": system_prompt}],
                }
            )
        if developer_prompt:
            messages.append(
                {
                    "role": str(MessageRole.DEVELOPER),
                    "content": [{"type": "text", "text": developer_prompt}],
                }
            )
        messages.append(
            {
                "role": str(MessageRole.USER),
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": prompt},
                ],
            }
        )

        text = self._processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=settings.chat_settings.add_generation_prompt,
        )
        inputs = self._processor(
            text=[text],
            images=image,
            videos=None,
            padding=True,
            return_tensors=tensor_format,
        )
        if settings.use_inputs_attention_mask:
            inputs.pop("attention_mask", None)

        inputs.to(self._device)
        with inference_mode():
            generated_ids = self._model.generate(
                **inputs, max_new_tokens=settings.max_new_tokens
            )
        generated_ids_trimmed = [
            out_ids[len(in_ids) :]
            for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        output_text = self._processor.batch_decode(
            generated_ids_trimmed,
            skip_special_tokens=skip_special_tokens,
            clean_up_tokenization_spaces=False,
        )
        return output_text[0] if isinstance(output_text, list) else output_text
