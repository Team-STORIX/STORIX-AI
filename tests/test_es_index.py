"""works_ai 매핑이 색인 계약(IndexWork)과 맞는지. ES 가 있으면 실제로 만들어 nori · BM25 · 필터를 확인한다.

ES 확인은 STORIX_AI_TEST_ES_URL (예: http://localhost:9200, nori 플러그인 필요) 이 있을 때만 돈다.
"""

import os
import uuid

import pytest

from indexing.es_index import FILTER_FIELDS, TEXT_FIELDS, create_index, index_body, point_alias
from schemas.index import IndexWork

PROPERTIES = index_body()["mappings"]["properties"]


def test_mapping_fields_match_index_contract():
    assert set(PROPERTIES) == set(IndexWork.model_fields)


def test_filter_fields_are_exact_match():
    for field in FILTER_FIELDS:
        assert PROPERTIES[field]["type"] in ("keyword", "boolean"), field


def test_text_fields_exist_in_mapping():
    for spec in TEXT_FIELDS:
        path = spec.split("^")[0].split(".")
        node = PROPERTIES[path[0]]
        if len(path) > 1:
            node = node["fields"][path[1]]
        assert node["type"] == "text", spec


def test_mapping_is_strict():
    assert index_body()["mappings"]["dynamic"] == "strict"


ES_URL = os.environ.get("STORIX_AI_TEST_ES_URL")


@pytest.fixture
def es_index():
    if not ES_URL:
        pytest.skip("STORIX_AI_TEST_ES_URL 없음")
    from elasticsearch import Elasticsearch

    es = Elasticsearch(ES_URL)
    name = create_index(es, f"test_{uuid.uuid4().hex[:8]}")
    yield es, name
    es.indices.delete(index=name)


def tokens(es, index: str, field: str, text: str) -> list[str]:
    return [t["token"] for t in es.indices.analyze(index=index, field=field, text=text)["tokens"]]


def test_nori_splits_korean(es_index):
    es, name = es_index
    assert "육아" in tokens(es, name, "description", "은발 꼬마 육아물")


def test_bm25_with_filters(es_index):
    es, name = es_index
    # 필터 값은 실제 enum 과 무관한 가짜 이름. 매핑이 keyword 로 정확히 거르는지만 본다
    docs = [
        {"work_id": 1, "title": "북부 대공의 육아 일기", "description": "은발 꼬마를 키우는 육아물",
         "genres": ["G1"], "work_type": "WEBTOON", "platforms": ["P1"], "adult": False},
        {"work_id": 2, "title": "황녀의 육아", "description": "육아와 복수",
         "genres": ["G1"], "work_type": "WEBNOVEL", "platforms": ["P2"], "adult": True},
        {"work_id": 3, "title": "검술 학교", "nicknames": ["검학"], "description": "학원 액션",
         "genres": ["G2"], "work_type": "WEBTOON", "platforms": ["P1"], "adult": False},
    ]
    for doc in docs:
        es.index(index=name, id=str(doc["work_id"]), document=IndexWork.model_validate(doc).model_dump(mode="json"))
    es.indices.refresh(index=name)

    def ids(query: str, filters: list[dict]) -> list[int]:
        body = {"bool": {"must": {"multi_match": {"query": query, "fields": list(TEXT_FIELDS)}}, "filter": filters}}
        return [int(h["_id"]) for h in es.search(index=name, query=body)["hits"]["hits"]]

    assert set(ids("육아", [])) == {1, 2}
    assert ids("육아", [{"term": {"adult": False}}]) == [1]
    assert ids("육아", [{"terms": {"platforms": ["P2"]}}]) == [2]
    assert ids("검학", []) == [3]


def test_point_alias_moves_without_gap(es_index):
    es, name = es_index
    other = create_index(es, f"test_{uuid.uuid4().hex[:8]}")
    alias = "works_ai"
    had_alias = es.indices.exists_alias(name=alias)
    if had_alias:
        pytest.skip("이 ES 에 이미 works_ai 별칭이 있어 건드리지 않는다")
    try:
        point_alias(es, name)
        point_alias(es, other)
        assert list(es.indices.get_alias(name=alias)) == [other]
    finally:
        es.indices.delete(index=other)
