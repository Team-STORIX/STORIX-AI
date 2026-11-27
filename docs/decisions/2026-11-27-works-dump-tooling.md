# 작품 덤프 받기 · 보기

- 날짜: 2026-11-27
- 상태: 확정 (도구는 STORIX-AI-Hub #4)

색인 · embed_text 규칙 · 임베딩 비교 · 평가 세트 정답 고르기는 실제 작품 데이터로 해야 한다. prod 작품 목록은 매일 덤프로 비공개 S3 에 올라가고(Hub 덤프 Lambda), 이 레포에는 데이터를 두지 않는다

## 결정

| 항목 | 결정 | 이유 |
| --- | --- | --- |
| 받기 | Hub 스크립트 · 스킬 `works-fetch` ("작품 덤프 받아 줘"). 최신 팩을 찾아 manifest 의 sha256 · 건수로 확인 | 버킷 · 팩 경로를 사람이 찾지 않게. 평가 세트 받기(`eval-fetch`)와 같은 방식 |
| 받는 곳 | 레포 밖 `~/storix-data/works/<env>/<팩>/works.jsonl` | 어느 레포에서 실행해도 prod 데이터가 공개 레포 작업 폴더에 놓이지 않게. git 훅보다 확실하다 |
| 접근 권한 | 각자 IAM 계정 (`aws configure`, 콘솔 로그인 불필요). 팀원 정책에 `*/data/works/*` 읽기 | 받은 기록이 계정 단위로 남는다 |
| 보기 | DuckDB. jsonl 을 import 없이 SQL 로 읽고, 브라우저 UI(`duckdb -ui`)와 IDE Database 창(IntelliJ · DataGrip · PyCharm)에서 본다 ("작품 덤프 열어 줘") | 서버 · 적재 없이 파일 하나로. 배열 컬럼(`hashtags` · `platforms`)도 `unnest` 로 집계. 작품 6천여 건은 즉시 |
| 역할 나누기 | 후보 찾기 · 정답 고르기는 DuckDB, 평가 세트 파일 쓰기 · 검증은 파이썬 + `schemas/` | 형식 검증은 계약 모델로 한 곳에서 |
| 다른 도구 | Pandas · Polars 는 코드로 돌리는 작업(임베딩 비교 등)에서 필요할 때. DuckDB 결과를 `.df()` · `.pl()` 로 넘길 수 있다. jsonlines 같은 읽기 전용 라이브러리는 쓰지 않는다 | 6천여 건이라 속도 차이가 의미 없다 |
| 금지 | 온라인 JSON 뷰어 · 웹 AI 채팅에 덤프를 붙이지 않는다. 슬랙 · 노션 · 이슈에도 | prod 데이터가 밖으로 나간다 |
| OS | macOS · Windows(Git Bash) 같은 스크립트 | 팀 개발 환경이 섞여 있다 |

## 덤프를 읽을 때 주의

- `genre` · `worksType` · `ageClassification` 는 DB 저장값 그대로 한글(`로판`), `platforms` 만 enum 이름(`KAKAO_PAGE`)이다
- 색인 · 필터 · 계약에는 이름을 쓴다. `serving/catalog.py` 의 `catalog.resolve("genre", "로판")` → `ROFAN`

## 남은 것

- 이 레포에서 덤프를 읽는 모듈 (`STORIX_AI_WORKS_FILE` 로 경로를 받아 enum 을 이름으로 바꿔 돌려줌). 색인(AI-04c) 작업에서
- `works-fetch` 를 Claude Code 플러그인으로 배포해 어느 레포에서든 부를지. 지금은 Hub 레포 스킬

## 관련

- dev 작품은 prod 와 같은 작품 ID 로 매일 맞춘다 (STORIX-BE-2.0 #475). prod 덤프로 고른 평가 세트 정답을 dev 서버에서도 그대로 쓸 수 있다

---

작성자 : 이수아
