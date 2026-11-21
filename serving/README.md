# serving

검색 API, 파이프라인 단계 ①~⑦, 답변 레이어, Claude 스트림 → SSE 변환. 설계는 [serving.md](../docs/architecture/serving.md)

| 파일 | 내용 |
| --- | --- |
| `main.py` | 앱 생성, `/health` |
| `config.py` | 환경변수 `STORIX_AI_*` 를 설정 클래스로 |
| `security.py` | `/internal/**` 서비스 토큰 확인 |
