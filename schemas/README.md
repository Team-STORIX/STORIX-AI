# schemas

Spring · AI 서버 · 앱이 같이 쓰는 형식의 원본. Pydantic 모델로 정의하고 `json/` 에 JSON Schema 로 내보낸다.
설명은 [api-contract.md](../docs/architecture/api-contract.md). 바꾸면 STORIX-BE 와 같이 바꾼다.

| 파일 | 형식 | JSON Schema |
| --- | --- | --- |
| `search.py` | `POST /internal/search/stream` 요청 (질문 · 정책값 · 대화 맥락) | `search-stream-request` |
| `events.py` | AI → Spring SSE 이벤트 (progress · token · works · done · error) | `search-event` |
| `tools.py` | Sonnet `recommend_works` 도구 입력 | `recommend-works-input` |
| `index.py` | `POST /internal/index/works` 요청 · 응답, 색인 결과 한 건 | `index-works-request` · `index-works-response` · `indexed-work` |
| `user_context.py` | `GET /internal/users/{userId}/context` 응답 | `user-context` |
| `eval.py` | 채점 결과 (이채연과 같이 확정 전 초안) | `eval-report` |
| `eval_policy.py` | 정책 질문 한 건 ([eval/policy](../eval/policy/README.md)) | `policy-case` |

- JSON 필드는 camelCase, 모르는 필드는 거절한다
- 모델을 바꾸면 `uv run python -m schemas.export` 로 `json/` 을 다시 만든다. 안 맞으면 테스트가 실패한다
