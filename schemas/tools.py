from typing import Annotated

from pydantic import Field

from schemas.base import ContractModel
from schemas.common import ClueSource


class RecommendClue(ContractModel):
    text: str
    source: ClueSource


class RecommendPick(ContractModel):
    work_id: int = Field(description="후보 목록에 있는 작품 ID 만")
    reason: Annotated[str, Field(max_length=200)]
    matched_clues: list[RecommendClue] = Field(default_factory=list, max_length=3)


class RecommendWorksInput(ContractModel):
    """Sonnet 의 recommend_works 도구 입력. 배열 순서 = 추천 순위."""

    works: list[RecommendPick] = Field(max_length=5)
