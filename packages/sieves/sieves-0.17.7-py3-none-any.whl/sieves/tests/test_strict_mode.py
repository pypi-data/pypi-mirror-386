# mypy: ignore-errors
import pydantic
import pytest

from sieves import Doc, Pipeline
from sieves.engines import EngineType
from sieves.tasks.predictive import information_extraction


@pytest.mark.parametrize(
    "batch_runtime", (EngineType.dspy, EngineType.langchain, EngineType.outlines), indirect=["batch_runtime"]
)
@pytest.mark.parametrize("strict_mode", [True, False])
def test_strict_mode(batch_runtime, strict_mode):
    batch_runtime.generation_settings.strict_mode = strict_mode

    class Person(pydantic.BaseModel, frozen=True):
        name: str
        age: pydantic.PositiveInt

    pipe = Pipeline([
        information_extraction.InformationExtraction(
            entity_type=Person,
            model=batch_runtime.model,
            generation_settings=batch_runtime.generation_settings,
            batch_size=batch_runtime.batch_size,
        )
    ])

    docs: list[Doc] = []
    hit_exception = False
    if strict_mode:
        try:
            docs = list(pipe([Doc(text=".")]))
        except Exception:
            hit_exception = True
    if strict_mode is False:
        docs = list(pipe([Doc(text=".")]))

    if strict_mode and hit_exception:
        assert len(docs) == 0
    else:
        assert len(docs) == 1

    for doc in docs:
        assert "InformationExtraction" in doc.results
