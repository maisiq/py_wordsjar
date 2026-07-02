from typing import Annotated

from api.deps import get_jar_service, get_userdata_strict
from api.v1.schemas import AddJarWordRequest
from fastapi import APIRouter, Depends, Query, Security, status
from fastapi.responses import JSONResponse
from models.domain import Word
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
    sort: str = Query("en", alias="order_by", min_length=1),
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
 
    if not Word.is_valid_sort_field(sort):
        return JSONResponse(
            {"detail": f"Invalid sort field. Possible values are {Word.valid_sort_fields}"}, 
            status.HTTP_400_BAD_REQUEST,
        )

    params = Params(
        limit=limit,
        desc=desc,
        sort=sort,
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
    try:
        await service.add_word(userdata.username, word_data.word_en, word_data.status)
        return JSONResponse({"status": "ok"})
    except Exception as e:
        return JSONResponse({"detail": "internal error"}, 400)
