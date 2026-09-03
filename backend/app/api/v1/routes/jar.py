from typing import Annotated

from api.deps import get_jar_service, get_userdata_strict
from api.v1.schemas import AddJarWordRequest
from fastapi import APIRouter, Depends, Query, Security, status
from fastapi.responses import JSONResponse
from models.domain import JarWord, Word
from pydantic import ValidationError
from services.jar import JarService
from services.pagination import Paginated, Params, decode_cursor, paginate

router = APIRouter(
    prefix="/jar",
    tags=["jar"],
)


@router.get("")
async def jar_words(
    userdata: Annotated[str, Security(get_userdata_strict, scopes=["user", "admin"])],
    service: Annotated[JarService, Depends(get_jar_service)],
    sort: str = Query("rating,id", alias="order_by", min_length=1),
    desc: bool = Query(False),
    limit: int = Query(10, alias="per_page"), 
    cursor: str | None = None,
) -> Paginated[Word]:
    if cursor:
        try:
            parsed_cur = decode_cursor(cursor)
        except ValidationError:
            parsed_cur = None
    else:
        parsed_cur = None

    sort_fields = sort.split(",")
    for field in sort_fields:
        if not JarWord.is_valid_sort_field(field):
            return JSONResponse(
                {"detail": f"Invalid sort field ({field}). Possible values are {JarWord.valid_sort_fields}"}, 
                status.HTTP_400_BAD_REQUEST,
            )

    params = Params(
        limit=limit,
        desc=desc,
        sort=sort_fields,
        cursor=parsed_cur,
    )
    words = await paginate(params, lambda q: service.words(userdata.username, q))
    return words


@router.post("")
async def add_word_to_jar(
    userdata: Annotated[str, Security(get_userdata_strict, scopes=["user", "admin"])],
    service: Annotated[JarService, Depends(get_jar_service)],
    word_data: AddJarWordRequest,
):
    await service.add_words(userdata.username, word_data.words_en, word_data.status)
    return JSONResponse({"status": "ok"})
