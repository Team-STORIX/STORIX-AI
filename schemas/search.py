from typing import Annotated

from pydantic import Field

from schemas.base import ContractModel
from schemas.common import WorkType


class SearchPolicy(ContractModel):
    """Spring 이 매 질문마다 확인해서 넘기는 정책값. AI 서버는 바꾸지 않는다."""

    adult_default: bool = Field(
        description="챗봇 설정의 19금 추천. 질문 · 대화에 19금 조건이 없을 때만 쓴다. 성인 인증이 풀리면 false"
    )
    adult_verified: bool = Field(
        description="지금 성인 인증 유효. false 면 Spring 이 19금 카드 표지를 가린다. AI 는 표지를 말로 풀지 않는다"
    )
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
        default_factory=list, description='사용자가 붙인 조건. 예: "웹툰만", "19금 빼고"'
    )


class SearchStreamRequest(ContractModel):
    """POST /internal/search/stream 요청. 응답은 SSE."""

    chat_id: int
    message_id: int
    user_id: int
    question: Annotated[str, Field(min_length=1, max_length=500)]
    policy: SearchPolicy
    context: ChatContext = Field(default_factory=ChatContext)
