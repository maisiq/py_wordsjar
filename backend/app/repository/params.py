from pydantic import BaseModel, Field


class QueryParams(BaseModel):
    limit: int = Field(default=10, lt=101)
    sort_by: list[str] | None = None
    desc: bool | None = None
    pointer: list[str] = Field(default_factory=list)
    username: str | None = None