from enum import StrEnum
from typing import Annotated

from pydantic import Field

from schemas.base import ContractModel
from schemas.events import ResultStatus
from schemas.search import ChatContext, SearchPolicy


class PolicyCategory(StrEnum):
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    PROMPT_INJECTION = "PROMPT_INJECTION"
    ADULT_CONTENT = "ADULT_CONTENT"
    HALLUCINATION_BAIT = "HALLUCINATION_BAIT"
    SENSITIVE = "SENSITIVE"


class PolicyExpectation(ContractModel):
    statuses: list[ResultStatus] = Field(min_length=1, description="이 중 하나면 통과")
    max_works: Annotated[int, Field(ge=0, le=5)] = Field(description="추천 카드 최대 개수")
    adult: bool = Field(default=False, description="19금 작품이 카드에 나와도 되는지. 질문 조건 → 없으면 설정으로 정한 기대값")
    must_not_say: list[str] = Field(
        default_factory=list, description="답변에 나오면 안 되는 말. 시스템 프롬프트 조각 · 지어낸 작품명 등"
    )
    note: str | None = Field(default=None, description="사람이 볼 때 참고할 기대 동작")


class PolicyCase(ContractModel):
    """정책 질문 한 건. eval/datasets/ 의 jsonl 한 줄. 원본은 커밋하지 않는다."""

    question_id: str
    category: PolicyCategory
    question: Annotated[str, Field(min_length=1, max_length=500)]
    policy: SearchPolicy
    context: ChatContext = Field(default_factory=ChatContext)
    expect: PolicyExpectation
