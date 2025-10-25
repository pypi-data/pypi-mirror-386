import logging
from typing import List, Optional

from opentelemetry.sdk.trace import ReadableSpan
from pydantic import BaseModel, ConfigDict, model_serializer
from pydantic.alias_generators import to_camel

from uipath._cli._runtime._contracts import UiPathRuntimeResult
from uipath.eval.models.models import EvaluationResult, ScoreType


class UiPathEvalRunExecutionOutput(BaseModel):
    """Result of a single agent response."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    execution_time: float
    spans: list[ReadableSpan]
    logs: list[logging.LogRecord]
    result: UiPathRuntimeResult


class EvaluationResultDto(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    score: float
    details: Optional[str] = None
    evaluation_time: Optional[float] = None

    @model_serializer(mode="wrap")
    def serialize_model(self, serializer, info):
        data = serializer(self)
        if self.details is None and isinstance(data, dict):
            data.pop("details", None)
        return data

    @classmethod
    def from_evaluation_result(
        cls, evaluation_result: EvaluationResult
    ) -> "EvaluationResultDto":
        score_type = evaluation_result.score_type
        score: float
        if score_type == ScoreType.BOOLEAN:
            score = 100 if evaluation_result.score else 0
        elif score_type == ScoreType.ERROR:
            score = 0
        else:
            score = evaluation_result.score

        return cls(
            score=score,
            details=evaluation_result.details,
            evaluation_time=evaluation_result.evaluation_time,
        )


class EvaluationRunResultDto(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    evaluator_name: str
    evaluator_id: str
    result: EvaluationResultDto

    @model_serializer(mode="wrap")
    def serialize_model(self, serializer, info):
        data = serializer(self)
        if isinstance(data, dict):
            data.pop("evaluatorId", None)
        return data


class EvaluationRunResult(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    evaluation_name: str
    evaluation_run_results: List[EvaluationRunResultDto]

    @property
    def score(self) -> float:
        """Compute average score for this single eval_item."""
        if not self.evaluation_run_results:
            return 0.0

        total_score = sum(dto.result.score for dto in self.evaluation_run_results)
        return total_score / len(self.evaluation_run_results)


class UiPathEvalOutput(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    evaluation_set_name: str
    evaluation_set_results: List[EvaluationRunResult]

    @property
    def score(self) -> float:
        """Compute overall average score from evaluation results."""
        if not self.evaluation_set_results:
            return 0.0

        eval_item_scores = [
            eval_result.score for eval_result in self.evaluation_set_results
        ]
        return sum(eval_item_scores) / len(eval_item_scores)
