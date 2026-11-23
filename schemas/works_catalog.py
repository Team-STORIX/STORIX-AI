from typing import Literal

from pydantic import Field

from schemas.base import ContractModel


class EnumItem(ContractModel):
    name: str = Field(description="enum 이름. 계약 · 색인 · 필터는 이 값을 쓴다 (예: ROFAN)")
    db_value: str = Field(description="한글 표기. storedAs 가 dbValue 면 DB 에 이 값이 들어 있다 (예: 로판)")


class EnumBlock(ContractModel):
    stored_as: Literal["name", "dbValue"] = Field(description="DB 칼럼에 name · dbValue 중 무엇이 저장되는지")
    values: list[EnumItem] = Field(min_length=1)


class WorksCatalog(ContractModel):
    """GET /internal/v1/ai/works/enum-catalog 응답. enum 원본은 STORIX-BE 이고 AI 서버는 기동 때 받아 쓴다."""

    genre: EnumBlock
    age_classification: EnumBlock
    works_type: EnumBlock
    platform: EnumBlock
    adult_age_classifications: list[str] = Field(
        min_length=1, description="19금으로 보는 연령가 enum 이름. 지금은 AGE_18 만"
    )
    selectable_works_types: list[str] = Field(
        min_length=1, description="챗봇 설정에서 고를 수 있는 작품 유형 enum 이름. 만화(COMIC)는 빠진다"
    )
