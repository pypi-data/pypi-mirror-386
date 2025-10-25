"""LangChain engine wrapper for structured outputs using Pydantic."""

import asyncio
import enum
from collections.abc import Iterable, Sequence
from typing import Any, override

import langchain_core.language_models
import nest_asyncio
import pydantic

from sieves.engines.core import Executable, PydanticEngine

nest_asyncio.apply()

Model = langchain_core.language_models.BaseChatModel
PromptSignature = pydantic.BaseModel
Result = pydantic.BaseModel


class InferenceMode(enum.Enum):
    """Available inference modes."""

    structured = "structured"


class LangChain(PydanticEngine[PromptSignature, Result, Model, InferenceMode]):
    """Engine for LangChain."""

    @override
    @property
    def inference_modes(self) -> type[InferenceMode]:
        return InferenceMode

    @override
    @override
    def build_executable(
        self,
        inference_mode: InferenceMode,
        prompt_template: str | None,  # noqa: UP007
        prompt_signature: type[PromptSignature] | PromptSignature,
        fewshot_examples: Sequence[pydantic.BaseModel] = tuple(),
    ) -> Executable[Result | None]:
        assert isinstance(prompt_signature, type)
        cls_name = self.__class__.__name__
        template = self._create_template(prompt_template)
        model = self._model.with_structured_output(prompt_signature)

        def execute(values: Sequence[dict[str, Any]]) -> Iterable[Result | None]:
            """Execute prompts with engine for given values.

            :param values: Values to inject into prompts.
            :return Iterable[Result | None]: Results for prompts. Results are None if corresponding prompt failed.
            """
            match inference_mode:
                case InferenceMode.structured:

                    def generate(prompts: list[str]) -> Iterable[Result]:
                        try:
                            yield from asyncio.run(model.abatch(prompts, **self._inference_kwargs))

                        except Exception as err:
                            raise type(err)(
                                f"Encountered problem in parsing {cls_name} output. Double-check your prompts and "
                                f"examples."
                            ) from err

                    generator = generate
                case _:
                    raise ValueError(f"Inference mode {inference_mode} not supported by {cls_name} engine.")

            yield from self._infer(generator, template, values, fewshot_examples)

        return execute
