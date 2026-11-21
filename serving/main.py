from fastapi import Depends, FastAPI

from serving.config import get_settings
from serving.security import require_internal_token


def create_app() -> FastAPI:
    app = FastAPI(title="STORIX-AI", docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "UP", "pipelineVersion": get_settings().pipeline_version}

    @app.get("/internal/ping", dependencies=[Depends(require_internal_token)])
    def internal_ping() -> dict[str, str]:
        return {"status": "OK"}

    return app


app = create_app()
