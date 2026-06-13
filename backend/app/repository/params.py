from pydantic import BaseModel, Field


class QueryParams(BaseModel):
    limit: int = Field(default=10, lt=101)
    sort_by: str | None = None
    desc: bool | None = None
    pointer: str = ""