import base64
import hashlib
import hmac
import os
import secrets
import time

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.app.database.connection import DATABASE_URL, SessionLocal
from backend.app.database.models import User

TOKEN_TTL_SECONDS = 60 * 60 * 12
PASSWORD_ITERATIONS = 600_000
bearer_scheme = HTTPBearer(auto_error=False)

_configured_secret = os.getenv("AUTH_SECRET_KEY")
if not _configured_secret and os.getenv("APP_ENV", "development").lower() == "production":
    raise RuntimeError("AUTH_SECRET_KEY must be configured in production.")
_token_secret = (_configured_secret or DATABASE_URL or "").encode("utf-8")
if not _token_secret:
    raise RuntimeError("Configure AUTH_SECRET_KEY before starting the API.")


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    salt_text = base64.urlsafe_b64encode(salt).decode("ascii")
    digest_text = base64.urlsafe_b64encode(digest).decode("ascii")
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt_text}${digest_text}"


def verify_password(password: str, encoded: str) -> bool:
    parts = encoded.split("$")
    if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
        # Upgrade the legacy demo seed's plaintext password at successful login.
        return hmac.compare_digest(password, encoded)
    try:
        iterations = int(parts[1])
        salt = base64.urlsafe_b64decode(parts[2].encode("ascii"))
        expected = base64.urlsafe_b64decode(parts[3].encode("ascii"))
    except (ValueError, TypeError):
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)


def create_access_token(user_id: int) -> str:
    expires_at = int(time.time()) + TOKEN_TTL_SECONDS
    payload = f"{user_id}.{expires_at}"
    signature = hmac.new(_token_secret, payload.encode("ascii"), hashlib.sha256).digest()
    encoded_signature = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")
    return f"{payload}.{encoded_signature}"


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Please sign in to continue.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized

    try:
        user_id_text, expires_text, provided_signature = credentials.credentials.split(".")
        payload = f"{user_id_text}.{expires_text}"
        expected_signature = hmac.new(
            _token_secret, payload.encode("ascii"), hashlib.sha256
        ).digest()
        expected_text = base64.urlsafe_b64encode(expected_signature).decode("ascii").rstrip("=")
        user_id = int(user_id_text)
        if int(expires_text) <= int(time.time()) or not hmac.compare_digest(
            provided_signature, expected_text
        ):
            raise unauthorized
    except (ValueError, TypeError):
        raise unauthorized from None

    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if user is None:
            raise unauthorized
        return user
    finally:
        db.close()


def require_path_user(
    user_id: str, current_user: User = Depends(get_current_user)
) -> User:
    if user_id != str(current_user.user_id):
        raise HTTPException(status_code=403, detail="You cannot access another user's data.")
    return current_user
