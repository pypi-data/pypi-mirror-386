"""Type definitions for rubrics and evaluation components."""

from enum import Enum
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict


class Criterion(BaseModel):
    """A single evaluation criterion with a weight and requirement description."""

    model_config = ConfigDict(frozen=True)

    weight: float
    requirement: str


class CriterionReport(Criterion):
    """A criterion with its evaluation verdict (MET/UNMET) and reasoning."""

    verdict: Literal["MET", "UNMET"]
    reason: str


class EvaluationReport(BaseModel):
    """Final evaluation result with score (0-100) and optional per-criterion reports."""

    score: float
    report: list[CriterionReport] | None = None


class ModelProvider(Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"


class ModelConfig(BaseModel):
    """Configuration for which LLM model to use for grading."""

    model: str
    provider: ModelProvider = ModelProvider.OPENROUTER

    def get_open_router_model_str(self) -> str:
        if self.provider == ModelProvider.OPENROUTER:
            return self.model
        return f"{self.provider.value}/{self.model}"


class AutograderFn(Protocol):
    """Protocol defining the signature for autograder functions."""

    async def __call__(
        self,
        to_grade: str,
        rubric: list[Criterion],
        model: ModelConfig,
        **kwargs: Any,
    ) -> EvaluationReport: ...
