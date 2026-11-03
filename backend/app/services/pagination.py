"""Keyset pagination with signed, validated cursors.

A cursor is a base64 encoded JSON payload plus an HMAC signature. The signature
makes the cursor tamper proof: previously a client could put any column name
into the payload and have it used as SQL, and any value that failed the type
coercion became a 500. Now an unknown field, a wrong signature or a value that
does not match its column are all 400 ``invalid_cursor``.
"""

import base64
import hashlib
import hmac
from typing import Any, Callable, Coroutine, Generic, Sequence, TypeVar

from core.errors import BadRequest, InvalidCursor
from pydantic import BaseModel, Field, ValidationError
from repository.params import QueryParams

T = TypeVar("T")

#: Largest page size the API accepts; ``paginate`` asks the repository for one
#: extra row to decide whether another page exists.
MAX_PAGE_SIZE = 100

#: Cursors are opaque, short strings. Anything longer is not one of ours.
MAX_CURSOR_LENGTH = 2048

#: Kept short: a 128 bit tag is plenty for a pagination cursor.
_SIGNATURE_LENGTH = 32


class InvalidSortField(BadRequest):
    code = "invalid_sort_field"
    message = "invalid sort field"


class Cursor(BaseModel):
    field: list[str]
    value: list[str]
    desc: bool
    #: ``True`` when this cursor points at the following page.
    next: bool


class Params(BaseModel):
    limit: int = Field(default=10, ge=1, le=MAX_PAGE_SIZE)
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


def parse_sort_fields(sort: str, allowed: Sequence[str]) -> list[str]:
    """Validate ``?sort=a,b`` against the fields an endpoint may sort by."""
    fields = [field.strip() for field in sort.split(",") if field.strip()]
    if not fields:
        raise InvalidSortField("sort field is required")

    for field in fields:
        if field not in allowed:
            raise InvalidSortField(
                f"invalid sort field '{field}', allowed fields: {', '.join(allowed)}"
            )
    return fields


def _sign(body: str, secret: str) -> str:
    return hmac.new(secret.encode("utf8"), body.encode("utf8"), hashlib.sha256).hexdigest()[
        :_SIGNATURE_LENGTH
    ]


def encode_cursor(cur: Cursor, secret: str) -> str:
    body = base64.urlsafe_b64encode(cur.model_dump_json().encode("utf8")).decode("utf8")
    return f"{body}.{_sign(body, secret)}"


def decode_cursor(cur: str, secret: str) -> Cursor:
    if not cur or len(cur) > MAX_CURSOR_LENGTH:
        raise InvalidCursor("cursor is malformed")

    body, _, signature = cur.rpartition(".")
    if not body or not signature:
        raise InvalidCursor("cursor is malformed")

    if not hmac.compare_digest(signature, _sign(body, secret)):
        raise InvalidCursor("cursor signature is invalid")

    try:
        payload = base64.urlsafe_b64decode(body)
        return Cursor.model_validate_json(payload)
    except (ValidationError, ValueError, TypeError) as exc:
        # A cursor is client supplied input: base64 errors and shape errors are
        # both "bad request", never an internal error.
        raise InvalidCursor("cursor is malformed") from exc


def parse_cursor(value: str | None, secret: str) -> Cursor | None:
    if not value:
        return None
    return decode_cursor(value, secret)


def validate_cursor(cur: Cursor, allowed: Sequence[str]) -> None:
    """Re-check a decoded cursor against the endpoint it is replayed on."""
    if not cur.field:
        raise InvalidCursor("cursor has no sort field")

    unknown = [field for field in cur.field if field not in allowed]
    if unknown:
        raise InvalidCursor(f"cursor uses an unsupported sort field: {', '.join(unknown)}")

    if len(cur.value) != len(cur.field):
        raise InvalidCursor("cursor value does not match its sort fields")


def _cursor_value(item: Any, fields: Sequence[str]) -> list[str]:
    return [str(getattr(item, field)) for field in fields]


async def paginate(
    params: Params,
    fn: Callable[[QueryParams], Coroutine[Any, Any, list[T]]],
    *,
    allowed_fields: Sequence[str],
    secret: str,
    default_sort: Sequence[str] = (),
) -> Paginated[T]:
    sort_fields = list(params.sort) or list(default_sort)
    if not sort_fields:
        raise InvalidSortField("this endpoint has no default sort order")

    # A keyset needs a unique tiebreaker, otherwise two rows with the same
    # rating can be skipped or repeated at a page boundary.
    if "id" not in sort_fields:
        sort_fields.append("id")

    desc = bool(params.desc)
    backward = False
    pointer: list[str] = []

    if params.cursor is not None:
        validate_cursor(params.cursor, allowed_fields)
        desc = params.cursor.desc
        sort_fields = list(params.cursor.field)
        pointer = list(params.cursor.value)
        backward = not params.cursor.next

    query_params = QueryParams(
        limit=params.limit + 1,
        sort_by=sort_fields,
        desc=not desc if backward else desc,
        pointer=pointer,
        username=params.username,
    )

    items = await fn(query_params)
    if not items:
        return Paginated(items=[])

    if backward:
        # The repository returned the rows in reverse order; restore the order
        # the caller expects (``desc``, not the flipped fetch direction).
        items.sort(
            key=lambda item: tuple(getattr(item, field) for field in sort_fields),
            reverse=desc,
        )

    extra = len(items) > params.limit
    if extra:
        # Drop the probe row: with a forward scan it is the row beyond the page,
        # with a backward scan it is the row before the page.
        if backward:
            items.pop(0)
        else:
            items.pop()

    if backward:
        has_prev = extra
        has_next = True
    else:
        has_next = extra
        has_prev = params.cursor is not None

    result = Paginated[T](items=items, has_next=has_next, has_prev=has_prev)
    if has_next:
        result.next_cursor = encode_cursor(
            Cursor(field=sort_fields, value=_cursor_value(items[-1], sort_fields), desc=desc, next=True),
            secret,
        )
    if has_prev:
        result.prev_cursor = encode_cursor(
            Cursor(field=sort_fields, value=_cursor_value(items[0], sort_fields), desc=desc, next=False),
            secret,
        )
    return result
