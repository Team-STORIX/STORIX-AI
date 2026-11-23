"""작품 enum 카탈로그.

enum 원본은 STORIX-BE 다. 파이썬에 복사해 두면 BE enum 이 바뀔 때 어긋나서, 기동 때
GET /internal/v1/ai/works/enum-catalog 를 받아 메모리에 들고 있는다 (크롤러와 같은 방식).
BE 없이 띄울 때(로컬 · CI)는 그 응답을 저장한 JSON 파일을 읽는다 (STORIX_AI_CATALOG_FILE).

장르 · 작품 유형 · 연령가 · 플랫폼 값은 이 모듈 밖에서 하드코딩하지 않는다.
tests/test_no_hardcoded_enums.py 가 막는다.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Literal

import httpx
from fastapi import Request

from schemas.works_catalog import EnumBlock, WorksCatalog
from serving.config import Settings

log = logging.getLogger(__name__)

CATALOG_PATH = "/internal/v1/ai/works/enum-catalog"
TOKEN_HEADER = "X-Internal-Token"

Kind = Literal["genre", "age_classification", "works_type", "platform"]
KINDS: tuple[Kind, ...] = ("genre", "age_classification", "works_type", "platform")


class CatalogUnavailable(RuntimeError):
    pass


class Catalog:
    def __init__(self, data: WorksCatalog):
        self.raw = data
        self._names: dict[Kind, list[str]] = {}
        self._lookup: dict[Kind, dict[str, str]] = {}
        self._labels: dict[Kind, dict[str, str]] = {}
        for kind in KINDS:
            block: EnumBlock = getattr(data, kind)
            self._names[kind] = [item.name for item in block.values]
            self._labels[kind] = {item.name: item.db_value for item in block.values}
            table: dict[str, str] = {}
            for item in block.values:
                table[item.name.upper()] = item.name
                table[_norm(item.db_value)] = item.name
            self._lookup[kind] = table

        unknown_adult = set(data.adult_age_classifications) - set(self._names["age_classification"])
        unknown_types = set(data.selectable_works_types) - set(self._names["works_type"])
        if unknown_adult or unknown_types:
            raise CatalogUnavailable(f"카탈로그 안에서 값이 안 맞음: {sorted(unknown_adult | unknown_types)}")

    def names(self, kind: Kind) -> list[str]:
        """enum 이름 목록 (예: ROFAN). 조건 추출 도구 enum · ES 필터 값."""
        return list(self._names[kind])

    def resolve(self, kind: Kind, value: str | None) -> str | None:
        """이름 · 한글 값 어느 쪽이 와도 이름으로. DB 에서 읽은 '로판' → 'ROFAN'. 못 맞추면 None."""
        text = (value or "").strip()
        if not text:
            return None
        table = self._lookup[kind]
        return table.get(text.upper()) or table.get(_norm(text))

    def label(self, kind: Kind, name: str) -> str:
        """이름 → 한글 값. 프롬프트에 사람이 읽는 말로 넣을 때."""
        return self._labels[kind][name]

    def is_adult(self, age_classification: str | None) -> bool:
        """연령가(이름 · 한글 값)가 19금인지."""
        return self.resolve("age_classification", age_classification) in self.raw.adult_age_classifications

    @property
    def selectable_works_types(self) -> list[str]:
        """챗봇 설정에서 고를 수 있는 작품 유형."""
        return list(self.raw.selectable_works_types)


def _norm(text: str) -> str:
    return "".join(text.split())


def load_catalog_file(path: str | Path) -> Catalog:
    body = json.loads(Path(path).read_text(encoding="utf-8"))
    return Catalog(WorksCatalog.model_validate(body))


async def fetch_catalog(settings: Settings, transport: httpx.AsyncBaseTransport | None = None) -> Catalog:
    """BE 에서 받는다. 같이 배포될 때 BE 가 늦게 뜰 수 있어서 몇 번 다시 시도하고, 그래도 안 되면 기동 실패."""
    if not settings.spring_base_url:
        raise CatalogUnavailable("STORIX_AI_SPRING_BASE_URL · STORIX_AI_CATALOG_FILE 중 하나가 필요함")
    headers = {TOKEN_HEADER: settings.internal_token.get_secret_value()}
    last_error: Exception | None = None
    async with httpx.AsyncClient(base_url=settings.spring_base_url, headers=headers,
                                 timeout=settings.catalog_timeout_seconds, transport=transport) as client:
        for attempt in range(1, settings.catalog_attempts + 1):
            try:
                response = await client.get(CATALOG_PATH)
                response.raise_for_status()
                return Catalog(WorksCatalog.model_validate(response.json()))
            except (httpx.HTTPError, ValueError) as error:
                last_error = error
                log.warning("enum 카탈로그 받기 실패 %d/%d: %s", attempt, settings.catalog_attempts, error)
                if attempt < settings.catalog_attempts:
                    await asyncio.sleep(settings.catalog_retry_seconds)
    raise CatalogUnavailable(f"enum 카탈로그를 못 받음: {last_error}") from last_error


async def load_catalog(settings: Settings) -> Catalog:
    if settings.catalog_file:
        return load_catalog_file(settings.catalog_file)
    return await fetch_catalog(settings)


def get_catalog(request: Request) -> Catalog:
    return request.app.state.catalog
