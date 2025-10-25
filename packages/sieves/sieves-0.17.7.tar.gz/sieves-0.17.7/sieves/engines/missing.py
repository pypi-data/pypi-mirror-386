"""Fallback engine types when optional dependencies are unavailable."""

import enum
from collections.abc import Callable, Iterable, Sequence
from typing import Any, override

import pydantic

from sieves.engines.core import Engine

PromptSignature = Any
Model = Any
Result = Any


class InferenceMode(enum.Enum):
    """Placeholder mode for unsupported engines."""

    any = Any


class MissingEngine(Engine[PromptSignature, Result, Model, InferenceMode]):
    """Placeholder for engine that couldn't be imported due to missing dependencies."""

    @override
    @property
    def supports_few_shotting(self) -> bool:
        raise NotImplementedError

    @override
    @property
    def inference_modes(self) -> type[InferenceMode]:
        raise NotImplementedError

    @override
    def build_executable(
        self,
        inference_mode: InferenceMode,
        prompt_template: str | None,
        prompt_signature: type[PromptSignature] | PromptSignature,
        fewshot_examples: Sequence[pydantic.BaseModel] = (),
    ) -> Callable[[Iterable[dict[str, Any]]], Iterable[Result | None]]:
        raise NotImplementedError
