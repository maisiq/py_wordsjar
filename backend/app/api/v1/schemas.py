from pydantic import BaseModel


class SuccessResponse(BaseModel):
    success: bool = True


# auth

class CreateUserRequest(BaseModel):
    username: str
    password: str


class AuthenticateRequest(BaseModel):
    username: str
    password: str


class UserInfoResponse(BaseModel):
    username: str
    role: str


# exam

class GetJarWordResponse(BaseModel):
    name: str


class VerifyWordRequest(BaseModel):
    word_id: int
    answer: str
    reverse: bool = False


#  jar

class AddJarWordRequest(BaseModel):
    word_en: str
    status: str | None = None


# words

class GetWordResponse(BaseModel):
    name: str


class AddWordRequest(BaseModel):
    en: str
    ru: list[str]
    transcription: str

