from pydantic import Field

from schemas.base import ContractModel
from schemas.common import WorkType


class IndexWork(ContractModel):
    work_id: int
    title: str
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    genres: list[str] = Field(default_factory=list)
    work_type: WorkType
    platforms: list[str] = Field(default_factory=list, description="연재 플랫폼. 작품 하나가 여러 곳에 있을 수 있다")
    adult: bool


class IndexWorksRequest(ContractModel):
    """POST /internal/index/works. 작품 적재 · 수정 · 삭제 때 Spring 이 부른다."""

    upserts: list[IndexWork] = Field(default_factory=list, max_length=500)
    delete_work_ids: list[int] = Field(default_factory=list, max_length=500)


class IndexWorksResponse(ContractModel):
    indexed: int
    deleted: int
    failed_work_ids: list[int] = Field(default_factory=list)


class EmbeddingModel(ContractModel):
    name: str
    version: str
    dims: int


class IndexedWork(ContractModel):
    """색인 배치 결과 한 건. 형식이 같으면 안에서 어떤 모델을 쓰든 서빙은 그대로 동작한다."""

    work_id: int
    embed_text: str
    text_vector: list[float]
    model: EmbeddingModel
