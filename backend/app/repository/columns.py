"""Sort column maps and cursor value coercion.

Sort names reach the server from ``?sort=`` and, once a cursor exists, from the
cursor itself. They are resolved through an explicit ``{name: column}`` map:
looking a name up with ``getattr`` on two ORM classes at once silently produced a
cartesian product for fields that exist in both tables (``id``, ``en``, ...).
"""

import datetime as dt
from collections.abc import Mapping, Sequence

from core.errors import InvalidCursor
from sqlalchemy import ColumnElement


def resolve_columns(
    columns: Mapping[str, ColumnElement], names: Sequence[str]
) -> list[ColumnElement]:
    resolved: list[ColumnElement] = []
    for name in names:
        column = columns.get(name)
        if column is None:
            raise InvalidCursor(f"cannot sort by '{name}'")
        resolved.append(column)
    return resolved


def coerce_cursor_value(column: ColumnElement, raw: str):
    """Turn the string from a cursor back into the column's python type."""
    python_type = column.type.python_type

    if issubclass(python_type, dt.datetime):
        try:
            return dt.datetime.fromisoformat(raw)
        except ValueError as exc:
            raise InvalidCursor(f"cursor value '{raw}' is not a valid timestamp") from exc

    try:
        return python_type(raw)
    except (TypeError, ValueError) as exc:
        raise InvalidCursor(
            f"cursor value '{raw}' is not a valid {python_type.__name__}"
        ) from exc