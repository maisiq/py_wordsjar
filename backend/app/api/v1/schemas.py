from pydantic import BaseModel, Field

#: Usernames end up in logs and in the ``sub`` claim, so keep them boring.
USERNAME_PATTERN = r"^[A-Za-z0-9_.-]{3,32}$"


class SuccessResponse(BaseModel):
    success: bool = True


# auth

class CreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=USERNAME_PATTERN)
    password: str = Field(min_length=8, max_length=128)


class AuthenticateRequest(BaseModel):
    # No minimum length on login: existing accounts must stay usable even if
    # their password predates the current policy.
    username: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=128)


class UserInfoResponse(BaseModel):
    username: str
    role: str


class TokensResponse(BaseModel):
    access_token: str = Field(validation_alias="access")
    refresh_token: str = Field(validation_alias="refresh")


# exam

class GetJarWordResponse(BaseModel):
    name: str


class VerifyWordRequest(BaseModel):
    word_id: int
    answer: str
    reverse: bool = False


#  jar

class AddJarWordRequest(BaseModel):
    words_en: list[str] = Field(min_length=1, max_length=1000)
    status: str | None = None


class DeleteJarWordRequest(BaseModel):
    word: str = Field(min_length=1, max_length=64)


class AddWordsToJarResponse(BaseModel):
    count: int


# words

class WordAPI(BaseModel):
    en: str
    ru: list[str]
    transcription: str
    examples: list[str] | None = Field(default_factory=list)
    in_jar: bool


class GetWordResponse(BaseModel):
    name: str


class AddWordRequest(BaseModel):
    en: str = Field(min_length=1, max_length=64)
    ru: list[str] = Field(min_length=1)
    transcription: str = Field(default="", max_length=128)
    examples: list[str] | None = None


class SearchResponse(BaseModel):
    items: list[WordAPI]