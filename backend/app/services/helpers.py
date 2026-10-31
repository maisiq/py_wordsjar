import asyncio
import datetime as dt
import secrets

from argon2 import PasswordHasher
from argon2 import exceptions as argon2_errors
from core import config
from core.errors import ExpiredTokenError, InvalidToken
from joserfc import errors as jose_errors
from joserfc import jwt
from joserfc.jwk import OctKey

# argon2id at 46 MiB is still above the OWASP recommendation (19 MiB) while
# costing half the memory of the previous 100 MiB setting.
_HASHER = PasswordHasher(
    time_cost=2,
    memory_cost=47104,
    parallelism=1,
    hash_len=32,
    salt_len=16,
)

#: Hashing is CPU bound and allocates the memory above, so a burst of sign-ins
#: must not spawn unbounded threads and exhaust the container.
_MAX_CONCURRENT_HASHES = 4
_hash_slots = asyncio.Semaphore(_MAX_CONCURRENT_HASHES)

_DUMMY_HASH: str | None = None


def hash_password(password: str) -> str:
    return _HASHER.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _HASHER.verify(hashed, plain)
    except argon2_errors.VerifyMismatchError:
        return False
    except argon2_errors.InvalidHashError:
        return False


async def hash_password_async(password: str) -> str:
    """Hash without blocking the event loop for ~40 ms."""
    async with _hash_slots:
        return await asyncio.to_thread(hash_password, password)


async def verify_password_async(plain: str, hashed: str) -> bool:
    async with _hash_slots:
        return await asyncio.to_thread(verify_password, plain, hashed)


async def verify_dummy_password(plain: str) -> None:
    """Spend the same time as a real verification.

    Without it an unknown username answers noticeably faster than a wrong
    password, which turns the login endpoint into a user enumeration oracle.
    """
    global _DUMMY_HASH

    if _DUMMY_HASH is None:
        _DUMMY_HASH = await hash_password_async(secrets.token_urlsafe(16))
    await verify_password_async(plain, _DUMMY_HASH)


def normalize_word(string: str) -> str:
    return string.lower().strip()


def normalize_username(string: str) -> str:
    return string.lower().strip()


def create_access_token(
    cfg: config.JWTSettings, key_material: str, username: str, role: str
) -> tuple[str, dt.datetime]:
    """Build a signed access token and return it with its expiry."""
    key = OctKey.import_key(key_material)

    now = dt.datetime.now(dt.UTC)
    expires_at = now + dt.timedelta(seconds=cfg.access_token_ttl)
    header = {
        "typ": "JWT",
        "alg": cfg.algorithm,
    }
    payload = {
        "iss": cfg.iss,
        "exp": expires_at,
        "iat": now,
        "sub": username,
        "role": role,
        "jti": secrets.token_urlsafe(16),
    }

    return jwt.encode(header, payload, key), expires_at


def decode_access_token(cfg: config.JWTSettings, key_material: str, token_string: str) -> dict:
    """Verify signature and registered claims, or raise a domain error.

    ``BadSignatureError`` is not a ``DecodeError`` in joserfc, so a forged token
    used to escape as an internal error; catching ``JoseError`` covers every
    failure of the token itself.
    """
    key = OctKey.import_key(key_material)

    try:
        token = jwt.decode(token_string, key, algorithms=[cfg.algorithm])
    except jose_errors.ExpiredTokenError as exc:
        raise ExpiredTokenError("access token has expired") from exc
    except jose_errors.JoseError as exc:
        raise InvalidToken("invalid access token") from exc

    claims_requests = jwt.JWTClaimsRegistry(
        iss={"essential": True, "value": cfg.iss},
        sub={"essential": True},
    )
    try:
        claims_requests.validate(token.claims)
    except jose_errors.ExpiredTokenError as exc:
        raise ExpiredTokenError("access token has expired") from exc
    except jose_errors.ClaimError as exc:
        raise InvalidToken("invalid access token") from exc

    return dict(token.claims)


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(64)