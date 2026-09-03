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
    sort: list[str] = Field(default_factory=list)
    desc: bool | None = None
    cursor: Cursor | None = None
    username: str | None = None


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
    json_bytes = base64.urlsafe_b64decode(cur)
    return Cursor.model_validate_json(json_bytes)


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
        username=params.username,
    )

    if params.cursor:
        if not params.cursor.next:
            backward = True

        query_params.sort_by = params.cursor.field.split(",")
        if backward:
            query_params.desc = not params.cursor.desc
        else:
            query_params.desc = params.cursor.desc
        query_params.pointer = params.cursor.value.split(",")

    items = await fn(query_params)
    pi = Paginated(items=items)

    if len(pi.items) == 0:
        return pi

    if backward:
        pi.items.sort(
            key=lambda item: tuple(getattr(item, f) for f in query_params.sort_by),
            reverse=query_params.desc,
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

    cur = params.cursor or Cursor(field=",".join(query_params.sort_by), desc=params.desc, value="", next=True)

    def get_cursor_value(item):
        return ",".join(str(getattr(item, f)) for f in query_params.sort_by)

    if has_next:
        pi.has_next = True
        cur.next = True

        if backward and len(items) > params.limit:
            pi.items.pop(0)
        else:
            pi.items.pop()

        cur.value = get_cursor_value(pi.items[-1])
        pi.next_cursor = encode_cursor(cur)

    if has_prev:
        pi.has_prev = True
        cur.next = False
        if backward:
            cur.value = get_cursor_value(pi.items[0])
        else:
            cur.value = get_cursor_value(pi.items[0])
        pi.prev_cursor = encode_cursor(cur)
    return pi
