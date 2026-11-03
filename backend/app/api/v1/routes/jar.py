from typing import Annotated

from api.deps import get_jar_service, get_userdata_strict
from api.v1.schemas import (
    AddJarWordRequest,
    AddWordsToJarResponse,
    DeleteJarWordRequest,
    SuccessResponse,
)
from fastapi import APIRouter, Depends, Query, Security, status
from models.domain import JarWord, Tokens, Word
from services.jar import JarService
from services.pagination import (
    MAX_PAGE_SIZE,
    Paginated,
    Params,
    paginate,
    parse_cursor,
    parse_sort_fields,
)

router = APIRouter(
    prefix="/jar",
    tags=["jar"],
)


@router.get("")
async def jar_words(
    userdata: Annotated[Tokens, Security(get_userdata_strict, scopes=["user", "admin"])],
    service: Annotated[JarService, Depends(get_jar_service)],
    sort: str = Query("rating,id", alias="order_by", min_length=1),
    desc: bool = Query(False),
    limit: int = Query(10, alias="per_page", ge=1, le=MAX_PAGE_SIZE),
    cursor: str | None = None,
) -> Paginated[Word]:
    params = Params(
        limit=limit,
        desc=desc,
        sort=parse_sort_fields(sort, JarWord.valid_sort_fields()),
        cursor=parse_cursor(cursor),
    )
    return await paginate(params, lambda q: service.words(userdata.username, q))


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_words_to_jar(
    userdata: Annotated[Tokens, Security(get_userdata_strict, scopes=["user", "admin"])],
    service: Annotated[JarService, Depends(get_jar_service)],
    word_data: AddJarWordRequest,
):
    result = await service.add_words(userdata.username, word_data.words_en, word_data.status)
    return AddWordsToJarResponse(count=result)


@router.delete("")
async def delete_word_from_jar(
    userdata: Annotated[Tokens, Security(get_userdata_strict, scopes=["user", "admin"])],
    service: Annotated[JarService, Depends(get_jar_service)],
    payload: DeleteJarWordRequest,
) -> SuccessResponse:
    await service.delete_word(userdata.username, payload.word)
    return SuccessResponse()
