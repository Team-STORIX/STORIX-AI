from datetime import datetime

from pydantic import Field

from schemas.base import ContractModel


class EvalMetrics(ContractModel):
    recall_at_10: float = Field(ge=0, le=1)
    mrr: float = Field(ge=0, le=1)
    precision_at_5: float = Field(ge=0, le=1)
    out_of_candidate_rate: float = Field(ge=0, le=1, description="후보 밖 작품을 말한 비율")
    adult_exposure_rate: float = Field(ge=0, le=1, description="성인 작품이 나오면 안 되는 질문에서 나온 비율")


class EvalCase(ContractModel):
    question_id: str
    tags: list[str] = Field(default_factory=list)
    expected_work_ids: list[int]
    candidate_work_ids: list[int]
    recommended_work_ids: list[int]
    passed: bool
    failure_reason: str | None = Field(
        default=None, description="검색 누락 · 지어냄 · 정책 위반 · 말투 등"
    )


class EvalReport(ContractModel):
    """채점 결과. PR 평가 · Hub 평가 게이트 · 출시 기준 측정이 같은 형식을 쓴다. 이채연과 같이 확정 전 초안."""

    pipeline_version: str
    dataset_version: str
    created_at: datetime
    metrics: EvalMetrics
    cases: list[EvalCase] = Field(default_factory=list)
