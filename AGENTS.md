# STORIX-AI

STORIX 앱의 AI 작품 검색 서버. 사용자의 자연어 질문을 받아 작품 후보를 찾고, Claude 가 후보만 보고 최대 5개를 추천한다(RAG).
Claude Code · Codex 같은 AI 도구가 같이 읽는 규칙 원본이다. `CLAUDE.md` 는 이 파일을 불러오기만 한다.

## 먼저 지킬 것

- 공개 레포다. 작품 · UGC 데이터, 평가 세트 원본, 임베딩 결과, 비밀값, 서버 주소는 커밋하지 않는다. 데이터는 비공개 저장소(S3)에만 둔다
- 앱이 이 서버를 직접 부르지 않는다. STORIX-BE(Spring)만 내부망으로 부른다. 인증 · 사용 횟수 · 대화 저장은 Spring 몫이다
- 19금 · 미성년자 · 서재 제외 값은 Spring 이 넘긴 값만 쓴다. 프롬프트나 모델 출력으로 정책을 바꾸지 않는다
- 추천 작품은 `recommend_works` 도구로 작품 ID 만 받는다. 제목 · 표지 · 플랫폼은 Spring 이 DB 값으로 채운다
- 요청 · 응답 · SSE 이벤트 형식은 `schemas/` 가 원본이다. 바꾸면 STORIX-BE 와 같이 바꾼다
- 프롬프트 · 검색 로직을 바꾸면 평가 세트로 숫자를 비교하고 나아졌을 때만 배포한다
- 답변 · 주석 · 커밋 · PR 은 한국어로 쓴다. `develop` · `main` 에 직접 push 하지 않는다

## 자주 쓰는 명령

아직 코드가 없다. FastAPI 뼈대(AI-01a)를 만들 때 여기에 실행 · 테스트 · 평가 명령을 적는다.

## 폴더

| 폴더 | 내용 |
| --- | --- |
| `serving/` | 검색 API, 파이프라인 단계 ①~⑦, 답변 레이어, SSE 변환 |
| `indexing/` | 작품 색인 스크립트, 증분 색인 로직 |
| `prompts/` | `system.md` · `examples.md` · `user_turn.jinja` |
| `eval/` | 채점 스크립트. 평가 세트 원본은 커밋하지 않음 |
| `schemas/` | API · SSE · 색인 결과 · 채점 결과 형식 |
| `docs/` | 설계 문서와 결정 기록 |

## 문서

| 문서 | 내용 |
| --- | --- |
| [docs/architecture.md](docs/architecture.md) | 전체 구조, 파이프라인 ①~⑦, 구성 요소, 인프라 제약 |
| [docs/indexing.md](docs/indexing.md) | 임베딩, embed_text, 표지 라벨, ES 매핑 · 적재 |
| [docs/serving.md](docs/serving.md) | FastAPI, 요청 흐름과 DB 커넥션, 내부 API, SSE, 답변 레이어, 대화 기억 |
| [docs/api-contract.md](docs/api-contract.md) | 레포 구조, 앱 · Spring · AI 사이 API, 응답 형식, SSE 이벤트, 개발 순서, 평가 지표 |
| [docs/onboarding.md](docs/onboarding.md) | 첫 대화 온보딩과 챗봇 설정 |
| [docs/plan.md](docs/plan.md) | 단계별 범위, 기술 스택, 데이터, 기대 결과, 출시 · 배포 기준, 평가 지표 |
| [docs/mvp-data.md](docs/mvp-data.md) | MVP 추천에 쓰는 작품 · 사용자 · 대화 데이터와 안 쓰는 데이터 |
| [docs/roles.md](docs/roles.md) | 작업 목록 · 담당 · 순서 |
| [docs/decisions/](docs/decisions) | 결정 기록 |

## 논의 중

| 항목 | 지금 상태 |
| --- | --- |
| 질문 · 작품 임베딩 모델 | Claude API 는 임베딩을 제공하지 않아 별도 모델이 필요. 후보 비교(AI-03a) 필요 |
| AI 서버 · ES 위치 | 앱 서버(메모리 4GB)에 같이 둘지, 분리할지 |
| 사용 제한을 켤 비용 기준 | 비용 지표를 모은 뒤 결정 |
| MVP 조건 추출 항목 | 파이프라인 ① 에는 소재 · 분위기가 있지만 AI-06 작업 목록에는 없음. 팀 확인 필요 |
| 관심작품 · 취향의 MVP 사용 방식 | 내부 API 로 가져오지만 순위 반영 방법은 안 정해짐 ([mvp-data.md](docs/mvp-data.md)) |
