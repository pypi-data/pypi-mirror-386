import math
from enum import Enum, StrEnum
from typing import Any, List, Mapping, Optional, Tuple

from pydantic import BaseModel, computed_field
from pydantic.fields import Field

from wxo_agentic_evaluation.metrics.llm_as_judge import (
    AnswerRelevancy,
    Faithfulness,
)
from wxo_agentic_evaluation.type import ConversationalConfidenceThresholdScore


def average(array):
    if len(array) == 0:
        return math.nan

    else:
        return sum(array) / len(array)


class DescriptionQuality(StrEnum):
    GOOD = "GOOD"
    BAD = "BAD"
    MISSING = "MISSING"


class DescriptionQualityMetric(BaseModel):
    tool_name: str = None
    description_score: float | None = None
    threshold: float | None = None

    @computed_field
    @property
    def is_bad_description(self) -> Optional[bool]:
        if self.description_score and self.threshold:
            return self.description_score >= self.threshold

        return None

    @computed_field
    @property
    def description_quality(self) -> str:
        if self.description_score is None:
            return DescriptionQuality.MISSING
        elif self.is_bad_description:
            return DescriptionQuality.BAD
        else:
            return DescriptionQuality.GOOD


class KnowledgeBaseMetrics(BaseModel):
    dataset_name: str = None
    knowledge_base_name: str = (
        None  # in the message response body it is represented as "tool_name"
    )
    tool_call_id: str = None
    faithfulness: Faithfulness = None
    answer_relevancy: AnswerRelevancy = None
    confidence_scores: ConversationalConfidenceThresholdScore = None


class KnowledgeBaseMetricSummary(BaseModel):
    knowledge_base_metrics: List[List[KnowledgeBaseMetrics]]

    @computed_field(alias="detailed")
    @property
    def groupby_dataset(self) -> Mapping[str, Any]:
        groupby = {}
        for metric in self.knowledge_base_metrics:
            for row in metric:
                name = row.dataset_name
                tool_call_id = row.tool_call_id
                knowledge_base_name = row.knowledge_base_name
                faithfulness = row.faithfulness
                confidence_scores = row.confidence_scores
                answer_relevancy = row.answer_relevancy

                if name not in groupby:
                    groupby[name] = {
                        "knowledge_base_name": [knowledge_base_name],
                        "faithfulness": [faithfulness],
                        "confidence_scores": [confidence_scores],
                        "tool_call_id": [tool_call_id],
                        "answer_relevancy": [answer_relevancy],
                        "number_of_calls": 1,
                    }
                else:
                    values = groupby[name]
                    values.get("knowledge_base_name").append(
                        knowledge_base_name
                    )
                    values.get("faithfulness").append(faithfulness)
                    values.get("answer_relevancy").append(answer_relevancy)
                    values.get("confidence_scores").append(confidence_scores)
                    values.get("tool_call_id").append(tool_call_id)
                    values["number_of_calls"] += 1
                    groupby[name] = values

        return groupby

    @computed_field(alias="summary")
    @property
    def average(self) -> Mapping[str, Any]:
        summary = {}
        for dataset, metric in self.groupby_dataset.items():
            average_metric = {}
            average_metric["average_faithfulness"] = average(
                [
                    float(faithfulness.faithfulness_score)
                    for faithfulness in metric["faithfulness"]
                ]
            )
            average_metric["average_response_confidence"] = average(
                [
                    float(confidence_score.response_confidence)
                    for confidence_score in metric["confidence_scores"]
                ]
            )
            average_metric["average_retrieval_confidence"] = average(
                [
                    float(confidence_score.retrieval_confidence)
                    for confidence_score in metric["confidence_scores"]
                ]
            )
            average_metric["average_answer_relevancy"] = average(
                [
                    float(answer_relevancy.answer_relevancy_score)
                    for answer_relevancy in metric["answer_relevancy"]
                ]
            )
            average_metric["number_of_calls"] = metric["number_of_calls"]
            average_metric["knowledge_bases_called"] = ", ".join(
                set(metric["knowledge_base_name"])
            )
            summary[dataset] = average_metric

        return summary


class KeywordSemanticSearchMetric(BaseModel):
    keyword_match: bool
    semantic_match: bool
    message: str
    goal_detail: str


class TextMatchType(Enum):
    text_match = "Summary Matched"
    text_mismatch = "Summary MisMatched"
    na = "NA"


class ToolCallAndRoutingMetrics(BaseModel):
    dataset_name: str = ""
    total_steps: int = 0
    llm_step: int = 0
    total_tool_calls: int = 0
    expected_tool_calls: int = 0
    correct_tool_calls: int = 0
    relevant_tool_calls: int = (
        0  # calls with the same function but different args
    )
    total_routing_calls: int = 0
    relevant_routing_calls: int = 0
    tool_calls_with_incorrect_parameter: int = 0
    text_match: TextMatchType = TextMatchType.na
    is_success: bool = False
    avg_resp_time: float = -1

    @computed_field
    @property
    def tool_call_recall(self) -> float:
        return round(
            (
                self.correct_tool_calls / self.expected_tool_calls
                if self.expected_tool_calls > 0
                else 0.0
            ),
            2,
        )

    @computed_field
    @property
    def tool_call_precision(self) -> float:
        return round(
            (
                (self.correct_tool_calls) / self.total_tool_calls
                if self.total_tool_calls > 0
                else 0.0
            ),
            2,
        )

    @computed_field
    @property
    def agent_routing_accuracy(self) -> float:
        return round(
            (
                self.relevant_routing_calls / self.total_routing_calls
                if self.total_routing_calls > 0
                else 0.0
            ),
            2,
        )


class Annotation(BaseModel):
    recommendation: str
    details: str
    quote: str
    parameter_name: Optional[str]


class FailedStaticTestCases(BaseModel):
    metric_name: str
    description: str
    explanation: str


class FailedSemanticTestCases(BaseModel):
    metric_name: str
    evidence: str
    explanation: str
    output: int
    confidence: float
    annotations: Optional[List[Annotation]] = None


class EnhancedAnalyzeMetrics(BaseModel):
    test_case_name: str
    tool_names: List[str]
    parameter_annotations: List[List[FailedSemanticTestCases]] = [[]]
    tool_annotations: List[List[FailedSemanticTestCases]] = [[]]
    static_metrics: List[List[FailedStaticTestCases]] = [[]]


class ReferenceLessEvalMetrics(BaseModel):
    dataset_name: str
    number_of_tool_calls: int
    number_of_successful_tool_calls: int
    number_of_static_failed_tool_calls: int
    number_of_semantic_failed_tool_calls: int
    failed_static_tool_calls: Optional[
        List[Tuple[int, List[FailedStaticTestCases]]]
    ]
    failed_semantic_tool_calls: Optional[
        List[Tuple[int, List[FailedSemanticTestCases]]]
    ]


class Metric(BaseModel):
    """Generic metric result."""

    eval_name: str = Field(description="name of eval that produce metric")
    value: int | float | bool | str = Field(description="metric value")
    metadata: Optional[dict] = Field(
        default=None,
        description="metadata that was generated along side the metric. example: llmaaj reason, retrieval score",
    )


class CustomEvalMetrics(BaseModel):
    dataset_name: str
    custom_metrics: list[Metric]
