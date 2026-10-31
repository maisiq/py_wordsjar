from pydantic import BaseModel, Field


class QueryParams(BaseModel):
    #: Fetch limit is the page size plus one extra row (see ``paginate``).
    limit: int = Field(default=10, ge=1, le=101)
    sort_by: list[str] | None = None
    desc: bool | None = None
    pointer: list[str] = Field(default_factory=list)
    username: str | None = None