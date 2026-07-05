from typing import Annotated

from api.deps import get_exam_service, get_userdata_strict
from api.v1.schemas import VerifyWordRequest
from core import errors
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from models.domain import TestWord
from pydantic import ValidationError
from services.exam import ExamService
from services.pagination import Paginated, Params, decode_cursor, paginate

router = APIRouter(
    prefix="/exam",
    tags=["exam"],
)


@router.get("")
async def test_user(
    userdata: Annotated[str, Depends(get_userdata_strict)],
    service: Annotated[ExamService, Depends(get_exam_service)],
    limit: int = Query(10, alias="per_page"), 
    cursor: str | None = None,
) -> Paginated[TestWord]:
    if cursor:
        try:
            parsed_cur = decode_cursor(cursor)
        except ValidationError:
            parsed_cur = None
    else:
        parsed_cur = None

    params = Params(
        limit=limit, 
        cursor=parsed_cur,
    )
    words = await paginate(params, lambda q: service.test_words(userdata.username, q))
    return words


@router.post("")
async def verify_word(
    userdata: Annotated[str, Depends(get_userdata_strict)],
    service: Annotated[ExamService, Depends(get_exam_service)],
    req: VerifyWordRequest,
):
    try:
        result = await service.verify_word(userdata.username, req.word_id, req.answer, req.reverse)
        return JSONResponse({"result": result})
    except errors.NotFound as e:
        return JSONResponse({"detail": str(e)}, status.HTTP_404_NOT_FOUND)
