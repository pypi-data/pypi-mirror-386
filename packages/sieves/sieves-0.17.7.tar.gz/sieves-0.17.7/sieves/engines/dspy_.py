"""DSPy engine integration for Sieves."""

import asyncio
import enum
from collections.abc import Iterable, Sequence
from typing import Any, override

import dspy
import nest_asyncio
import pydantic

from sieves.engines.core import Engine, Executable
from sieves.engines.types import GenerationSettings

PromptSignature = dspy.Signature | dspy.Module
Model = dspy.LM | dspy.BaseLM
Result = dspy.Prediction


nest_asyncio.apply()


class InferenceMode(enum.Enum):
    """Available inference modes.

    See https://dspy.ai/#__tabbed_2_6 for more information and examples.
    """

    # Default inference mode.
    predict = dspy.Predict
    # CoT-style inference.
    chain_of_thought = dspy.ChainOfThought
    # Agentic, i.e. with tool use.
    react = dspy.ReAct
    # For multi-stage pipelines within a task. This is handled differently than the other supported modules: dspy.Module
    # serves as both the signature as well as the inference generator.
    module = dspy.Module


class DSPy(Engine[PromptSignature, Result, Model, InferenceMode]):
    """Engine for DSPy."""

    def __init__(self, model: Model, generation_settings: GenerationSettings):
        """Initialize engine.

        :param model: Model to run. Note: DSPy only runs with APIs. If you want to run a model locally from v2.5
            onwards, serve it with OLlama - see here: # https://dspy.ai/learn/programming/language_models/?h=models#__tabbed_1_5.
            In a nutshell:
            > curl -fsSL https://ollama.ai/install.sh | sh
            > ollama run MODEL_ID
            > `model = dspy.LM(MODEL_ID, api_base='http://localhost:11434', api_key='')`
        :param generation_settings: Settings including DSPy configuration in `config_kwargs`.
        """
        super().__init__(model, generation_settings)
        cfg = generation_settings.config_kwargs or {}
        dspy.configure(lm=model, **cfg)

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
        prompt_template: str | None,  # noqa: UP007
        prompt_signature: type[PromptSignature] | PromptSignature,
        fewshot_examples: Sequence[pydantic.BaseModel] = tuple(),
    ) -> Executable[Result | None]:
        # Note: prompt_template is ignored here, as DSPy doesn't use it directly (only prompt_signature_description).
        assert isinstance(prompt_signature, type)

        # Handled differently than the other supported modules: dspy.Module serves as both the signature as well as
        # the inference generator.
        if inference_mode == InferenceMode.module:
            assert isinstance(prompt_signature, dspy.Module), ValueError(
                "In inference mode 'module' the provided prompt signature has to be of type dspy.Module."
            )
            generator = inference_mode.value(**self._init_kwargs)
        else:
            assert issubclass(prompt_signature, dspy.Signature)
            generator = inference_mode.value(signature=prompt_signature, **self._init_kwargs)

        def execute(values: Sequence[dict[str, Any]]) -> Iterable[Result | None]:
            """Execute structured generation with DSPy.

            :params values: Values to inject into prompts.
            :returns: Results for prompts.
            """
            # Compile predictor with few-shot examples.
            fewshot_examples_dicts = DSPy.convert_fewshot_examples(fewshot_examples)
            generator_fewshot: dspy.Module | None = None
            if len(fewshot_examples_dicts):
                examples = [dspy.Example(**fs_example) for fs_example in fewshot_examples_dicts]
                generator_fewshot = dspy.LabeledFewShot(k=len(examples)).compile(student=generator, trainset=examples)

            try:
                gen = generator_fewshot or generator
                calls = [gen.acall(**doc_values, **self._inference_kwargs) for doc_values in values]
                yield from asyncio.run(self._execute_async_calls(calls))

            except Exception as err:
                if self._strict_mode:
                    raise type(err)(
                        "Encountered problem when executing prompt. Ensure your few-shot examples and document "
                        "chunks contain sensible information."
                    ) from err
                else:
                    yield from [None] * len(values)

        return execute
