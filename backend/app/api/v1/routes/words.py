from typing import Annotated

from api.deps import get_userdata, get_userdata_strict, get_word_service
from api.v1.mappers import word_domain_to_api
from api.v1.schemas import AddWordRequest, SearchResponse
from fastapi import APIRouter, Depends, Query, Security, status
from models.domain import Tokens, Word
from services.pagination import (
    MAX_PAGE_SIZE,
    Paginated,
    Params,
    paginate,
    parse_cursor,
    parse_sort_fields,
)
from services.words import WordService

router = APIRouter(
    tags=["words"],
)

#: Search is not cursor paginated, so its page size needs an explicit ceiling.
MAX_SEARCH_LIMIT = 50


@router.get("/words")
async def word_list(
    service: Annotated[WordService, Depends(get_word_service)],
    userdata: Annotated[Tokens | None, Security(get_userdata, scopes=[])],
    limit: int = Query(10, alias="per_page", ge=1, le=MAX_PAGE_SIZE),
    sort: str = Query("en", min_length=1),
    desc: bool = Query(False),
    cursor: str | None = None,
) -> Paginated[Word]:
    params = Params(
        sort=parse_sort_fields(sort, Word.valid_sort_fields()),
        desc=desc,
        limit=limit,
        cursor=parse_cursor(cursor),
    )
    if userdata:
        params.username = userdata.username
    return await paginate(params, service.words)


@router.post("/words", status_code=status.HTTP_201_CREATED)
async def add_word_global(
    userdata: Annotated[Tokens, Security(get_userdata_strict, scopes=["admin"])],
    service: Annotated[WordService, Depends(get_word_service)],
    word_data: AddWordRequest,
):
    word = Word(
        en=word_data.en,
        ru=word_data.ru,
        transcription=word_data.transcription,
        examples=word_data.examples,
    )
    # A duplicate word is reported as AlreadyExistsError -> 409.
    await service.add_word(word)
    return {"status": "ok"}


@router.get("/search")
async def search(
    userdata: Annotated[Tokens | None, Security(get_userdata, scopes=[])],
    service: Annotated[WordService, Depends(get_word_service)],
    query: str = Query(min_length=2),
    limit: int = Query(10, alias="per_page", ge=1, le=MAX_SEARCH_LIMIT),
) -> SearchResponse:
    user = userdata.username if userdata else None
    words_domain = await service.search(query, limit, user)
    return SearchResponse(items=[word_domain_to_api(w) for w in words_domain])


@router.get("/words/{word}")
async def get_word(
    service: Annotated[WordService, Depends(get_word_service)],
    word: str,
) -> Word:
    # A missing word is reported as NotFound -> 404.
    return await service.get_word(word)
