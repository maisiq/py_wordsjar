import base64
from typing import Any, Callable, Coroutine, Generic, TypeVar

from pydantic import BaseModel, Field
from repository.params import QueryParams

T = TypeVar("T")


class Cursor(BaseModel):
    field: str
    desc: bool | None
    value: str
    next: bool


class Params(BaseModel):
    limit: int = Field(default=10, lt=101)
    sort: str | None = None
    desc: bool | None = None
    cursor: Cursor | None = None


class Paginated(BaseModel, Generic[T]):
    items: list[T]
    has_next: bool = False
    has_prev: bool = False
    next_cursor: str = ""
    prev_cursor: str = ""


def encode_cursor(cur: Cursor) -> str:
    cursor = cur.model_dump_json()
    cur_encoded = base64.urlsafe_b64encode(bytes(cursor, encoding="utf8"))
    return str(cur_encoded, encoding="utf8")


def decode_cursor(cur: str) -> Cursor:
    json_str = base64.urlsafe_b64decode(cur)
    return Cursor.model_validate_json(json_str)


async def paginate(
    params: Params, 
    fn: Callable[[QueryParams], Coroutine[Any, Any, list[T]]],
) -> Paginated[T]:
    limit = params.limit + 1
    backward = False

    query_params = QueryParams(
        limit=limit,
        desc=params.desc,
        sort_by=params.sort,
    )

    if params.cursor:
        if not params.cursor.next:
            backward = True

        query_params.sort_by = params.cursor.field
        if backward:
            query_params.desc = not params.cursor.desc
        else:
            query_params.desc = params.cursor.desc
        query_params.pointer = params.cursor.value

    items = await fn(query_params)

    if backward:
        items.sort(
            key=lambda item: getattr(item, params.cursor.field),
            reverse=params.cursor.desc,
        )

    has_next = False
    has_prev = False

    extra = len(items) > params.limit

    if extra:
        has_next = True
    
    if params.cursor:
        if params.cursor.next:
            has_prev = True
        else:
            has_next = True
            if extra:
                has_prev = True
    
    pi = Paginated(items=items)

    cur = params.cursor or Cursor(field="en", desc=params.desc, value="", next=True)

    if has_next:
        pi.has_next = True
        cur.next = True

        if backward and len(items) <= params.limit:
            if len(items) > 0:
                cur.value = getattr(pi.items[-1], cur.field)
                pi.next_cursor = encode_cursor(cur)
        elif backward:
            pi.items = items[1:params.limit+1]
            cur.value = getattr(pi.items[-1], cur.field)
            pi.next_cursor = encode_cursor(cur)
        else:
            pi.items = items[:params.limit]
            cur.value = getattr(pi.items[-1], cur.field)
            pi.next_cursor = encode_cursor(cur)

    if has_prev:
        pi.has_prev = True
        cur.next = False
        if backward:
            cur.value = getattr(pi.items[0], cur.field)
        else:
            cur.value = getattr(pi.items[0], cur.field)
        pi.prev_cursor = encode_cursor(cur)
    return pi