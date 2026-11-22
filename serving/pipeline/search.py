"""②③ 필터 · 검색. AI-07 에서 ES 하이브리드 검색으로 state.candidates 를 채운다."""

from typing import Protocol

from schemas.search import SearchStreamRequest
from serving.pipeline.state import Candidate, SearchState


class SearchUnavailable(Exception):
    """검색을 할 수 없을 때. SSE error(SEARCH_UNAVAILABLE) 로 끝난다."""


class CandidateFinder(Protocol):
    async def find(self, request: SearchStreamRequest) -> list[Candidate]: ...


class NotReadyCandidateFinder:
    """검색(AI-07)이 붙기 전 자리. 항상 SearchUnavailable."""

    async def find(self, request: SearchStreamRequest) -> list[Candidate]:
        raise SearchUnavailable("검색이 아직 연결되지 않았다")


async def search(state: SearchState, finder: CandidateFinder) -> SearchState:
    state.candidates = await finder.find(state.request)
    return state
