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


def include_adult(state: SearchState) -> bool:
    """19금 작품을 후보에 넣을지. 질문 · 대화에서 말한 조건이 먼저고, 없으면 챗봇 설정."""
    stated = state.conditions.get("adult")
    if stated is not None:
        return bool(stated)
    return state.request.policy.adult_default


async def search(state: SearchState, finder: CandidateFinder) -> SearchState:
    state.candidates = await finder.find(state.request)
    return state
