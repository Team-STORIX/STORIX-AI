import asyncio

import pytest

from schemas.search import SearchPolicy, SearchStreamRequest
from serving.pipeline.extract import extract
from serving.pipeline.search import NotReadyCandidateFinder, SearchUnavailable, search
from serving.pipeline.state import Candidate, SearchState


def make_state() -> SearchState:
    request = SearchStreamRequest(chat_id=1, message_id=2, user_id=3, question="로판",
                                  policy=SearchPolicy(adult_allowed=False))
    return SearchState(request=request)


class OneFinder:
    async def find(self, request):
        return [Candidate(work_id=7, title="작품", works_type="WEBTOON")]


def test_extract_passes_state_through():
    state = make_state()
    assert asyncio.run(extract(state)) is state


def test_search_fills_candidates():
    state = asyncio.run(search(make_state(), OneFinder()))
    assert [c.work_id for c in state.candidates] == [7]


def test_search_not_ready_raises():
    with pytest.raises(SearchUnavailable):
        asyncio.run(search(make_state(), NotReadyCandidateFinder()))
