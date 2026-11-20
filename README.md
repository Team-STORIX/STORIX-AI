<h1>
<img src="https://github.com/user-attachments/assets/b65bf457-6754-4e0d-9d94-4511721b2b36" align=left width=100>
STORIX-AI
</h1>

> 이야기에 대한 이야기로 모두가 연결되는 이 곳! 데이터로 취향을 연결하는 웹툰·웹소설 팬덤 플랫폼, STORIX

<br>

STORIX 의 AI 작품 검색 서버입니다. "계약결혼 로판 중에 완결된 거"처럼 말로 물어보면, 미리 색인한 작품에서 후보를 찾고 Claude 가 그중 최대 5개를 골라 추천합니다.

```
앱 ──질문──▶ STORIX-BE (Spring) ──내부 호출──▶ STORIX-AI (FastAPI) ──▶ Elasticsearch · Claude
   ◀──SSE──                      ◀──SSE──
```

- 앱은 STORIX-AI 를 직접 부르지 않습니다. 로그인 · 사용 횟수 · 대화 기록 · 작품 검증은 Spring 이 합니다
- 작품은 `recommend_works` 도구로 넘긴 작품 ID 로만 추천합니다. 후보에 없는 작품은 말하지 않습니다
- 색인 팩 빌드 · 배포는 비공개 레포 STORIX-AI-Hub 에서 합니다. 이 레포에는 데이터를 두지 않습니다

## 🛠️ Tech Stack

<table>
  <tr>
    <td align="center"><b>Language</b></td>
    <td>
      <img alt="Python-3.12" src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white">
    </td>
  </tr>
  <tr>
    <td align="center"><b>Serving</b></td>
    <td>
      <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white">
      <img alt="Uvicorn" src="https://img.shields.io/badge/Uvicorn-2C2C2C?style=flat-square">
      <img alt="Pydantic" src="https://img.shields.io/badge/Pydantic-E92063?style=flat-square&logo=pydantic&logoColor=white">
      <img alt="SSE" src="https://img.shields.io/badge/SSE-555555?style=flat-square">
    </td>
  </tr>
  <tr>
    <td align="center"><b>LLM</b></td>
    <td>
      <img alt="Claude Haiku" src="https://img.shields.io/badge/Claude_Haiku-D97757?style=flat-square&logo=anthropic&logoColor=white">
      <img alt="Claude Sonnet" src="https://img.shields.io/badge/Claude_Sonnet-D97757?style=flat-square&logo=anthropic&logoColor=white">
    </td>
  </tr>
  <tr>
    <td align="center"><b>Search</b></td>
    <td>
      <img alt="Elasticsearch-8.18" src="https://img.shields.io/badge/Elasticsearch-8.18-005571?style=flat-square&logo=elasticsearch&logoColor=white">
      <img alt="kNN + BM25" src="https://img.shields.io/badge/kNN_+_BM25-005571?style=flat-square">
    </td>
  </tr>
  <tr>
    <td align="center"><b>Indexing</b></td>
    <td>
      <img alt="sentence-transformers" src="https://img.shields.io/badge/sentence--transformers-FFD21E?style=flat-square&logo=huggingface&logoColor=black">
      <img alt="VLM" src="https://img.shields.io/badge/VLM_표지_라벨링-6E40C9?style=flat-square">
      <img alt="SigLIP" src="https://img.shields.io/badge/SigLIP-4285F4?style=flat-square&logo=google&logoColor=white">
    </td>
  </tr>
  <tr>
    <td align="center"><b>테스트 · 평가</b></td>
    <td>
      <img alt="pytest" src="https://img.shields.io/badge/pytest-0A9EDC?style=flat-square&logo=pytest&logoColor=white">
      <img alt="Recall@10 · MRR" src="https://img.shields.io/badge/Recall@10_·_MRR-555555?style=flat-square">
    </td>
  </tr>
</table>

## 🧭 Architecture

```mermaid
flowchart TB
  subgraph IDX["색인 · 배치"]
    W["작품 DB<br/>설명 · 태그 · 장르"]
    U["공개 UGC<br/>리뷰 · 피드 · 토픽룸"]
    C["표지 이미지"]
    VLM["VLM<br/>표지 라벨링"]
    ET["embed_text"]
    TE["텍스트 임베딩 모델"]
    SIG["SigLIP"]
    C --> VLM --> ET
    W --> ET
    U --> ET
    ET --> TE
    C --> SIG
  end

  ES[("Elasticsearch<br/>text_vector · image_vector")]
  TE -- text_vector --> ES
  SIG -- image_vector --> ES

  subgraph SRV["서빙 · 질문할 때"]
    APP["앱"]
    SP["Spring<br/>STORIX-BE"]
    FA["FastAPI<br/>STORIX-AI"]
    CL["Claude API"]
    APP -- 질문 --> SP
    SP -- SSE --> APP
    SP -- 내부 호출 --> FA
    FA -- SSE --> SP
    FA -- 스트리밍 --> CL
    FA -- "취향 · 서재 조회" --> SP
  end

  FA -- "후보 20개" --> ES
  HUB["STORIX-AI-Hub<br/>색인 팩 빌드 · 배포"] -- "팩 복원 · 별칭 교체" --> ES
```

| 단계 | 하는 일 |
|---|---|
| ① 조건 추출 | Haiku 가 질문에서 작품 유형 · 완결 · 소재 · 분위기를 뽑음 |
| ② 필터 | 19금 · 작품 유형 같은 정책값은 Spring 이 넘긴 값만 씀 |
| ③ 검색 | kNN + BM25 하이브리드, RRF 로 합쳐 후보 20개 |
| ④ 답변 | Sonnet 이 후보와 단서만 보고 최대 5개를 `recommend_works` 로 고름 |
| ⑤ 스트리밍 | `progress` → `token` → `works` → `done` / `error` |

## 📚 Docs

| 문서 | 내용 |
|---|---|
| [기술 구조](docs/architecture.md) | 전체 구조 · 검색 파이프라인 · 구성 요소 · 응답 흐름 · 인프라 제약 |
| [색인과 임베딩](docs/indexing.md) | 임베딩 · 데이터별 색인 · 표지 라벨 · VLM vs SigLIP · Elasticsearch |
| [서빙과 스트리밍](docs/serving.md) | FastAPI · DB 커넥션 · 사용자 데이터 접근 · SSE · 프롬프트 · 대화 기억 |
| [레포와 API 계약](docs/api-contract.md) | API · SSE 이벤트 · 최종 응답 · 색인 결과 형식 · 평가 결과 형식 |
| [온보딩 · 챗봇 설정](docs/onboarding.md) | 첫 대화 흐름 · 기본 멘트 · 설정 · 검색 반영 규칙 |
| [MVP 데이터](docs/mvp-data.md) | 추천에 쓰는 작품 · 사용자 · 대화 데이터 |
| [개발 계획](docs/plan.md) | 단계 · 기술 스택 · 정책 · 단계별 할 일 · 기대 결과 |
| [역할 분담](docs/roles.md) | 작업 목록 · 작업 순서 |
| [결정 기록](docs/decisions) | 날짜와 이유를 같이 남긴 결정 |

개발 규칙은 [AGENTS.md](AGENTS.md), 브랜치 · PR · 릴리스 규칙은 [agents/conventions/git.md](agents/conventions/git.md) 에 있습니다.

## 📂 File Structure

```
.
├── serving/          # 검색 API · 파이프라인 단계 · 답변 레이어 · SSE 변환
├── indexing/
│   ├── labeling/     # VLM 표지 라벨링
│   ├── image_embed/  # SigLIP → image_vector
│   └── text_embed/   # embed_text → text_vector
├── prompts/          # 프롬프트 (git 으로 버전 관리)
├── eval/             # 채점 스크립트 (평가 세트 원본은 커밋 안 됨)
├── schemas/          # 주고받는 형식 정의 (계약의 원본)
└── docs/             # 설계 문서
```

<br>

## 🛠️ Developers

| <img src="https://github.com/Immmii.png" width="160px"> | <img src="https://github.com/codus02.png" width="160px"> |
|:---:|:---:|
| __이수아<br>[@Immmii](https://github.com/Immmii)__ | __이채연<br>[@codus02](https://github.com/codus02)__ |
| 개발 환경 · CI · 인프라 · Hub 배포 <br/> Spring 연동 · API 계약 · SSE 스트리밍 | 임베딩 · 색인 · 검색 <br/> 프롬프트 · 평가 세트 · 채점 |
