"""① 조건 추출. AI-06 에서 Haiku tool use 로 작품 유형 · 장르 · 범위 밖 여부를 뽑아 state.conditions 에 채운다."""

from serving.pipeline.state import SearchState


async def extract(state: SearchState) -> SearchState:
    # AI-06 전까지는 그대로 넘긴다
    return state
