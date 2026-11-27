---
name: works-fetch
description: STORIX 작품 목록 덤프(prod DB, 매일 05:00 갱신)를 받아 레포 밖 ~/storix-data 에 풀고 DuckDB 로 연다. 색인 · embed_text · 조건 추출 · 평가 세트 정답 고르기를 실제 작품으로 할 때. "작품 덤프 받아 줘", "작품 덤프 열어 줘", "works.jsonl 줘", "최신 작품 데이터", "DuckDB 로 작품 보기" 요청 시 사용.
---

# 작품 덤프 받기 · 보기

스크립트는 비공개 레포 STORIX-AI-Hub 에 있고, 이 레포는 서브모듈 `hub/` 로 연결해 그 스크립트를 부른다.
자세한 규칙은 `hub/.claude/skills/works-fetch/SKILL.md`. 데이터는 레포 밖에 받으므로 이 공개 레포 폴더에는 아무것도 생기지 않는다.

## 처음 한 번

```bash
git submodule update --init hub     # Hub 접근 권한이 있는 계정이어야 한다
aws sts get-caller-identity         # 본인 IAM 계정이 보이면 된다. 없으면 aws configure
```

- DuckDB: macOS `brew install duckdb`, Windows `winget install DuckDB.cli` (Windows 는 Git Bash 에서)
- `hub/` 가 비어 있으면 위 첫 줄을 먼저 돌린다

## 쓰기

| 요청 | 실행 |
| --- | --- |
| 최신 덤프 받기 | `hub/scripts/works-fetch.sh` |
| 특정 팩 받기 | `hub/scripts/works-fetch.sh prod <팩 ID>` |
| 받고 DuckDB UI 열기 (http://localhost:4213) | `hub/scripts/works-open.sh` (에이전트는 백그라운드로 띄우고, 다 보면 끈다) |
| DB 파일만 (IntelliJ · DataGrip · PyCharm 에서 붙일 때) | `hub/scripts/works-open.sh --no-ui` |
| 자주 쓰는 쿼리 | `hub/scripts/works-queries.sql` |

- 결과: `~/storix-data/works/<env>/<팩 ID>/works.jsonl`, `~/storix-data/works.duckdb` (뷰 `works` · `works_tags` · `works_platforms`)
- 스크립트가 바뀌었으면 `git submodule update --remote hub` 로 Hub 최신 main 을 받는다

## 이 레포 코드에서 쓸 때

- 덤프의 `genre` · `worksType` · `ageClassification` 은 한글 저장값(`로판`), `platforms` 만 enum 이름(`KAKAO_PAGE`)이다
- 색인 · 필터 · 계약에는 이름을 쓴다: `catalog.resolve("genre", "로판")` → `ROFAN` (`serving/catalog.py`). 하드코딩하면 `tests/test_no_hardcoded_enums.py` 가 막는다
- 경로는 `~/storix-data/...` 를 그대로 읽는다. 이 레포로 복사하지 않는다

## 지킬 것

- prod 작품 데이터다. git · 슬랙 · 노션 · 이슈 · 온라인 JSON 뷰어 · 웹 AI 에 붙이지 않는다
- 덤프를 바로 다시 만드는 건 관리자만 한다 (작품 데이터 작업)
