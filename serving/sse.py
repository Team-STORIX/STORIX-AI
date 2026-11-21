"""SearchEvent 를 SSE 프레임으로. 조용한 동안에는 heartbeat 주석 줄을 보내 연결을 살려 둔다."""

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator

from schemas.events import ErrorCode, ErrorEvent, SearchEvent

log = logging.getLogger(__name__)

HEARTBEAT = ": ping\n\n"


def format_event(event: SearchEvent) -> str:
    return f"event: {event.event}\ndata: {event.model_dump_json(by_alias=True)}\n\n"


async def sse_stream(events: AsyncIterator[SearchEvent], heartbeat_seconds: float) -> AsyncIterator[str]:
    iterator = aiter(events)
    pending: asyncio.Task | None = None
    try:
        while True:
            if pending is None:
                pending = asyncio.ensure_future(anext(iterator))
            done, _ = await asyncio.wait({pending}, timeout=heartbeat_seconds)
            if not done:
                yield HEARTBEAT
                continue
            task, pending = pending, None
            try:
                event = task.result()
            except StopAsyncIteration:
                return
            except Exception:
                log.exception("답변 스트림 중 예외")
                yield format_event(ErrorEvent(code=ErrorCode.INTERNAL, message="답변을 만들지 못했어요"))
                return
            yield format_event(event)
    finally:
        # Spring 이 연결을 끊으면 진행 중인 단계를 멈춘다
        if pending is not None:
            pending.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await pending
        aclose = getattr(iterator, "aclose", None)
        if aclose is not None:
            await aclose()
