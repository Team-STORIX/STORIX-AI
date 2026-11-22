"""schemas/json/ 에 JSON Schema 를 쓴다. Spring 은 이 파일을 보고 DTO 를 맞춘다.

uv run python -m schemas.export
"""

import json
from pathlib import Path

from pydantic import BaseModel, TypeAdapter

from schemas.eval import EvalReport
from schemas.eval_policy import PolicyCase
from schemas.events import SearchEvent
from schemas.index import IndexedWork, IndexWorksRequest, IndexWorksResponse
from schemas.search import SearchStreamRequest
from schemas.tools import RecommendWorksInput
from schemas.user_context import UserContext

OUT_DIR = Path(__file__).parent / "json"

TARGETS: dict[str, type[BaseModel] | TypeAdapter] = {
    "search-stream-request": SearchStreamRequest,
    "search-event": TypeAdapter(SearchEvent),
    "recommend-works-input": RecommendWorksInput,
    "index-works-request": IndexWorksRequest,
    "index-works-response": IndexWorksResponse,
    "indexed-work": IndexedWork,
    "user-context": UserContext,
    "eval-report": EvalReport,
    "policy-case": PolicyCase,
}


def render() -> dict[str, str]:
    files = {}
    for name, target in TARGETS.items():
        if isinstance(target, TypeAdapter):
            schema = target.json_schema(by_alias=True)
        else:
            schema = target.model_json_schema(by_alias=True)
        files[f"{name}.schema.json"] = json.dumps(schema, ensure_ascii=False, indent=2) + "\n"
    return files


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    for old in OUT_DIR.glob("*.schema.json"):
        old.unlink()
    for filename, text in render().items():
        (OUT_DIR / filename).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
