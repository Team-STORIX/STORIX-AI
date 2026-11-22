# STORIX-BE 작품 데이터

> AI 쪽에서 쓸 수 있는 작품 데이터가 실제로 어떻게 생겼는지. STORIX-BE-2.0 엔티티 기준 (2026-11-22). 색인 계약(`schemas/index.py`) · 매핑 · 조건 추출은 여기 있는 값만 전제로 한다

## 1. 테이블

### `works` (작품)

| 칼럼 | 타입 | 내용 |
| --- | --- | --- |
| `works_id` | bigint | 작품 ID. 계약의 `workId` |
| `works_name` | varchar | 제목 |
| `normalized_name` | varchar | 검색용으로 정규화한 제목 |
| `works_type` | enum | 작품 유형. 아래 `WorksType` |
| `genre` | enum | 장르 **하나**. 아래 `Genre` |
| `age_classification` | enum | 연령 등급. 아래 `AgeClassification` |
| `description` | text | 작품 설명 (필수) |
| `artist_name` | varchar | 작가 표기 (작가 · 그림 작가를 합친 표시용) |
| `author` · `illustrator` · `original_author` | varchar | 글 · 그림 · 원작 작가 (없을 수 있음) |
| `thumbnail_url` | varchar | 표지 이미지 주소 |
| `reviews_count` | int | 리뷰 수 |
| `avg_rating` | double | 평균 별점 |

### `works_platform` (연재 플랫폼, 작품 하나에 여러 개)

| 칼럼 | 타입 | 내용 |
| --- | --- | --- |
| `works_id` | bigint | 작품 ID |
| `platform` | enum | 아래 `Platform`. (작품, 플랫폼) 중복 없음 |
| `landing_url` | varchar | 해당 플랫폼 작품 페이지 (없을 수 있음) |

### `hashtag` · `works_hashtag` (해시태그, 작품 하나에 여러 개)

- `hashtag(hashtag_id, name)`, `name` 은 겹치지 않음
- `works_hashtag(works_id, hashtag_id)` 로 연결

### `works_nickname` (별칭 · 줄임말)

- `works_nickname(works_id, nickname)`. 예: "전독시". 제목 검색 보조용

## 2. enum 값

| enum | 값 |
| --- | --- |
| `WorksType` | `WEBTOON` 웹툰 · `WEBNOVEL` 웹소설 · `COMIC` 만화 · `BOOK` 단행본 |
| `Genre` | `ROMANCE` 로맨스 · `FANTASY` 판타지 · `DAILY` 일상 · `ROFAN` 로판 · `HISTORICAL` 무협 · `DRAMA` 드라마 · `GAG` 개그 · `THRILLER` 스릴러 · `ACTION` 액션 · `SPORTS` 스포츠 · `SENTIMENTAL` 감성 · `BL` BL · `MODERN_FANTASY` 현판 |
| `AgeClassification` | `ALL` 전체연령가 · `AGE_12` · `AGE_15` · `AGE_18` |
| `Platform` | `NAVER_WEBTOON` · `KAKAO_PAGE` · `RIDIBOOKS` · `BOMTOON` · `NAVER_SERIES` · `LEZHIN` · `MRBLUE` |

- **성인 작품** = `age_classification = AGE_18` 만. 계약의 `adult` 는 이 값으로 채운다
- 챗봇 설정에서 고를 수 있는 작품 유형은 웹툰 · 웹소설 · 단행본. 만화(`COMIC`)는 작품 DB 에는 있지만 설정에서 못 고른다
- 장르는 작품당 하나다. 계약의 `genres` 는 목록이지만 지금은 값이 하나만 들어간다

## 3. 없는 것

| 정보 | 상태 | 영향 |
| --- | --- | --- |
| 완결 · 연재 여부 | 없음 | 필터 · 조건 추출에 못 씀. "완결된 거" 요청은 거르지 못한다고 답한다 |
| 회차 수 · 연재 요일 · 최신화 날짜 | 없음 | 쓰지 않는다 |
| 조회수 · 플랫폼 인기 순위 | 없음 | v2 인기 점수는 STORIX 안 데이터(관심작품 수 · 리뷰 수 · 별점)로 만든다 |
| 표지 외형 · 그림체 | 없음 | v2 표지 라벨 · 3단계 SigLIP 에서 새로 만든다 |

## 4. 사용자 쪽 (AI 서버는 직접 안 읽음)

- 취향 장르 · 해시태그, 서재(리뷰한 작품) · 관심작품 ID 는 Spring 내부 API `GET /internal/ai/users/{userId}/context` 로 받는다 ([api-contract.md](api-contract.md))
- 19금 허용 · 작품 유형 · 서재 작품 ID · 최근 대화는 질문마다 Spring 이 `SearchStreamRequest` 에 넣어 보낸다
- 대화 기록 · 챗봇 설정(`ai_chats` · `ai_chat_messages` · `ai_chat_settings`) 은 Spring 만 읽고 쓴다

---

작성자 : 이수아

업데이트 날짜 : 2026-11-22
