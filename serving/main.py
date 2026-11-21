from functools import lru_cache

import anthropic
from fastapi import Depends, FastAPI
from fastapi.responses import StreamingResponse

from schemas.search import SearchStreamRequest
from serving.answer.claude_answer import ClaudeAnswerer
from serving.config import Settings, get_settings
from serving.pipeline.candidates import CandidateFinder, NotReadyCandidateFinder
from serving.pipeline.search import Answerer, run_search
from serving.security import require_internal_token
from serving.sse import sse_stream


@lru_cache
def get_anthropic_client() -> anthropic.AsyncAnthropic:
    # 스트림 전체 시간은 파이프라인의 answer_timeout_seconds 가 자른다. 여기서는 연결 · 조각 사이만
    return anthropic.AsyncAnthropic(timeout=anthropic.Timeout(60.0, connect=5.0), max_retries=1)


def get_candidate_finder() -> CandidateFinder:
    # 검색(AI-07)이 붙으면 바꾼다
    return NotReadyCandidateFinder()


def get_answerer(settings: Settings = Depends(get_settings)) -> Answerer:
    return ClaudeAnswerer(get_anthropic_client(), settings)


def create_app() -> FastAPI:
    app = FastAPI(title="STORIX-AI", docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "UP", "pipelineVersion": get_settings().pipeline_version}

    @app.get("/internal/ping", dependencies=[Depends(require_internal_token)])
    def internal_ping() -> dict[str, str]:
        return {"status": "OK"}

    @app.post("/internal/search/stream", dependencies=[Depends(require_internal_token)])
    async def search_stream(
        request: SearchStreamRequest,
        settings: Settings = Depends(get_settings),
        finder: CandidateFinder = Depends(get_candidate_finder),
        answerer: Answerer = Depends(get_answerer),
    ) -> StreamingResponse:
        events = run_search(request, finder, answerer, settings)
        return StreamingResponse(
            sse_stream(events, settings.heartbeat_seconds),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return app


app = create_app()
