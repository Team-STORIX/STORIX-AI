import asyncio

import anthropic
import httpx2 as httpx
import pytest

from schemas.events import ErrorCode, ResultStatus
from schemas.search import SearchPolicy, SearchStreamRequest
from schemas.tools import RecommendClue, RecommendPick
from serving.answer.claude_answer import AnswerDone, TextDelta
from serving.config import Settings
from serving.pipeline.candidates import Candidate, NotReadyCandidateFinder
from serving.pipeline.search import run_search

SETTINGS = Settings(internal_token="t", pipeline_version="v-test", answer_timeout_seconds=0.5)
REQUEST = SearchStreamRequest(chat_id=1, message_id=2, user_id=3, question="계약결혼 로판",
                              policy=SearchPolicy(adult_allowed=False))
CANDIDATES = [Candidate(work_id=i, title=f"작품{i}", works_type="WEBTOON") for i in range(1, 8)]


class FixedFinder:
    def __init__(self, candidates):
        self.candidates = candidates

    async def find(self, request):
        return self.candidates


class FakeAnswerer:
    def __init__(self, items=(), error=None, delay=0.0):
        self.items, self.error, self.delay = items, error, delay

    async def stream(self, question, candidates, context, policy):
        for item in self.items:
            await asyncio.sleep(self.delay)
            yield item
        if self.error:
            raise self.error


def pick(work_id):
    return RecommendPick(work_id=work_id, reason="이유", matched_clues=[RecommendClue(text="로판", source="GENRE")])


async def collect(finder, answerer):
    return [event async for event in run_search(REQUEST, finder, answerer, SETTINGS)]


def run(finder, answerer):
    return asyncio.run(collect(finder, answerer))


def test_ok_flow_filters_outside_and_duplicate_picks():
    picks = [pick(2), pick(99), pick(2), pick(1), pick(3), pick(4), pick(5), pick(6)]
    events = run(FixedFinder(CANDIDATES), FakeAnswerer([TextDelta("고른 "), TextDelta("작품이에요."),
                                                         AnswerDone(picks=picks, refused=False)]))

    assert [e.event for e in events] == ["progress", "progress", "token", "token", "works", "done"]
    works = events[4]
    assert [w.work_id for w in works.recommended_works] == [2, 1, 3, 4, 5]
    assert [w.rank for w in works.recommended_works] == [1, 2, 3, 4, 5]
    assert works.candidate_work_ids == [c.work_id for c in CANDIDATES]
    assert works.pipeline_version == "v-test"
    assert events[-1].status == ResultStatus.OK


def test_no_candidates_is_no_result_without_llm():
    events = run(FixedFinder([]), FakeAnswerer(error=AssertionError("부르면 안 됨")))

    assert [e.event for e in events] == ["progress", "token", "works", "done"]
    assert events[-1].status == ResultStatus.NO_RESULT


def test_search_not_ready():
    events = run(NotReadyCandidateFinder(), FakeAnswerer())

    assert events[-1].event == "error"
    assert events[-1].code == ErrorCode.SEARCH_UNAVAILABLE


def test_empty_picks_is_no_result():
    events = run(FixedFinder(CANDIDATES), FakeAnswerer([TextDelta("단서를 더 알려 주세요."),
                                                         AnswerDone(picks=[], refused=False)]))

    assert events[-1].status == ResultStatus.NO_RESULT
    assert events[-2].recommended_works == []


def test_refusal_is_off_topic_without_works():
    events = run(FixedFinder(CANDIDATES), FakeAnswerer([AnswerDone(picks=[pick(1)], refused=True)]))

    assert events[-2].recommended_works == []
    assert events[-1].status == ResultStatus.OFF_TOPIC


def test_timeout():
    events = run(FixedFinder(CANDIDATES), FakeAnswerer([TextDelta("a"), TextDelta("b")], delay=0.4))

    assert events[-1].event == "error"
    assert events[-1].code == ErrorCode.TIMEOUT


def _response(status):
    return httpx.Response(status, request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"))


@pytest.mark.parametrize("error, code", [
    (anthropic.RateLimitError("rate", response=_response(429), body=None), ErrorCode.LLM_UNAVAILABLE),
    (anthropic.InternalServerError("down", response=_response(529), body=None), ErrorCode.LLM_UNAVAILABLE),
    (anthropic.BadRequestError("bad", response=_response(400), body=None), ErrorCode.INTERNAL),
    (ValueError("깨진 JSON"), ErrorCode.INTERNAL),
])
def test_llm_errors(error, code):
    events = run(FixedFinder(CANDIDATES), FakeAnswerer([TextDelta("a")], error=error))

    assert events[-1].event == "error"
    assert events[-1].code == code
