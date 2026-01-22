"""Security utilities for authentication and encryption."""

from datetime import datetime, timedelta
from typing import Any

from cryptography.fernet import Fernet
from jose import jwt, JWTError
from passlib.context import CryptContext

from backend.app.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Fernet encryption for MT5 credentials
_fernet: Fernet | None = None


def get_fernet() -> Fernet:
    """Get or create Fernet instance."""
    global _fernet
    if _fernet is None:
        if settings.FERNET_KEY:
            _fernet = Fernet(settings.FERNET_KEY.encode())
        else:
            # Generate a new key for development
            key = Fernet.generate_key()
            _fernet = Fernet(key)
            print(f"WARNING: No FERNET_KEY set. Generated temporary key: {key.decode()}")
    return _fernet


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_access_token(
    subject: str | Any,
    expires_delta: timedelta | None = None,
) -> str:
    """Create JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(
    subject: str | Any,
    expires_delta: timedelta | None = None,
) -> str:
    """Create JWT refresh token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict | None:
    """Decode and verify JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError:
        return None


def encrypt_credentials(password: str) -> str:
    """Encrypt MT5 password using Fernet."""
    fernet = get_fernet()
    return fernet.encrypt(password.encode()).decode()


def decrypt_credentials(encrypted_password: str) -> str:
    """Decrypt MT5 password using Fernet."""
    fernet = get_fernet()
    return fernet.decrypt(encrypted_password.encode()).decode()
