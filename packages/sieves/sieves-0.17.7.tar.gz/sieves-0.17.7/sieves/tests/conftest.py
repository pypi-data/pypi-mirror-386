# mypy: ignore-errors
import os
from functools import cache
from typing import Any, NamedTuple

import dspy
import gliner.multitask
import outlines
import pytest
import tokenizers
import transformers
from langchain_openai import ChatOpenAI

from sieves import Doc
from sieves.engines.engine_type import EngineType
from sieves.engines.utils import GenerationSettings
from sieves.tasks.types import Model


class Runtime(NamedTuple):
    model: Model
    generation_settings: GenerationSettings
    batch_size: int


@pytest.fixture(scope="session")
def tokenizer() -> tokenizers.Tokenizer:
    return tokenizers.Tokenizer.from_pretrained("gpt2")


@cache
def make_model(engine_type: EngineType) -> Model:
    """Create model.
    :param engine_type: Engine type. to create model for.
    :return Any: Model instance.
    """
    openrouter_api_base = "https://openrouter.ai/api/v1/"
    openrouter_model_id = "google/gemini-2.5-flash-lite-preview-09-2025"

    match engine_type:
        case EngineType.dspy:
            model = dspy.LM(
                f"openrouter/{openrouter_model_id}",
                api_base=openrouter_api_base,
                api_key=os.environ['OPENROUTER_API_KEY']
            )

        case EngineType.glix:
            model = gliner.GLiNER.from_pretrained("knowledgator/gliner-multitask-v1.0")

        case EngineType.langchain:
            model = ChatOpenAI(
                api_key=os.environ['OPENROUTER_API_KEY'],
                base_url=openrouter_api_base,
                model=openrouter_model_id,
                temperature=0
            )

        case EngineType.huggingface:
            model = transformers.pipeline(
                "zero-shot-classification", model="MoritzLaurer/xtremedistil-l6-h256-zeroshot-v1.1-all-33"
            )

        case EngineType.outlines:
            model_name = "HuggingFaceTB/SmolLM-135M-Instruct"
            model = outlines.models.from_transformers(
                transformers.AutoModelForCausalLM.from_pretrained(model_name),
                transformers.AutoTokenizer.from_pretrained(model_name),
            )

        case _:
            raise ValueError(f"Unsupported runtime type {engine_type}.")

    return model


@cache
def _make_runtime(engine_type: EngineType, batch_size: int) -> Runtime:
    """Create runtime tuple (model, generation_settings) for tests.

    :param engine_type: Engine type.
    :param batch_size: Batch size to use in runtime.
    :return: Runtime tuple.
    """
    return Runtime(make_model(engine_type), GenerationSettings(), batch_size)


@pytest.fixture(scope="function")
def batch_runtime(request) -> Runtime:
    """Initialize runtime with batching enabled (batch_size = -1)."""
    assert isinstance(request.param, EngineType)
    return _make_runtime(engine_type=request.param, batch_size=-1)


@pytest.fixture(scope="function")
def runtime(request) -> Runtime:
    """Initialize runtime without batching (batch_size = 1)."""
    assert isinstance(request.param, EngineType)
    return _make_runtime(engine_type=request.param, batch_size=1)


@pytest.fixture(scope="session")
def dummy_docs() -> list[Doc]:
    return [Doc(text="This is about politics stuff. " * 10), Doc(text="This is about science stuff. " * 10)]


@pytest.fixture(scope="session")
def classification_docs() -> list[Doc]:
    return [
        Doc(
            text="A new law has been passed. The opposition doesn't support it, but parliament has voted on it. This "
            "is about politics - parliament, laws, parties, politicians."
        ),
        Doc(
            text="Scientists report that plasma is a state of matter. They published an academic paper. This is about "
            "science - scientists, papers, experiments, laws of nature."
        ),
    ]


@pytest.fixture(scope="session")
def translation_docs() -> list[Doc]:
    return [Doc(text="It is rainy today."), Doc(text="It is cloudy today.")]


@pytest.fixture(scope="session")
def sentiment_analysis_docs() -> list[Doc]:
    return [
        Doc(
            text="Beautiful dishes, haven't eaten so well in a long time. Overall pretty good, if you can ignore the "
            "annoying waiters."
        ),
        Doc(text="Horrible place. Service is unfriendly, food overpriced and bland. Do not go."),
    ]


@pytest.fixture(scope="session")
def qa_docs() -> list[Doc]:
    return [
        Doc(
            text="""
            History is the systematic study of the past. As an academic discipline, it analyzes and interprets evidence
            to construct narratives about what happened and explain why it happened, focusing primarily on the human
            past. Some theorists categorize history as a social science, while others see it as part of the humanities
            or consider it a hybrid discipline. Similar debates surround the purpose of history, for example, whether
            its main aim is theoretical, to uncover the truth, or practical, to learn lessons from the past. In a
            slightly different sense, the term history refers not to an academic field but to the past itself or to
            individual texts about the past.
            """
        ),
        Doc(
            text="""
            Sociology is the scientific study of human society that focuses on society, human social behavior, patterns
            of social relationships, social interaction, and aspects of culture associated with everyday life. Regarded
            as a part of both the social sciences and humanities, sociology uses various methods of empirical
            investigation and critical analysis to develop a body of knowledge about social order and social change.
            Sociological subject matter ranges from micro-level analyses of individual interaction and agency to
            macro-level analyses of social systems and social structure. Applied sociological research may be applied
            directly to social policy and welfare, whereas theoretical approaches may focus on the understanding of
            social processes and phenomenological method.
            """
        ),
    ]


@pytest.fixture(scope="session")
def summarization_docs() -> list[Doc]:
    return [
        Doc(
            text="""
            The decay spreads over the State, and the sweet smell is a great sorrow on the land. Men who can graft the
            trees and make the seed fertile and big can find no way to let the hungry people eat their produce. Men
            who have created new fruits in the world cannot create a system whereby their fruits may be eaten. And the
            failure hangs over the State like a great sorrow. The works of the roots of the vines, of the trees, must
            be destroyed to keep up the price, and this is the saddest, bitterest thing of all. Carloads of oranges
            dumped on the ground. The people came for miles to take the fruit, but this could not be. How would they
            buy oranges at twenty cents a dozen if they could drive out and pick them up? And men with hoses squirt
            kerosene on the oranges, and they are angry at the crime, angry at the people who have come to take the
            fruit. A million people hungry, needing the fruit—and kerosene sprayed over the golden mountains. And the
            smell of rot fills the country.
            """
        ),
        Doc(
            text="""
            After all, the practical reason why, when the power is once in the hands of the people, a majority are
            permitted, and for a long period continue, to rule is not because they are most likely to be in the right,
            nor because this seems fairest to the minority, but because they are physically the strongest. But a
            government in which the majority rule in all cases cannot be based on justice, even as far as men
            understand it. Can there not be a government in which majorities do not virtually decide right and wrong,
            but conscience?- in which majorities decide only those questions to which the rule of expediency is
            applicable? Must the citizen ever for a moment, or in the least degree, resign his conscience to the
            legislation? Why has every man a conscience, then? I think that we should be men first, and subjects
            afterward. It is not desirable to cultivate a respect for the law, so much as for the right. The only
            obligation which I have a right to assume is to do at any time what I think right. It is truly enough
            said that a corporation has no conscience; but a corporation of conscientious men is a corporation with
            a conscience.
            """
        ),
    ]


@pytest.fixture(scope="session")
def information_extraction_docs() -> list[Doc]:
    return [
        Doc(text="Mahatma Ghandi lived to 79 years old. Bugs Bunny is at least 85 years old."),
        Doc(text="Marie Curie passed away at the age of 67 years. Marie Curie was 67 years old."),
    ]


@pytest.fixture(scope="session")
def pii_masking_docs() -> list[Doc]:
    return [
        Doc(text="Her SSN is 222-333-444. Her credit card number is 1234 5678."),
        Doc(text="You can reach Michael at michael.michaels@gmail.com."),
    ]


@pytest.fixture(scope="session")
def ner_docs() -> list[Doc]:
    return [
        Doc(text="John studied data science in Barcelona and lives with Jaume"),
        Doc(text="Maria studied computer engineering in Madrid and works with Carlos"),
    ]
