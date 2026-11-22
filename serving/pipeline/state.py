"""파이프라인 단계 사이에 넘기는 값. 단계 함수는 state 를 받아 자기 칸을 채워 돌려준다."""

from dataclasses import dataclass, field

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


@dataclass
class SearchState:
    request: SearchStreamRequest
    # ① 조건 추출 결과. AI-06 에서 형식을 정해 채운다
    conditions: dict = field(default_factory=dict)
    # ②③ 검색 결과
    candidates: list[Candidate] = field(default_factory=list)
