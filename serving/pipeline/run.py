"""질문 하나를 SSE 이벤트 흐름으로. ① extract → ②③ search → ⑦ answer 순서로 state 를 넘긴다.

progress → token(여러 번) → works → done, 실패하면 error 로 끝난다."""

import asyncio
import logging
import time
from collections.abc import AsyncIterator

import anthropic

from schemas.events import (
    DoneEvent,
    ErrorCode,
    ErrorEvent,
    ProgressEvent,
    ProgressStep,
    ResultStatus,
    SearchEvent,
    TokenEvent,
    WorksEvent,
)
from schemas.search import SearchStreamRequest
from serving.config import Settings
from serving.pipeline.answer import AnswerDone, Answerer, TextDelta, to_recommended
from serving.pipeline.extract import extract
from serving.pipeline.search import CandidateFinder, SearchUnavailable, search
from serving.pipeline.state import SearchState

log = logging.getLogger(__name__)

NO_CANDIDATE_TEXT = "딱 맞는 작품을 못 찾았어요. 장르나 분위기, 기억나는 장면을 조금 더 알려 주시겠어요?"


async def run_search(request: SearchStreamRequest, finder: CandidateFinder, answerer: Answerer,
                     settings: Settings) -> AsyncIterator[SearchEvent]:
    started = time.monotonic()

    def elapsed_ms() -> int:
        return int((time.monotonic() - started) * 1000)

    state = SearchState(request=request)
    yield ProgressEvent(step=ProgressStep.SEARCHING, message="작품 찾는 중…")
    state = await extract(state)
    try:
        state = await search(state, finder)
    except SearchUnavailable:
        yield ErrorEvent(code=ErrorCode.SEARCH_UNAVAILABLE, message="검색을 할 수 없어요")
        return

    candidates = state.candidates
    if not candidates:
        yield TokenEvent(text=NO_CANDIDATE_TEXT)
        yield WorksEvent(recommended_works=[], candidate_work_ids=[], pipeline_version=settings.pipeline_version)
        yield DoneEvent(status=ResultStatus.NO_RESULT, elapsed_ms=elapsed_ms())
        return

    yield ProgressEvent(step=ProgressStep.FOUND, message=f"후보 {len(candidates)}개 찾음")
    done: AnswerDone | None = None
    try:
        async with asyncio.timeout(settings.answer_timeout_seconds):
            async for item in answerer.stream(request.question, candidates, request.context, request.policy):
                if isinstance(item, TextDelta):
                    yield TokenEvent(text=item.text)
                else:
                    done = item
    except (TimeoutError, anthropic.APITimeoutError):
        yield ErrorEvent(code=ErrorCode.TIMEOUT, message="답변이 늦어져 멈췄어요")
        return
    except (anthropic.RateLimitError, anthropic.InternalServerError, anthropic.APIConnectionError):
        log.warning("Claude 호출 실패 messageId=%s", request.message_id, exc_info=True)
        yield ErrorEvent(code=ErrorCode.LLM_UNAVAILABLE, message="답변 모델에 연결하지 못했어요")
        return
    except anthropic.APIStatusError:
        log.error("Claude 요청 거절 messageId=%s", request.message_id, exc_info=True)
        yield ErrorEvent(code=ErrorCode.INTERNAL, message="답변을 만들지 못했어요")
        return
    except ValueError:
        # 스트리밍 중 SDK 가 도구 입력 JSON 을 아예 읽지 못했을 때
        log.error("recommend_works 입력을 읽지 못함 messageId=%s", request.message_id, exc_info=True)
        yield ErrorEvent(code=ErrorCode.INTERNAL, message="답변을 만들지 못했어요")
        return

    if done is None:
        yield ErrorEvent(code=ErrorCode.INTERNAL, message="답변을 만들지 못했어요")
        return

    works = [] if done.refused else to_recommended(done.picks, candidates)
    yield WorksEvent(recommended_works=works, candidate_work_ids=[c.work_id for c in candidates],
                     pipeline_version=settings.pipeline_version)
    if done.refused:
        status = ResultStatus.OFF_TOPIC
    elif works:
        status = ResultStatus.OK
    else:
        status = ResultStatus.NO_RESULT
    yield DoneEvent(status=status, usage=done.usage, elapsed_ms=elapsed_ms())
