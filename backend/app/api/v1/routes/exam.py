from typing import Annotated

from api.deps import get_exam_service, get_userdata_strict
from api.v1.schemas import VerifyWordRequest
from fastapi import APIRouter, Depends, Query
from models.domain import TestWord, Tokens
from services.exam import ExamService
from services.pagination import (
    MAX_PAGE_SIZE,
    Paginated,
    Params,
    parse_cursor,
    paginate,
)

router = APIRouter(
    prefix="/exam",
    tags=["exam"],
)


@router.get("")
async def test_user(
    userdata: Annotated[Tokens, Depends(get_userdata_strict)],
    service: Annotated[ExamService, Depends(get_exam_service)],
    limit: int = Query(10, alias="per_page", ge=1, le=MAX_PAGE_SIZE),
    cursor: str | None = None,
) -> Paginated[TestWord]:
    params = Params(
        limit=limit,
        cursor=parse_cursor(cursor),
    )
    return await paginate(params, lambda q: service.test_words(userdata.username, q))


@router.post("")
async def verify_word(
    userdata: Annotated[Tokens, Depends(get_userdata_strict)],
    service: Annotated[ExamService, Depends(get_exam_service)],
    req: VerifyWordRequest,
):
    result = await service.verify_word(userdata.username, req.word_id, req.answer, req.reverse)
    return {"result": result}