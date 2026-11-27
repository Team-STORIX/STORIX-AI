"""works_ai 인덱스 만들기 · 별칭 바꾸기.

서빙은 별칭 works_ai 만 본다. 실제 인덱스는 works_ai_<버전> 으로 만들고, 다 채운 뒤 별칭만 옮긴다
(매핑 · 임베딩 모델이 바뀌어도 검색이 끊기지 않게). 매핑 원본은 works_ai_index.json.

1차(AI-04a): 필터 필드(enum 이름) + nori 텍스트 필드. 2차에 벡터 필드를 더한다.
"""

import json
from pathlib import Path

from elasticsearch import Elasticsearch

ALIAS = "works_ai"
INDEX_FILE = Path(__file__).with_name("works_ai_index.json")

# 필터에 쓰는 keyword 필드. 값은 catalog 의 enum 이름 (예: genres 에 '로판' 이 아니라 이름)
FILTER_FIELDS = ("genres", "work_type", "platforms", "adult")
# BM25 로 찾는 텍스트 필드와 가중치. AI-07b 에서 평가 세트로 조정한다
TEXT_FIELDS = ("title^3", "title.bigram", "nicknames^3", "nicknames.bigram", "authors^2",
               "tags.text^2", "description")


def index_body() -> dict:
    return json.loads(INDEX_FILE.read_text(encoding="utf-8"))


def index_name(version: str) -> str:
    return f"{ALIAS}_{version}"


def create_index(es: Elasticsearch, version: str) -> str:
    """works_ai_<version> 을 새로 만든다. 이미 있으면 ES 가 거절한다 (덮어쓰지 않음)."""
    name = index_name(version)
    body = index_body()
    es.indices.create(index=name, settings=body["settings"], mappings=body["mappings"])
    return name


def point_alias(es: Elasticsearch, index: str) -> None:
    """별칭 works_ai 를 index 로 옮긴다. 붙이기 · 떼기를 한 요청으로 해서 비는 순간이 없다."""
    actions: list[dict] = [{"add": {"index": index, "alias": ALIAS}}]
    if es.indices.exists_alias(name=ALIAS):
        current = es.indices.get_alias(name=ALIAS)
        actions = [{"remove": {"index": old, "alias": ALIAS}} for old in current if old != index] + actions
    es.indices.update_aliases(actions=actions)
