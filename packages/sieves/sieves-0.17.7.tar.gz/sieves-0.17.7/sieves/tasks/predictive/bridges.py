"""Bridge base class and types."""

from __future__ import annotations

import abc
from collections import defaultdict
from collections.abc import Iterable
from typing import Any, Generic, TypeVar, override

from sieves.data import Doc
from sieves.engines import EngineInferenceMode, glix_

TaskPromptSignature = TypeVar("TaskPromptSignature", covariant=True)
TaskResult = TypeVar("TaskResult")
TaskBridge = TypeVar("TaskBridge", bound="Bridge[TaskPromptSignature, TaskResult, EngineInferenceMode]")  # type: ignore[valid-type]


class Bridge(Generic[TaskPromptSignature, TaskResult, EngineInferenceMode], abc.ABC):
    """Bridge base class."""

    def __init__(self, task_id: str, prompt_instructions: str | None, overwrite: bool):
        """Initialize new bridge.

        :param task_id: Task ID.
        :param prompt_instructions: Custom prompt instructions. If None, default instructions are used.
        :param overwrite: Whether to overwrite text with produced text. Considered only by bridges for tasks producing
            fluent text - like translation, summarization, PII masking, etc.
        """
        self._task_id = task_id
        self._custom_prompt_instructions = prompt_instructions
        self._overwrite = overwrite

    @property
    @abc.abstractmethod
    def _default_prompt_instructions(self) -> str:
        """Return default prompt instructions.

        Instructions are injected at the beginning of each prompt.

        :return: Default prompt instructions.
        """

    @property
    def _prompt_instructions(self) -> str:
        """Returns prompt instructions.

        :returns: If `_custom_prompt_instructions` is set, this is used. Otherwise, `_default_prompt_instructions` is
            used.
        """
        return self._custom_prompt_instructions or self._default_prompt_instructions

    @property
    @abc.abstractmethod
    def _prompt_example_template(self) -> str | None:
        """Return default prompt template for example injection.

        Examples are injected between instructions and conclusions.

        :return: Default prompt example template.
        """

    @property
    @abc.abstractmethod
    def _prompt_conclusion(self) -> str | None:
        """Return prompt conclusion.

        Prompt conclusions are injected at the end of each prompt.

        :return: Default prompt conclusion.
        """

    @property
    def prompt_template(self) -> str:
        """Return prompt template.

        Chains `_prompt_instructions`, `_prompt_example_template` and `_prompt_conclusion`.

        Note: different engines have different expectations as how a prompt should look like. E.g. outlines supports the
        Jinja 2 templating format for insertion of values and few-shot examples, whereas DSPy integrates these things in
        a different value in the workflow and hence expects the prompt not to include these things. Mind engine-specific
        expectations when creating a prompt template.
        :return str | None: Prompt template as string. None if not used by engine.
        """
        return f"""
        {self._custom_prompt_instructions or self._prompt_instructions}
        {self._prompt_example_template or ""}
        {self._prompt_conclusion or ""}
        """

    @property
    @abc.abstractmethod
    def prompt_signature(self) -> type[TaskPromptSignature] | TaskPromptSignature:
        """Create output signature.

        E.g.: `Signature` in DSPy, Pydantic objects in outlines, JSON schema in jsonformers.
        This is engine-specific.

        :return type[_TaskPromptSignature] | _TaskPromptSignature: Output signature object. This can be an instance
            (e.g. a regex string) or a class (e.g. a Pydantic class).
        """

    @property
    @abc.abstractmethod
    def inference_mode(self) -> EngineInferenceMode:
        """Return inference mode.

        :return EngineInferenceMode: Inference mode.
        """

    def extract(self, docs: Iterable[Doc]) -> Iterable[dict[str, Any]]:
        """Extract all values from doc instances that are to be injected into the prompts.

        :param docs: Docs to extract values from.
        :return Iterable[dict[str, Any]]: All values from doc instances that are to be injected into the prompts
        """
        return ({"text": doc.text if doc.text else None} for doc in docs)

    @abc.abstractmethod
    def integrate(self, results: Iterable[TaskResult], docs: Iterable[Doc]) -> Iterable[Doc]:
        """Integrate results into Doc instances.

        :param results: Results from prompt executable.
        :param docs: Doc instances to update.
        :return Iterable[Doc]: Updated doc instances.
        """

    @abc.abstractmethod
    def consolidate(self, results: Iterable[TaskResult], docs_offsets: list[tuple[int, int]]) -> Iterable[TaskResult]:
        """Consolidate results for document chunks into document results.

        :param results: Results per document chunk.
        :param docs_offsets: Chunk offsets per document. Chunks per document can be obtained with
            `results[docs_chunk_offsets[i][0]:docs_chunk_offsets[i][1]]`.
        :return Iterable[_TaskResult]: Results per document.
        """


class GliXBridge(Bridge[list[str], glix_.Result, glix_.InferenceMode]):
    """Bridge for GliX models."""

    def __init__(
        self,
        task_id: str,
        prompt_instructions: str | None,
        prompt_signature: tuple[str, ...] | list[str],
        inference_mode: glix_.InferenceMode,
        label_whitelist: tuple[str, ...] | None = None,
        only_keep_best: bool = False,
    ):
        """Initialize GliX bridge.

        :param task_id: Task ID.
        :param prompt_instructions: Custom prompt instructions. If None, default instructions are used.
        :param prompt_signature: Prompt signature.
        :param inference_mode: Inference mode.
        :param label_whitelist: Labels to record predictions for. If None, predictions for all labels are recorded.
        :param only_keep_best: Whether to only return the result with the highest score.
        """
        super().__init__(
            task_id=task_id,
            prompt_instructions=prompt_instructions,
            overwrite=False,
        )
        self._prompt_signature = prompt_signature
        self._inference_mode = inference_mode
        self._label_whitelist = label_whitelist
        self._has_scores = inference_mode in (
            glix_.InferenceMode.classification,
            glix_.InferenceMode.question_answering,
        )
        self._only_keep_best = only_keep_best
        self._pred_attr: str | None = None

    @override
    @property
    def _default_prompt_instructions(self) -> str:
        # GliNER doesn't support custom instructions.
        return ""

    @override
    @property
    def _prompt_example_template(self) -> str | None:
        return None

    @override
    @property
    def _prompt_conclusion(self) -> str | None:
        return None

    @override
    @property
    def prompt_signature(self) -> list[str]:
        return list(self._prompt_signature)

    @override
    @property
    def inference_mode(self) -> glix_.InferenceMode:
        return self._inference_mode

    @override
    def integrate(self, results: Iterable[glix_.Result], docs: Iterable[Doc]) -> Iterable[Doc]:
        for doc, result in zip(docs, results):
            if self._has_scores:
                doc.results[self._task_id] = []
                for res in sorted(result, key=lambda x: x["score"], reverse=True):
                    assert isinstance(res, dict)
                    doc.results[self._task_id].append((res[self._pred_attr], res["score"]))

                if self._only_keep_best:
                    doc.results[self._task_id] = doc.results[self._task_id][0]
            else:
                doc.results[self._task_id] = result
        return docs

    @override
    def consolidate(
        self, results: Iterable[glix_.Result], docs_offsets: list[tuple[int, int]]
    ) -> Iterable[glix_.Result]:
        results = list(results)

        # Determine label scores for chunks per document.
        for doc_offset in docs_offsets:
            # Prediction key exists: this is label-score situation. Extract scores and average.
            if self._has_scores:
                scores: dict[str, float] = defaultdict(lambda: 0)

                for res in results[doc_offset[0] : doc_offset[1]]:
                    seen_attrs: set[str] = set()

                    for entry in res:
                        assert isinstance(entry, dict)
                        # Fetch attribute name for predicted dict. Note that this assumes a (ATTR, score) structure.
                        if self._pred_attr is None:
                            self._pred_attr = [k for k in entry.keys() if k != "score"][0]
                        assert isinstance(self._pred_attr, str)
                        assert isinstance(entry[self._pred_attr], str)
                        assert isinstance(entry["score"], float)
                        label = entry[self._pred_attr]
                        assert isinstance(label, str)

                        # GliNER may return multiple results with the same attribute value (e.g. in classification:
                        # multiple scores for the same label). We ignore those.
                        if label in seen_attrs:
                            continue
                        seen_attrs.add(label)

                        # Ignore if whitelist set and predicted label isn't in whitelist.
                        if self._label_whitelist and label not in self._label_whitelist:
                            continue
                        scores[label] += entry["score"]

                # No predictions, yield empty list.
                if self._pred_attr is None:
                    yield []

                else:
                    # Average score, sort by it in descending order.
                    assert self._pred_attr is not None
                    sorted_scores: list[dict[str, str | float]] = sorted(
                        (
                            {self._pred_attr: attr, "score": score / (doc_offset[1] - doc_offset[0])}
                            for attr, score in scores.items()
                        ),
                        key=lambda x: x["score"],
                        reverse=True,
                    )
                    yield sorted_scores

            else:
                for res in results[doc_offset[0] : doc_offset[1]]:
                    yield res
