import pytest
from pydantic import TypeAdapter, ValidationError

from schemas.eval_policy import PolicyCase
from schemas.events import SearchEvent, WorksEvent
from schemas.export import OUT_DIR, render
from schemas.search import SearchStreamRequest
from schemas.tools import RecommendWorksInput
from schemas.works_catalog import WorksCatalog


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
            "policy": {"adultDefault": False, "adultVerified": False, "workTypes": ["WEBNOVEL"], "excludedWorkIds": [3]},
        }
    )
    assert request.policy.excluded_work_ids == [3]
    assert request.model_dump(by_alias=True)["policy"]["adultDefault"] is False


def test_unknown_field_is_rejected():
    with pytest.raises(ValidationError):
        SearchStreamRequest.model_validate(
            {
                "chatId": 1,
                "messageId": 1,
                "userId": 1,
                "question": "q",
                "policy": {"adultDefault": True, "adultVerified": True},
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


def test_policy_case_example_is_valid():
    case = PolicyCase.model_validate(
        {
            "questionId": "oos-001",
            "category": "OUT_OF_SCOPE",
            "question": "오늘 서울 날씨 어때?",
            "policy": {"adultDefault": False, "adultVerified": False, "workTypes": [], "excludedWorkIds": []},
            "expect": {"statuses": ["OFF_TOPIC"], "maxWorks": 0},
        }
    )
    assert case.expect.must_not_say == []
    with pytest.raises(ValidationError):
        PolicyCase.model_validate({**case.model_dump(by_alias=True), "expect": {"statuses": [], "maxWorks": 0}})


def _catalog_payload() -> dict:
    def block(stored_as: str, *pairs: tuple[str, str]) -> dict:
        return {"storedAs": stored_as, "values": [{"name": n, "dbValue": v} for n, v in pairs]}

    return {
        "genre": block("dbValue", ("ROFAN", "로판"), ("BL", "BL")),
        "ageClassification": block("dbValue", ("ALL", "전체연령가"), ("AGE_18", "18세 이용가")),
        "worksType": block("dbValue", ("WEBTOON", "웹툰"), ("COMIC", "만화")),
        "platform": block("name", ("NAVER_WEBTOON", "네이버 웹툰")),
        "adultAgeClassifications": ["AGE_18"],
        "selectableWorksTypes": ["WEBTOON", "WEBNOVEL", "BOOK"],
    }


def test_works_catalog_reads_be_response():
    catalog = WorksCatalog.model_validate(_catalog_payload())
    assert catalog.genre.stored_as == "dbValue"
    assert catalog.genre.values[0].name == "ROFAN"
    assert catalog.platform.stored_as == "name"
    assert catalog.adult_age_classifications == ["AGE_18"]


def test_works_catalog_rejects_unknown_field():
    with pytest.raises(ValidationError):
        WorksCatalog.model_validate({**_catalog_payload(), "unknown": 1})
