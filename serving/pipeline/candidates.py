from dataclasses import dataclass, field
from typing import Protocol

from schemas.search import SearchStreamRequest


@dataclass(frozen=True)
class Candidate:
    """검색(②③)이 찾은 작품 후보. 답변 프롬프트에 넣는 값만 담는다."""

    work_id: int
    title: str
    works_type: str
    genre: str | None = None
    description: str = ""
    tags: tuple[str, ...] = field(default_factory=tuple)


class SearchUnavailable(Exception):
    """검색을 할 수 없을 때. SSE error(SEARCH_UNAVAILABLE) 로 끝난다."""


class CandidateFinder(Protocol):
    async def find(self, request: SearchStreamRequest) -> list[Candidate]: ...


class NotReadyCandidateFinder:
    """검색(AI-07)이 붙기 전 자리. 항상 SearchUnavailable."""

    async def find(self, request: SearchStreamRequest) -> list[Candidate]:
        raise SearchUnavailable("검색이 아직 연결되지 않았다")
