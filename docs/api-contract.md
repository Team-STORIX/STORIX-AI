# API 계약

형식의 원본은 `schemas/` 다. 이 문서는 초안이고, 확정되면 `schemas/` 와 맞춘다.

## 1. API

| 구분 | API | 설명 |
| --- | --- | --- |
| 앱 → Spring | `POST /api/v1/ai-search/chats` | 대화방 만들기. 첫 대화면 온보딩을 같이 내려줌 |
| 앱 → Spring | `POST /api/v1/ai-search/chats/{chatId}/messages` | 질문 보내기. SSE 응답 |
| 앱 → Spring | `GET /api/v1/ai-search/chats/{chatId}/messages` | 지난 대화 보기 |
| 앱 → Spring | `GET · PUT /api/v1/ai-search/settings` | 챗봇 설정 (19금 · 작품 유형) |
| 앱 → Spring | `GET /api/v1/ai-search/examples` | 예시 질문 |
| Spring → AI | `POST /internal/search/stream` | 질문 · 대화 맥락 · 사용자 설정 전달, SSE 응답 |
| Spring → AI | `POST /internal/index/works` | 작품 증분 색인 · 삭제 |
| AI → Spring | `GET /internal/users/{userId}/context` | 취향 장르 · 해시태그, 서재 · 관심작품 ID |

## 2. SSE 이벤트

`progress` → `token` (여러 번) → `works` (최대 5개) → `done` / `error`

```
event: progress
data: {"step":"SEARCHING","message":"작품 찾는 중…"}

event: token
data: {"text":"은발 꼬마와 "}

event: works
data: {"recommendedWorks":[{"rank":1,"workId":123,"title":"…","thumbnailUrl":"…","platform":"카카오페이지","matchedClues":[{"text":"은발 보라 눈 유아","source":"COVER"}]}],"pipelineVersion":"v1.0"}

event: done
data: {"chatId":12,"messageId":31}
```

| 이벤트 | 앱에서 할 일 |
| --- | --- |
| progress | 진행 표시 |
| token | 말풍선에 글자 이어 붙이기 |
| works | 작품 카드 (배열 순서 = 추천 순위) |
| done | 입력창 다시 켜기 |
| error | 오류 화면 |

- `title` · `thumbnailUrl` · `platform` 은 Spring 이 DB 값으로 채운다. AI 서버는 `workId` · 이유 · 단서만 보낸다
- `messageId` · `pipelineVersion` · `rank` 는 GA 이벤트와 서버 기록을 이어 붙이는 키

## 3. 최종 응답 (대화 기록 조회 형식)

```json
{
  "message": "은발 꼬마와 귀족 보호자가 나오는 육아물이에요.",
  "works": [
    { "workId": 123, "title": "…", "platform": "카카오페이지",
      "matchedClues": [{ "text": "은발 보라 눈 유아", "source": "COVER" }] }
  ],
  "status": "OK"
}
```

| status | 의미 | 화면 |
| --- | --- | --- |
| OK | 정상 답변. works 가 있으면 카드형 | 작품 추천 대화 / text 대화 |
| NO_RESULT | 맞는 작품 없음 | text 대화 |
| OFF_TOPIC | 작품 외 질문 | text 대화 |
| ERROR | 오류 · 한도 초과 | 오류 |

## 4. 색인 결과 형식

| 구분 | 항목 |
| --- | --- |
| 입력 | work_id, 설명, 태그, 장르 (v2: 표지 URL) |
| 출력 | work_id, embed_text, text_vector, 모델 이름 · 버전 (v2: 라벨 JSON, image_vector) |

## 5. 채점 결과 형식

채점 스크립트(`eval/`)는 CLI 한 번으로 돌고 결과를 JSON 으로 낸다. PR 평가 · Hub 평가 게이트 · 출시 기준 측정이 같은 형식을 쓴다. 항목은 AI-02 에서 확정한다.
