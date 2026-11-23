import asyncio
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from schemas.works_catalog import WorksCatalog
from serving.catalog import (
    CATALOG_PATH,
    Catalog,
    CatalogUnavailable,
    fetch_catalog,
    load_catalog_file,
)
from serving.config import Settings, get_settings
from tests.conftest import CATALOG_FILE


@pytest.fixture
def catalog() -> Catalog:
    return load_catalog_file(CATALOG_FILE)


def settings(**overrides) -> Settings:
    base = {"internal_token": "test-token", "spring_base_url": "http://be", "catalog_retry_seconds": 0}
    return Settings(**{**base, **overrides})


def test_names_are_enum_names(catalog):
    assert "ROFAN" in catalog.names("genre")
    assert "로판" not in catalog.names("genre")


def test_resolve_accepts_name_or_db_value(catalog):
    assert catalog.resolve("genre", "로판") == "ROFAN"
    assert catalog.resolve("genre", "rofan") == "ROFAN"
    assert catalog.resolve("age_classification", "18세이용가") == "AGE_18"
    assert catalog.resolve("genre", "없는장르") is None
    assert catalog.resolve("genre", None) is None


def test_label_and_rules(catalog):
    assert catalog.label("genre", "ROFAN") == "로판"
    assert catalog.is_adult("AGE_18") and catalog.is_adult("18세 이용가")
    assert not catalog.is_adult("AGE_15")
    assert "COMIC" not in catalog.selectable_works_types


def test_rejects_rule_outside_enum():
    body = json.loads(CATALOG_FILE.read_text(encoding="utf-8"))
    body["adultAgeClassifications"] = ["AGE_19"]
    with pytest.raises(CatalogUnavailable):
        Catalog(WorksCatalog.model_validate(body))


def test_fetch_sends_token_and_reads_response():
    body = CATALOG_FILE.read_text(encoding="utf-8")
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["token"] = request.headers.get("X-Internal-Token")
        return httpx.Response(200, content=body, headers={"Content-Type": "application/json"})

    catalog = asyncio.run(fetch_catalog(settings(), httpx.MockTransport(handler)))
    assert seen == {"path": CATALOG_PATH, "token": "test-token"}
    assert catalog.resolve("genre", "현판") == "MODERN_FANTASY"


def test_fetch_retries_then_succeeds():
    body = CATALOG_FILE.read_text(encoding="utf-8")
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        if len(calls) < 3:
            return httpx.Response(503)
        return httpx.Response(200, content=body, headers={"Content-Type": "application/json"})

    asyncio.run(fetch_catalog(settings(catalog_attempts=3), httpx.MockTransport(handler)))
    assert len(calls) == 3


def test_fetch_gives_up_after_attempts():
    with pytest.raises(CatalogUnavailable):
        asyncio.run(fetch_catalog(settings(catalog_attempts=2), httpx.MockTransport(lambda r: httpx.Response(401))))


def test_fetch_needs_spring_base_url():
    with pytest.raises(CatalogUnavailable):
        asyncio.run(fetch_catalog(settings(spring_base_url=None)))


def test_app_loads_catalog_on_startup(client):
    with client:
        assert client.app.state.catalog.resolve("genre", "로판") == "ROFAN"


def test_app_fails_to_start_without_catalog(monkeypatch):
    monkeypatch.setenv("STORIX_AI_INTERNAL_TOKEN", "test-token")
    # 로컬 .env 보다 앞서게 빈 값으로 덮는다
    monkeypatch.setenv("STORIX_AI_CATALOG_FILE", "")
    monkeypatch.setenv("STORIX_AI_SPRING_BASE_URL", "")
    get_settings.cache_clear()
    from serving.main import create_app

    with pytest.raises(CatalogUnavailable), TestClient(create_app()):
        pass
    get_settings.cache_clear()
