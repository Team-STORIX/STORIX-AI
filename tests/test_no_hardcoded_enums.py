"""장르 · 작품 유형 · 연령가 · 플랫폼 값을 코드에 직접 쓰지 않는다. 값은 serving/catalog.py 의 Catalog 에서 가져온다.

BE enum 이 바뀌면 하드코딩한 값은 조용히 어긋난다. 예: DB 에는 '로판', ES 필터는 'ROFAN' → 검색 0건, 오류 없음.
문자열 상수만 본다. 주석 · docstring 의 설명은 걸리지 않는다.
"""

import ast
import json
from pathlib import Path

from tests.conftest import CATALOG_FILE

ROOT = Path(__file__).parent.parent
SCANNED = ("serving", "indexing")
# 카탈로그 로더 자신만 예외
ALLOWED = {Path("serving/catalog.py")}


def banned_literals() -> set[str]:
    body = json.loads(CATALOG_FILE.read_text(encoding="utf-8"))
    banned: set[str] = set()
    for kind in ("genre", "ageClassification", "worksType", "platform"):
        for item in body[kind]["values"]:
            banned |= {item["name"], item["dbValue"]}
    return banned


def docstring_nodes(tree: ast.AST) -> set[int]:
    ids = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                ids.add(id(first.value))
    return ids


def find_hardcoded(source: str, banned: set[str]) -> list[tuple[int, str]]:
    tree = ast.parse(source)
    skip = docstring_nodes(tree)
    return [(node.lineno, node.value) for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
            and id(node) not in skip and node.value.strip() in banned]


def test_enum_values_come_from_catalog():
    banned = banned_literals()
    hits = []
    for folder in SCANNED:
        for path in sorted((ROOT / folder).rglob("*.py")):
            relative = path.relative_to(ROOT)
            if relative in ALLOWED:
                continue
            hits += [f"{relative}:{line} {value!r}" for line, value in find_hardcoded(path.read_text(encoding="utf-8"), banned)]
    assert not hits, "enum 값은 catalog 에서 가져온다 (catalog.names · catalog.resolve):\n" + "\n".join(hits)


def test_detector_catches_literals_and_ignores_docstrings():
    source = '''
"""모듈 설명에 ROFAN 이 나와도 괜찮다."""
GENRES = ["ROFAN", "로판"]
def f():
    """함수 설명의 로판도 괜찮다."""
    return {"term": {"genre": "MODERN_FANTASY"}}
'''
    assert [value for _, value in find_hardcoded(source, banned_literals())] == ["ROFAN", "로판", "MODERN_FANTASY"]
