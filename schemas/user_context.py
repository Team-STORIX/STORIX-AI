from pydantic import Field

from schemas.base import ContractModel


class UserContext(ContractModel):
    """GET /internal/users/{userId}/context 응답. 닉네임 · 이메일은 넣지 않는다."""

    preferred_genres: list[str] = Field(default_factory=list)
    preferred_hashtags: list[str] = Field(default_factory=list)
    library_work_ids: list[int] = Field(default_factory=list)
    favorite_work_ids: list[int] = Field(default_factory=list)
