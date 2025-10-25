"""GliX engine wrapper built on top of GLiNER multi‑task pipelines."""

import enum
import warnings
from collections.abc import Iterable, Sequence
from typing import Any, override

import gliner.multitask.base
import jinja2
import pydantic

from sieves.engines.core import Engine, Executable
from sieves.engines.types import GenerationSettings

PromptSignature = list[str]
Model = gliner.model.GLiNER
Result = list[dict[str, str | float]] | str


class InferenceMode(enum.Enum):
    """Available inference modes."""

    ner = gliner.config.GLiNERConfig
    classification = gliner.multitask.GLiNERClassifier
    question_answering = gliner.multitask.GLiNERQuestionAnswerer
    information_extraction = gliner.multitask.GLiNEROpenExtractor
    summarization = gliner.multitask.GLiNERSummarizer
    relation_extraction = gliner.multitask.GLiNERRelationExtractor


class GliX(Engine[PromptSignature, Result, Model, InferenceMode]):
    """Engine adapter for GLiNER's multitask utilities (NER, CLS, QA, etc.)."""

    def __init__(self, model: Model, generation_settings: GenerationSettings):
        """Initialize GliX engine wrapper with model and settings."""
        super().__init__(model, generation_settings)
        self._model_wrappers: dict[InferenceMode, gliner.multitask.base.GLiNERBasePipeline] = {}

    @override
    @property
    def inference_modes(self) -> type[InferenceMode]:
        return InferenceMode

    @override
    @property
    def supports_few_shotting(self) -> bool:
        return False

    @override
    def build_executable(
        self,
        inference_mode: InferenceMode,
        prompt_template: str | None,
        prompt_signature: type[PromptSignature] | PromptSignature,
        fewshot_examples: Sequence[pydantic.BaseModel] = (),
    ) -> Executable[Result]:
        assert isinstance(prompt_signature, list)
        cls_name = self.__class__.__name__
        if len(list(fewshot_examples)):
            warnings.warn(f"Few-shot examples are not supported by engine {cls_name}.")

        # Lazily initialize multi-task wrapper for underlying GliNER model.
        if inference_mode not in self._model_wrappers:
            self._model_wrappers[inference_mode] = inference_mode.value(model=self._model)

        model = self._model_wrappers[inference_mode]

        # Overwrite prompt default template, if template specified. Note that this is a static prompt and GliX doesn't
        # do few-shotting, so we don't inject anything into the template.
        if prompt_template:
            self._model.prompt = jinja2.Template(prompt_template).render()

        def execute(values: Sequence[dict[str, Any]]) -> Iterable[Result]:
            """Execute prompts with engine for given values.

            :param values: Values to inject into prompts.
            :return Iterable[Result]: Results for prompts.
            """
            try:
                params: dict[InferenceMode, dict[str, Any]] = {
                    InferenceMode.classification: {"classes": prompt_signature, "multi_label": True},
                    InferenceMode.question_answering: {"questions": prompt_signature},
                    InferenceMode.summarization: {},
                    InferenceMode.ner: {"entity_types": prompt_signature},
                }
                selected_params = params[inference_mode]  # Select parameters based on inference mode
            except KeyError:
                raise ValueError(f"Inference mode {inference_mode} not supported by {cls_name} engine.")

            texts = [val["text"] for val in values]
            if inference_mode == InferenceMode.ner:
                yield from self._model.batch_predict_entities(texts=texts, labels=selected_params["entity_types"])
            else:
                assert isinstance(selected_params, dict)
                yield from model(texts, **(selected_params | self._inference_kwargs))

        return execute
