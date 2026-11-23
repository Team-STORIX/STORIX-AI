# serving

검색 API, 파이프라인 단계 ①~⑦, 답변 레이어, Claude 스트림 → SSE 변환. 설계는 [serving.md](../docs/architecture/serving.md)

| 파일 | 내용 |
| --- | --- |
| `main.py` | 앱 생성, `/health` |
| `config.py` | 환경변수 `STORIX_AI_*` 를 설정 클래스로 |
| `security.py` | `/internal/**` 서비스 토큰 확인 |
| `catalog.py` | 작품 enum 카탈로그. 기동 때 BE 에서 받아 `app.state.catalog` 에 둔다. enum 값은 여기서만 가져온다 |
| `sse.py` | SearchEvent → SSE 프레임, heartbeat |
| `pipeline/state.py` | 단계 사이에 넘기는 `SearchState` (요청 · 조건 · 후보), `Candidate` |
| `pipeline/extract.py` | ① 조건 추출 (AI-06 자리) |
| `pipeline/search.py` | ②③ 필터 · 검색 (AI-07 자리). `CandidateFinder` 를 바꿔 끼운다 |
| `pipeline/answer.py` | ⑦ Sonnet 스트리밍 답변, `recommend_works` 검증, 후보 밖 작품 거르기 |
| `pipeline/prompt.py` | 시스템 프롬프트 · 도구 · 질문 턴 (AI-09a 에서 `prompts/` 로) |
| `pipeline/run.py` | 순서 정의: extract → search → answer, 단계별 progress · 오류 변환 |

단계 함수는 `state` 를 받아 자기 칸을 채워 돌려준다. 새 단계는 `pipeline/` 에 파일을 하나 만들고 `run.py` 순서에 끼운다
