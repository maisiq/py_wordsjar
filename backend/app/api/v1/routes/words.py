from typing import Annotated

from api.deps import get_userdata_strict, get_word_service
from api.v1.schemas import AddWordRequest
from core import errors
from fastapi import APIRouter, Depends, Query, Security, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from services.pagination import Paginated, Params, decode_cursor, paginate
from services.words import Word, WordService

router = APIRouter(
    prefix="/words",
    tags=["words"],
)


@router.get("")
async def word_list(
    service: Annotated[WordService, Depends(get_word_service)],
    limit: int = Query(10, alias="per_page"),
    sort: str = Query("en", min_length=1),
    desc: bool = Query(False),
    cursor: str | None = None,
) -> Paginated[Word]:
    if cursor:
        try:
            parsed_cur = decode_cursor(cursor)
        except ValidationError as e:
            parsed_cur = None
    else:
        parsed_cur = None

    if not Word.is_valid_sort_field(sort):
        return JSONResponse(
            {"detail": f"Invalid sort field. Possible values are {Word.valid_sort_fields}"}, 
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    params = Params(
        sort=sort,
        desc=desc,
        limit=limit,
        cursor=parsed_cur,
    )
    try:
        return await paginate(params, service.words)
    except (errors.InternalError, Exception):
        return JSONResponse({"detail": "internal error"}, status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("")
async def add_word_global(
    userdata: Annotated[str, Security(get_userdata_strict, scopes=["admin"])],
    service: Annotated[WordService, Depends(get_word_service)],
    word_data: AddWordRequest,
):
    word = Word(
        en=word_data.en,
        ru=word_data.ru,
        transcription=word_data.transcription,
    )
    try:
        await service.add_word(word)
        return JSONResponse({"status": "ok"})
    except errors.AlreadyExistsError as e:
        return JSONResponse({"detail": str(e)}, status.HTTP_400_BAD_REQUEST)
    except (errors.InternalError, Exception):
        return JSONResponse({"detail": "internal error"}, status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/{word}")
async def get_word(
    service: Annotated[WordService, Depends(get_word_service)],
    word: str
) -> Word:
    try:
        return await service.get_word(word)
    except errors.NotFound as e:
        return JSONResponse({"detail": str(e)}, status.HTTP_404_NOT_FOUND)
    except (errors.InternalError, Exception):
        return JSONResponse({"detail": "internal error"}, status.HTTP_500_INTERNAL_SERVER_ERROR)
