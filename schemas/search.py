from typing import Annotated

from pydantic import Field

from schemas.base import ContractModel
from schemas.common import WorkType


class SearchPolicy(ContractModel):
    """Spring 이 매 질문마다 확인해서 넘기는 정책값. AI 서버는 바꾸지 않는다."""

    adult_allowed: bool = Field(description="설정 켜짐 + 지금 성인 인증 유효일 때만 true")
    work_types: list[WorkType] = Field(
        default_factory=list, description="챗봇 설정의 작품 유형. 비어 있으면 상관없음"
    )
    excluded_work_ids: list[int] = Field(
        default_factory=list, description="서재에 있는 작품. 추천에서 뺀다"
    )


class ChatTurn(ContractModel):
    role: Annotated[str, Field(pattern="^(user|assistant)$")]
    text: str
    work_ids: list[int] = Field(default_factory=list, description="이 턴에 보여 준 작품")


class ChatContext(ContractModel):
    """대화방 단위 맥락. 최근 25턴까지."""

    turns: list[ChatTurn] = Field(default_factory=list, max_length=25)
    shown_work_ids: list[int] = Field(
        default_factory=list, description="이 대화방에서 이미 보여 준 작품"
    )
    conditions: list[str] = Field(
        default_factory=list, description='사용자가 붙인 조건. 예: "완결작만"'
    )


class SearchStreamRequest(ContractModel):
    """POST /internal/search/stream 요청. 응답은 SSE."""

    chat_id: int
    message_id: int
    user_id: int
    question: Annotated[str, Field(min_length=1, max_length=500)]
    policy: SearchPolicy
    context: ChatContext = Field(default_factory=ChatContext)
