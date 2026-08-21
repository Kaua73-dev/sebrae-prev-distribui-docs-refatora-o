

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from src.core.config import settings


BCRYPT_MAX_PASSWORD_BYTES = 72


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(_encode_password(plain_password), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(_encode_password(plain_password), hashed_password.encode())


def create_access_token(user_id: int, email: str, role: str) -> str:
    issued_at = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "iat": issued_at,
        "exp": issued_at + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    }

    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


def _encode_password(plain_password: str) -> bytes:
    return plain_password.encode()[:BCRYPT_MAX_PASSWORD_BYTES]
