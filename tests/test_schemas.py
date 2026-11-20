import pytest
from pydantic import TypeAdapter, ValidationError

from schemas.events import SearchEvent, WorksEvent
from schemas.export import OUT_DIR, render
from schemas.search import SearchStreamRequest
from schemas.tools import RecommendWorksInput


def test_json_schema_is_up_to_date():
    expected = render()
    actual = {p.name: p.read_text(encoding="utf-8") for p in OUT_DIR.glob("*.schema.json")}
    assert actual == expected, "uv run python -m schemas.export 로 다시 만들어 커밋한다"


def test_request_uses_camel_case():
    request = SearchStreamRequest.model_validate(
        {
            "chatId": 12,
            "messageId": 31,
            "userId": 7,
            "question": "계약결혼 로판 중에 완결된 거",
            "policy": {"adultAllowed": False, "workTypes": ["WEBNOVEL"], "excludedWorkIds": [3]},
        }
    )
    assert request.policy.excluded_work_ids == [3]
    assert request.model_dump(by_alias=True)["policy"]["adultAllowed"] is False


def test_unknown_field_is_rejected():
    with pytest.raises(ValidationError):
        SearchStreamRequest.model_validate(
            {
                "chatId": 1,
                "messageId": 1,
                "userId": 1,
                "question": "q",
                "policy": {"adultAllowed": True},
                "adult": True,
            }
        )


def test_event_is_parsed_by_event_name():
    event = TypeAdapter(SearchEvent).validate_python(
        {
            "event": "works",
            "recommendedWorks": [{"rank": 1, "workId": 123, "reason": "은발 유아 주인공"}],
            "candidateWorkIds": [123, 456],
            "pipelineVersion": "v1.0",
        }
    )
    assert isinstance(event, WorksEvent)


def test_at_most_five_recommendations():
    picks = [{"workId": i, "reason": "r"} for i in range(6)]
    with pytest.raises(ValidationError):
        RecommendWorksInput.model_validate({"works": picks})
