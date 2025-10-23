import logging
import time
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np
from PIL.Image import Image

from docling.datamodel.accelerator_options import AcceleratorOptions
from docling.datamodel.base_models import Page, VlmPrediction
from docling.datamodel.document import ConversionResult
from docling.datamodel.pipeline_options_vlm_model import (
    InlineVlmOptions,
    TransformersPromptStyle,
)
from docling.models.base_model import BaseVlmPageModel
from docling.models.utils.hf_model_download import HuggingFaceModelDownloadMixin
from docling.utils.accelerator_utils import decide_device
from docling.utils.profiling import TimeRecorder

_log = logging.getLogger(__name__)


class VllmVlmModel(BaseVlmPageModel, HuggingFaceModelDownloadMixin):
    """
    vLLM-backed vision-language model that accepts PIL images (or numpy arrays)
    via vLLM's multi_modal_data, with prompt formatting handled by formulate_prompt().
    """

    # --------- Allowlist of vLLM args ---------
    # SamplingParams (runtime generation controls)
    _VLLM_SAMPLING_KEYS = {
        # Core
        "max_tokens",
        "temperature",
        "top_p",
        "top_k",
        # Penalties
        "presence_penalty",
        "frequency_penalty",
        "repetition_penalty",
        # Stops / outputs
        "stop",
        "stop_token_ids",
        "skip_special_tokens",
        "spaces_between_special_tokens",
        # Search / length
        "n",
        "best_of",
        "length_penalty",
        "early_stopping",
        # Misc
        "logprobs",
        "prompt_logprobs",
        "min_p",
        "seed",
    }

    # LLM(...) / EngineArgs (engine/load-time controls)
    _VLLM_ENGINE_KEYS = {
        # Model/tokenizer/impl
        "tokenizer",
        "tokenizer_mode",
        "download_dir",
        # Parallelism / memory / lengths
        "tensor_parallel_size",
        "pipeline_parallel_size",
        "gpu_memory_utilization",
        "max_model_len",
        "max_num_batched_tokens",
        "kv_cache_dtype",
        "dtype",
        # Quantization (coarse switch)
        "quantization",
        # Multimodal limits
        "limit_mm_per_prompt",
        # Execution toggles
        "enforce_eager",
    }

    def __init__(
        self,
        enabled: bool,
        artifacts_path: Optional[Path],
        accelerator_options: AcceleratorOptions,
        vlm_options: InlineVlmOptions,
    ):
        self.enabled = enabled
        self.vlm_options = vlm_options

        self.llm = None
        self.sampling_params = None
        self.processor = None  # used for CHAT templating in formulate_prompt()
        self.device = "cpu"
        self.max_new_tokens = vlm_options.max_new_tokens
        self.temperature = vlm_options.temperature

        if not self.enabled:
            return

        from transformers import AutoProcessor
        from vllm import LLM, SamplingParams

        # Device selection
        self.device = decide_device(
            accelerator_options.device, supported_devices=vlm_options.supported_devices
        )
        _log.debug(f"Available device for VLM: {self.device}")

        # Resolve artifacts path / cache folder
        repo_cache_folder = vlm_options.repo_id.replace("/", "--")
        if artifacts_path is None:
            artifacts_path = self.download_models(
                self.vlm_options.repo_id, revision=self.vlm_options.revision
            )
        elif (artifacts_path / repo_cache_folder).exists():
            artifacts_path = artifacts_path / repo_cache_folder

        # --------- Strict split & validation of extra_generation_config ---------
        extra_cfg = self.vlm_options.extra_generation_config

        load_cfg = {k: v for k, v in extra_cfg.items() if k in self._VLLM_ENGINE_KEYS}
        gen_cfg = {k: v for k, v in extra_cfg.items() if k in self._VLLM_SAMPLING_KEYS}

        unknown = sorted(
            k
            for k in extra_cfg.keys()
            if k not in self._VLLM_ENGINE_KEYS and k not in self._VLLM_SAMPLING_KEYS
        )
        if unknown:
            _log.warning(
                "Ignoring unknown extra_generation_config keys for vLLM: %s", unknown
            )

        # --------- Construct LLM kwargs (engine/load-time) ---------
        llm_kwargs: Dict[str, Any] = {
            "model": str(artifacts_path),
            "model_impl": "transformers",
            "limit_mm_per_prompt": {"image": 1},
            "revision": self.vlm_options.revision,
            "trust_remote_code": self.vlm_options.trust_remote_code,
            **load_cfg,
        }

        if self.device == "cpu":
            llm_kwargs.setdefault("enforce_eager", True)
        else:
            llm_kwargs.setdefault(
                "gpu_memory_utilization", 0.3
            )  # room for other models

        # Quantization (kept as-is; coarse)
        if self.vlm_options.quantized and self.vlm_options.load_in_8bit:
            llm_kwargs.setdefault("quantization", "bitsandbytes")

        # Initialize vLLM LLM
        self.llm = LLM(**llm_kwargs)

        # Initialize processor for prompt templating (needed for CHAT style)
        self.processor = AutoProcessor.from_pretrained(
            artifacts_path,
            trust_remote_code=self.vlm_options.trust_remote_code,
            revision=self.vlm_options.revision,
        )

        # --------- SamplingParams (runtime) ---------
        self.sampling_params = SamplingParams(
            temperature=self.temperature,
            max_tokens=self.max_new_tokens,
            stop=(self.vlm_options.stop_strings or None),
            **gen_cfg,
        )

    def __call__(
        self, conv_res: ConversionResult, page_batch: Iterable[Page]
    ) -> Iterable[Page]:
        # If disabled, pass-through
        if not self.enabled:
            for page in page_batch:
                yield page
            return

        page_list = list(page_batch)
        if not page_list:
            return

        # Preserve original order
        original_order = page_list[:]

        # Separate valid/invalid
        valid_pages: list[Page] = []
        invalid_pages: list[Page] = []
        for page in page_list:
            assert page._backend is not None
            if page._backend.is_valid():
                valid_pages.append(page)
            else:
                invalid_pages.append(page)

        if valid_pages:
            with TimeRecorder(conv_res, "vlm"):
                images: list[Image] = []
                user_prompts: list[str] = []
                pages_with_images: list[Page] = []

                for page in valid_pages:
                    assert page.size is not None
                    hi_res_image = page.get_image(
                        scale=self.vlm_options.scale,
                        max_size=self.vlm_options.max_size,
                    )
                    if hi_res_image is None:
                        continue

                    images.append(hi_res_image)

                    # Define prompt structure
                    user_prompt = self.vlm_options.build_prompt(page.parsed_page)

                    user_prompts.append(user_prompt)
                    pages_with_images.append(page)

                if images:
                    predictions = list(self.process_images(images, user_prompts))
                    for page, prediction in zip(pages_with_images, predictions):
                        page.predictions.vlm_response = prediction

        # Yield in original order
        for page in original_order:
            yield page

    def process_images(
        self,
        image_batch: Iterable[Union[Image, np.ndarray]],
        prompt: Union[str, list[str]],
    ) -> Iterable[VlmPrediction]:
        """Process images in a single batched vLLM inference call."""
        import numpy as np
        from PIL import Image as PILImage

        # -- Normalize images to RGB PIL
        pil_images: list[Image] = []
        for img in image_batch:
            if isinstance(img, np.ndarray):
                if img.ndim == 3 and img.shape[2] in (3, 4):
                    pil_img = PILImage.fromarray(img.astype(np.uint8))
                elif img.ndim == 2:
                    pil_img = PILImage.fromarray(img.astype(np.uint8), mode="L")
                else:
                    raise ValueError(f"Unsupported numpy array shape: {img.shape}")
            else:
                pil_img = img
            if pil_img.mode != "RGB":
                pil_img = pil_img.convert("RGB")
            pil_images.append(pil_img)

        if not pil_images:
            return

        # Normalize prompts
        if isinstance(prompt, str):
            user_prompts = [prompt] * len(pil_images)
        elif isinstance(prompt, list):
            if len(prompt) != len(pil_images):
                raise ValueError(
                    f"Number of prompts ({len(prompt)}) must match number of images ({len(pil_images)})"
                )
            user_prompts = prompt
        else:
            raise ValueError(f"prompt must be str or list[str], got {type(prompt)}")

        # Format prompts
        prompts: list[str] = [self.formulate_prompt(up) for up in user_prompts]

        # Build vLLM inputs
        llm_inputs = [
            {"prompt": p, "multi_modal_data": {"image": im}}
            for p, im in zip(prompts, pil_images)
        ]

        # Generate
        assert self.llm is not None and self.sampling_params is not None
        start_time = time.time()
        outputs = self.llm.generate(llm_inputs, sampling_params=self.sampling_params)  # type: ignore
        generation_time = time.time() - start_time

        # Optional debug
        if outputs:
            try:
                num_tokens = len(outputs[0].outputs[0].token_ids)
                _log.debug(f"Generated {num_tokens} tokens in {generation_time:.2f}s.")
            except Exception:
                pass

        # Emit predictions
        for output in outputs:
            text = output.outputs[0].text if output.outputs else ""
            decoded_text = self.vlm_options.decode_response(text)
            yield VlmPrediction(text=decoded_text, generation_time=generation_time)
