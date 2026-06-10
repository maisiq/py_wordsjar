import datetime as dt
import secrets

from argon2 import PasswordHasher, exceptions
from core import config
from joserfc import errors, jwt
from joserfc.jwk import OctKey

_ph = PasswordHasher(
    time_cost=2,
    memory_cost=102400,
    parallelism=8,
    hash_len=32,
    salt_len=16
)

def hash_password(pw: str):
    return _ph.hash(pw)


def normalize_word(string: str):
    return string.lower().strip()


def normalize_username(string: str):
    return string.lower().strip()


def verify_password(plain: str, hashed: str):
    try:
        return _ph.verify(hashed, plain)
    except exceptions.VerifyMismatchError:
        return False


def create_access_token(valid_key: str, user_id: str, user_role: str):
    key = OctKey.import_key(valid_key)

    header = {
        "typ": "JWT", 
        "alg": config.JWT_ALGORITHM,
    }

    exp = dt.datetime.now(dt.UTC) + dt.timedelta(seconds=config.ACCESS_TOKEN_TTL)
    payload = {
        "iss": config.JWT_ISS,
        "exp": exp,
        "sub": user_id,
        "role": user_role,
    }

    ss = jwt.encode(header, payload, key)
    return ss


def validate_access_token(valid_key: str, token_string: str) -> str | None:
    key = OctKey.import_key(valid_key)
    try:
        token = jwt.decode(token_string, key)
    except errors.DecodeError as e:
        return

    claims_requests = jwt.JWTClaimsRegistry(
        iss={"essential": True, "value": config.JWT_ISS},
        sub={"essential": True},
    )
    try:
        claims_requests.validate(token.claims)
    except errors.ClaimError as e:
        return

    username = token.claims["sub"]
    return username


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(64)