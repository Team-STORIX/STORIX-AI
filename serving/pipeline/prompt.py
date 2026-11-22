"""답변(⑦) 프롬프트 초안. AI-09a 에서 prompts/ 의 system.md · user_turn 으로 옮긴다."""

from schemas.search import ChatContext, SearchPolicy
from schemas.tools import RecommendWorksInput
from serving.pipeline.state import Candidate

RECOMMEND_TOOL_NAME = "recommend_works"

# 바이트가 바뀌면 캐시가 깨진다. 날짜 · 요청별 값은 여기 넣지 않는다
SYSTEM_PROMPT = """너는 웹툰 · 웹소설 팬덤 앱 STORIX 의 작품 탐색 도우미야.
사용자가 말로 설명한 작품을, 메시지에 주어진 후보 목록 안에서만 골라 추천해.

규칙
- 후보 목록에 없는 작품은 말하지도 추천하지도 마. 작품 이름을 지어내지 마
- 추천할 작품은 반드시 recommend_works 도구로 넘겨. 배열 순서가 추천 순위고 최대 5개야
- 맞는 작품이 없으면 recommend_works 를 빈 배열로 부르고, 어떤 단서를 더 주면 찾기 쉬운지 짧게 물어봐
- 답변 글은 ~해요체로 한두 문장. 작품별 설명은 도구의 reason 에 쓰고 본문에서 반복하지 마
- 결말 · 반전 같은 스포일러는 쓰지 마
- 작품 찾기와 상관없는 요청은 정중히 거절하고 찾고 싶은 작품을 물어봐
"""


def recommend_tool() -> dict:
    return {
        "name": RECOMMEND_TOOL_NAME,
        "description": "후보 목록에서 고른 추천 작품을 순위대로 넘긴다. 맞는 작품이 없으면 빈 배열",
        # 스트리밍이라 입력 조각을 바로 받는다. 서버 검증이 꺼지므로 받은 쪽에서 다시 검증한다
        "eager_input_streaming": True,
        "input_schema": RecommendWorksInput.model_json_schema(by_alias=True),
    }


def _candidate_line(candidate: Candidate) -> str:
    tags = ", ".join(candidate.tags) if candidate.tags else "-"
    genre = candidate.genre or "-"
    adult = " | 19금" if candidate.adult else ""
    return (f"- workId={candidate.work_id} | {candidate.title} | {candidate.works_type} | 장르 {genre}{adult} | "
            f"태그 {tags}\n  {candidate.description.strip()}")


def user_turn(question: str, candidates: list[Candidate], context: ChatContext, policy: SearchPolicy) -> str:
    lines = ["[후보 작품]", *(_candidate_line(c) for c in candidates)]
    if context.shown_work_ids:
        lines += ["", f"[이미 보여 준 작품] {', '.join(map(str, context.shown_work_ids))} — 다시 추천하지 마"]
    if context.conditions:
        lines += ["", f"[사용자가 붙인 조건] {' / '.join(context.conditions)}"]
    if not policy.adult_verified:
        lines += ["", "[정책] 사용자는 성인 인증 전이라 19금 작품 표지가 가려져 보인다. "
                      "19금 작품 표지를 보여 달라거나 묘사해 달라고 하면 성인 인증 후 볼 수 있다고만 안내하고, "
                      "표지 내용은 말하지 마"]
    lines += ["", "[질문]", question]
    return "\n".join(lines)
