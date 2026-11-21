"""답변(⑦): Sonnet 스트리밍. 글자 조각은 바로 넘기고, recommend_works 입력은 끝까지 모아 검증한다."""

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

import anthropic
from pydantic import ValidationError

from schemas.events import Usage
from schemas.search import ChatContext, SearchPolicy
from schemas.tools import RecommendPick, RecommendWorksInput
from serving.answer.prompt import RECOMMEND_TOOL_NAME, SYSTEM_PROMPT, recommend_tool, user_turn
from serving.config import Settings
from serving.pipeline.candidates import Candidate

log = logging.getLogger(__name__)

# 거절되면 같은 요청을 대체 모델이 이어서 처리한다 (거절 분류에 따라 서버가 고름)
FALLBACK_BETA = "server-side-fallback-2026-07-01"


@dataclass(frozen=True)
class TextDelta:
    text: str


@dataclass(frozen=True)
class AnswerDone:
    picks: list[RecommendPick]
    refused: bool
    usage: list[Usage] = field(default_factory=list)


def history_messages(context: ChatContext) -> list[dict]:
    """최근 대화를 user · assistant 가 번갈아 오는 메시지로. 첫 메시지는 user 여야 한다."""
    messages: list[dict] = []
    for turn in context.turns:
        if not turn.text.strip():
            continue
        if messages and messages[-1]["role"] == turn.role:
            messages[-1]["content"] += "\n" + turn.text
        else:
            messages.append({"role": turn.role, "content": turn.text})
    while messages and messages[0]["role"] != "user":
        messages.pop(0)
    # 마지막 질문이 user 로 붙으니 기록은 assistant 로 끝나야 한다
    if messages and messages[-1]["role"] == "user":
        messages.pop()
    return messages


def parse_picks(final: anthropic.types.beta.BetaMessage) -> list[RecommendPick]:
    """잘리거나(max_tokens) 거절된 답의 도구 입력은 쓰지 않는다. 검증에 실패해도 버린다."""
    if final.stop_reason in ("max_tokens", "refusal"):
        return []
    for block in final.content:
        if block.type == "tool_use" and block.name == RECOMMEND_TOOL_NAME:
            try:
                return list(RecommendWorksInput.model_validate(block.input).works)
            except ValidationError:
                log.warning("recommend_works 입력 검증 실패 messageId 없음, 추천 없이 진행")
                return []
    return []


def usage_of(final: anthropic.types.beta.BetaMessage) -> list[Usage]:
    u = final.usage
    return [Usage(model=final.model, input_tokens=u.input_tokens, output_tokens=u.output_tokens,
                  cache_read_tokens=u.cache_read_input_tokens or 0)]


class ClaudeAnswerer:
    def __init__(self, client: anthropic.AsyncAnthropic, settings: Settings):
        self._client = client
        self._settings = settings

    async def stream(self, question: str, candidates: list[Candidate], context: ChatContext,
                     policy: SearchPolicy) -> AsyncIterator[TextDelta | AnswerDone]:
        messages = history_messages(context) + [
            {"role": "user", "content": user_turn(question, candidates, context, policy)}
        ]
        async with self._client.beta.messages.stream(
            model=self._settings.answer_model,
            max_tokens=self._settings.answer_max_tokens,
            # 도구 정의 + 시스템 프롬프트까지 캐시. 후보 · 질문은 그 뒤라 캐시를 깨지 않는다
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            tools=[recommend_tool()],
            # Sonnet 5.5 는 도구 강제 지정이 안 돼서 auto + 프롬프트 지시. 안 부르면 추천 없음으로 본다
            tool_choice={"type": "auto"},
            output_config={"effort": self._settings.answer_effort},
            betas=[FALLBACK_BETA],
            fallbacks="default",
            messages=messages,
        ) as stream:
            async for event in stream:
                if event.type == "text" and event.text:
                    yield TextDelta(event.text)
            final = await stream.get_final_message()

        yield AnswerDone(picks=parse_picks(final), refused=final.stop_reason == "refusal", usage=usage_of(final))
