from enum import StrEnum


class WorkType(StrEnum):
    WEBTOON = "WEBTOON"
    WEBNOVEL = "WEBNOVEL"
    BOOK = "BOOK"


class ClueSource(StrEnum):
    DESCRIPTION = "DESCRIPTION"
    TAG = "TAG"
    GENRE = "GENRE"
    COVER = "COVER"
    REVIEW = "REVIEW"
