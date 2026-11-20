from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field

from schemas.base import ContractModel
from schemas.common import ClueSource


class ProgressStep(StrEnum):
    UNDERSTANDING = "UNDERSTANDING"
    SEARCHING = "SEARCHING"
    FOUND = "FOUND"
    ANSWERING = "ANSWERING"


class ResultStatus(StrEnum):
    OK = "OK"
    NO_RESULT = "NO_RESULT"
    WORK_NOT_FOUND = "WORK_NOT_FOUND"
    OFF_TOPIC = "OFF_TOPIC"


class ErrorCode(StrEnum):
    TIMEOUT = "TIMEOUT"
    LLM_UNAVAILABLE = "LLM_UNAVAILABLE"
    SEARCH_UNAVAILABLE = "SEARCH_UNAVAILABLE"
    INVALID_REQUEST = "INVALID_REQUEST"
    INTERNAL = "INTERNAL"


class MatchedClue(ContractModel):
    text: str
    source: ClueSource


class RecommendedWork(ContractModel):
    """AI 서버는 ID · 이유 · 단서만 보낸다. 제목 · 표지 · 플랫폼은 Spring 이 DB 값으로 채운다."""

    rank: Annotated[int, Field(ge=1, le=5)]
    work_id: int
    reason: str
    matched_clues: list[MatchedClue] = Field(default_factory=list)


class Usage(ContractModel):
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int = 0


class ProgressEvent(ContractModel):
    event: Literal["progress"] = "progress"
    step: ProgressStep
    message: str


class TokenEvent(ContractModel):
    event: Literal["token"] = "token"
    text: str


class WorksEvent(ContractModel):
    event: Literal["works"] = "works"
    recommended_works: list[RecommendedWork] = Field(max_length=5)
    candidate_work_ids: list[int] = Field(
        description="검색 후보. Spring 이 추천 작품이 후보 안에 있는지 확인할 때 쓴다"
    )
    pipeline_version: str


class DoneEvent(ContractModel):
    event: Literal["done"] = "done"
    status: ResultStatus
    usage: list[Usage] = Field(default_factory=list, description="모델 호출마다 하나")
    elapsed_ms: int


class ErrorEvent(ContractModel):
    event: Literal["error"] = "error"
    code: ErrorCode
    message: str


SearchEvent = Annotated[
    ProgressEvent | TokenEvent | WorksEvent | DoneEvent | ErrorEvent,
    Field(discriminator="event"),
]
