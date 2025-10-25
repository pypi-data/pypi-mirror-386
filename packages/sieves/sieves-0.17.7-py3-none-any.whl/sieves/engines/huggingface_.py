"""Hugging Face transformers engine wrapper (zero-shot classification)."""

import enum
from collections.abc import Iterable, Sequence
from typing import Any, override

import jinja2
import pydantic
import transformers

from sieves.engines.core import Engine, Executable

PromptSignature = list[str]
Model = transformers.Pipeline
Result = dict[str, list[str] | list[float]]


class InferenceMode(enum.Enum):
    """Available inference modes."""

    zeroshot_cls = 0


class HuggingFace(Engine[PromptSignature, Result, Model, InferenceMode]):
    """Engine adapter around ``transformers.Pipeline`` for zero‑shot tasks."""

    @override
    @property
    def inference_modes(self) -> type[InferenceMode]:
        return InferenceMode

    @override
    @property
    def supports_few_shotting(self) -> bool:
        return True

    @override
    def build_executable(
        self,
        inference_mode: InferenceMode,
        prompt_template: str | None,
        prompt_signature: type[PromptSignature] | PromptSignature,
        fewshot_examples: Sequence[pydantic.BaseModel] = (),
    ) -> Executable[Result | None]:
        cls_name = self.__class__.__name__
        assert prompt_template, ValueError(f"prompt_template has to be provided to {cls_name} engine by task.")
        assert isinstance(prompt_signature, list)

        # Render template with few-shot examples. Note that we don't use extracted document values here, as HF zero-shot
        # pipelines only support one hypothesis template per call - and we want to batch, so our hypothesis template
        # will be document-invariant.
        fewshot_examples_dict = HuggingFace.convert_fewshot_examples(fewshot_examples)
        # Render hypothesis template with everything but text.
        template = jinja2.Template(prompt_template).render(**({"examples": fewshot_examples_dict}))

        def execute(values: Sequence[dict[str, Any]]) -> Iterable[Result]:
            """Execute prompts with engine for given values.

            :param values: Values to inject into prompts.
            :return Iterable[Result]: Results for prompts.
            """
            match inference_mode:
                case InferenceMode.zeroshot_cls:
                    yield from self._model(
                        sequences=[doc_values["text"] for doc_values in values],
                        candidate_labels=prompt_signature,
                        hypothesis_template=template,
                        multi_label=True,
                        **self._inference_kwargs,
                    )

                case _:
                    raise ValueError(f"Inference mode {inference_mode} not supported by {cls_name} engine.")

        return execute
