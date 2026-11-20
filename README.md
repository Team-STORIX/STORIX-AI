# STORIX-AI

웹툰 · 웹소설 팬덤 앱 STORIX 의 AI 작품 검색 서버입니다.
"계약결혼 로판 중에 완결된 거"처럼 말로 물어보면, 미리 색인한 작품에서 후보를 찾고 Claude 가 그중 최대 5개를 골라 추천합니다.

- Python 3.12 · FastAPI · Claude API (Haiku · Sonnet) · Elasticsearch
- 앱 → STORIX-BE(Spring) → STORIX-AI 순서로 호출되고, 답변은 SSE 로 흘러갑니다

설계는 [docs/architecture.md](docs/architecture.md), 개발 규칙은 [AGENTS.md](AGENTS.md) 에 있습니다.
