import pytest
from fastapi.testclient import TestClient

from serving.config import get_settings


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("STORIX_AI_INTERNAL_TOKEN", "test-token")
    get_settings.cache_clear()
    from serving.main import create_app

    yield TestClient(create_app())
    get_settings.cache_clear()
