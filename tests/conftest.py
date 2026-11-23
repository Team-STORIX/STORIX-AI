from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from serving.config import get_settings

CATALOG_FILE = Path(__file__).parent / "fixtures" / "works_catalog.json"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("STORIX_AI_INTERNAL_TOKEN", "test-token")
    monkeypatch.setenv("STORIX_AI_CATALOG_FILE", str(CATALOG_FILE))
    get_settings.cache_clear()
    from serving.main import create_app

    yield TestClient(create_app())
    get_settings.cache_clear()
