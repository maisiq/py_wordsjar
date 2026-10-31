"""Domain errors.

Each error carries the HTTP status and the machine readable code that the
exception handlers in :mod:`api.errors` put into the response, so services do
not need to know about HTTP at all.
"""


class AppError(Exception):
    """Base class for every expected, domain level failure."""

    status_code: int = 500
    code: str = "internal_error"
    message: str = "internal error"

    def __init__(self, message: str | None = None, *, code: str | None = None):
        if message is not None:
            self.message = message
        if code is not None:
            self.code = code
        super().__init__(self.message)


class BadRequest(AppError):
    status_code = 400
    code = "bad_request"
    message = "bad request"


class NotFound(AppError):
    status_code = 404
    code = "not_found"
    message = "not found"


class AlreadyExistsError(AppError):
    status_code = 409
    code = "already_exists"
    message = "already exists"


class NotDue(AppError):
    """The resource exists, but not in the state an action requires.

    Used by the exam: a word can be answered again only after its cooldown.
    """

    status_code = 409
    code = "not_due"
    message = "not due yet"


class AuthError(AppError):
    status_code = 401
    code = "invalid_credentials"
    message = "invalid credentials"


class ExpiredTokenError(AppError):
    status_code = 401
    code = "token_expired"
    message = "token has expired"


class InvalidToken(AppError):
    status_code = 401
    code = "invalid_token"
    message = "invalid token"


class InvalidCursor(BadRequest):
    code = "invalid_cursor"
    message = "invalid cursor"


class InternalError(AppError):
    status_code = 500
    code = "internal_error"
    message = "internal error"


class RateLimited(AppError):
    status_code = 429
    code = "rate_limited"
    message = "too many requests"

    def __init__(self, retry_after: int, message: str | None = None):
        self.retry_after = max(1, int(retry_after))
        super().__init__(message or f"too many requests, retry in {self.retry_after} seconds")