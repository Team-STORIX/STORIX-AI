# 브랜치 · 커밋 · PR · 릴리스

## 흐름

`develop` 에 기능 PR → `release/vX.Y.Z` → `main`. STORIX-BE 와 같은 Release 방식이다.

| 단계 | 규칙 |
| --- | --- |
| 이슈 | 작업 전에 이슈부터 만든다 |
| 브랜치 | `develop` 에서 딴다. Feat · Refactor · Chore · Docs 는 `feature/`, Fix 는 `hotfix/` |
| PR | base 는 `develop`. 본문 관련 이슈에 `Closes #N` |
| 머지 | `develop` PR 은 merge commit, `main` Release PR 만 squash |
| 릴리스 | `main` 에서 `release/vX.Y.Z` 를 따서 나갈 커밋을 cherry-pick, PR 제목은 `Release vX.Y.Z` |

`develop` · `main` 에 직접 push 하지 않는다.

## 커밋 · PR 제목

- `Type: 내용` 명사형 종결. Type 은 `Feat` · `Fix` · `Refactor` · `Chore` · `Docs`
- 커밋 메시지는 제목만 쓴다
- 제목에 팀원 실명을 넣지 않는다

## 라벨

STORIX-BE 와 같은 다섯 개만 쓴다.

| 라벨 | 쓰는 곳 |
| --- | --- |
| `:rocket: feat` | 기능 |
| `🐛 bug` | 버그 수정 |
| `:hammer: refactor` | 리팩터링 |
| `:memo: docs` | 문서 |
| `:globe_with_meridians: chore` | 설정 · CI · 릴리스 |

## PR 에 남길 것

- 프롬프트 · 검색 로직 · 임베딩을 바꾸면 같은 평가 세트로 돌린 점수(Recall@10 · MRR · 추천 Precision · 후보 밖 작품 비율)를 바꾸기 전과 나란히 적는다
- 점수가 떨어졌으면 이유와 그래도 올리는 근거를 같이 적는다
- 데이터 · 비밀값 · 서버 주소는 본문에도 넣지 않는다. 키 이름만 적는다
