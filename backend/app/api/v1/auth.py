"""Authentication router for /api/v1/auth."""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from backend.app.schemas.auth import (
    AccountDeletionRequest,
    LoginRequest,
    MessageResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from backend.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer(auto_error=False)

try:
    from src.auth.password_reset import request_password_reset
    from src.auth.ses_email import EmailDeliveryError
    from src.database.db import (
        authenticate_user,
        create_user,
        get_user_by_id,
        reset_password_with_code,
    )

    SRC_AVAILABLE = True
except Exception as e:
    print(f"Warning: src modules not available: {e}")
    SRC_AVAILABLE = False

settings = get_settings()

ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> tuple[str, str]:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    jti = str(uuid.uuid4())
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"iat": now, "exp": expire, "type": "access", "jti": jti})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, jti


def create_refresh_token(data: dict) -> tuple[str, str]:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    jti = str(uuid.uuid4())
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"iat": now, "exp": expire, "type": "refresh", "jti": jti})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, jti


def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        if not SRC_AVAILABLE:
            raise HTTPException(status_code=503, detail="Backend modules not loaded")
        user = get_user_by_id(int(user_id))
        if not user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return user
    except (JWTError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")


async def get_current_user_from_refresh(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        if not SRC_AVAILABLE:
            raise HTTPException(status_code=503, detail="Backend modules not loaded")
        user = get_user_by_id(int(user_id))
        if not user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return user
    except (JWTError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, request: Request):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")

    user = authenticate_user(req.username, req.password)
    if not user:
        logger.warning("Failed login attempt for username: %s from IP: %s", req.username, request.client.host if request.client else "unknown")
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token, access_jti = create_access_token({"sub": str(user["id"]), "username": user["username"]})
    refresh_token, refresh_jti = create_refresh_token({"sub": str(user["id"]), "username": user["username"]})

    if SRC_AVAILABLE:
        from src.database.db import _connect
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO refresh_tokens (user_id, token_jti, expires_at, created_at, revoked)
                VALUES (?, ?, ?, ?, 0)
                """,
                (
                    user["id"],
                    refresh_jti,
                    (datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)).isoformat(),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()

    logger.info("User logged in: %s (ID: %d)", user["username"], user["id"])
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token": refresh_token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user.get("email", ""),
            "created_at": user.get("created_at", ""),
        },
    }


@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest, request: Request):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")

    user = create_user(req.username, req.email, req.password)
    if not user:
        logger.warning("Registration failed for username: %s (already exists)", req.username)
        raise HTTPException(status_code=400, detail="Username or email already exists")

    from src.database.db import create_portfolio
    create_portfolio(user["id"], "My Portfolio", "Default portfolio", "USD")

    access_token, access_jti = create_access_token({"sub": str(user["id"]), "username": user["username"]})
    refresh_token, refresh_jti = create_refresh_token({"sub": str(user["id"]), "username": user["username"]})

    if SRC_AVAILABLE:
        from src.database.db import _connect
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO refresh_tokens (user_id, token_jti, expires_at, created_at, revoked)
                VALUES (?, ?, ?, ?, 0)
                """,
                (
                    user["id"],
                    refresh_jti,
                    (datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)).isoformat(),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()

    logger.info("User registered: %s (ID: %d)", user["username"], user["id"])
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token": refresh_token,
        "user": {"id": user["id"], "username": user["username"], "email": req.email, "created_at": user.get("created_at", "")},
    }


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(req: RefreshTokenRequest, request: Request):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")

    try:
        payload = decode_token(req.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        user_id = payload.get("sub")
        jti = payload.get("jti")
        if user_id is None or jti is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        from src.database.db import _connect
        with _connect() as conn:
            row = conn.execute(
                "SELECT revoked, expires_at FROM refresh_tokens WHERE user_id = ? AND token_jti = ?",
                (int(user_id), jti),
            ).fetchone()
            if not row or row["revoked"]:
                logger.warning("Revoked or invalid refresh token used for user_id: %s", user_id)
                raise HTTPException(status_code=401, detail="Token revoked or invalid")
            expires_at = datetime.fromisoformat(row["expires_at"])
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) >= expires_at:
                raise HTTPException(status_code=401, detail="Refresh token expired")

            conn.execute("UPDATE refresh_tokens SET revoked = 1 WHERE token_jti = ?", (jti,))
            conn.commit()

        user = get_user_by_id(int(user_id))
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        new_access_token, new_access_jti = create_access_token({"sub": str(user["id"]), "username": user["username"]})
        new_refresh_token, new_refresh_jti = create_refresh_token({"sub": str(user["id"]), "username": user["username"]})

        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO refresh_tokens (user_id, token_jti, expires_at, created_at, revoked)
                VALUES (?, ?, ?, ?, 0)
                """,
                (
                    user["id"],
                    new_refresh_jti,
                    (datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)).isoformat(),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()

        logger.info("Token refreshed for user: %s (ID: %d)", user["username"], user["id"])
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "refresh_token": new_refresh_token,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user.get("email", ""),
                "created_at": user.get("created_at", ""),
            },
        }
    except (JWTError, TypeError, ValueError) as e:
        logger.warning("Invalid refresh token: %s", str(e))
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")


@router.post("/logout", response_model=MessageResponse)
def logout(req: RefreshTokenRequest, request: Request):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")

    try:
        payload = decode_token(req.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        jti = payload.get("jti")
        if jti:
            from src.database.db import _connect
            with _connect() as conn:
                conn.execute("UPDATE refresh_tokens SET revoked = 1 WHERE token_jti = ?", (jti,))
                conn.commit()
    except (JWTError, TypeError, ValueError):
        pass

    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def me(user: dict = Depends(get_current_user)):
    return user


@router.post("/password-reset/request", response_model=MessageResponse)
def password_reset_request(req: PasswordResetRequest, request: Request):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")

    try:
        request_password_reset(req.username, str(req.email))
    except EmailDeliveryError:
        logger.exception("Password-reset email delivery failed")
        raise HTTPException(
            status_code=503,
            detail="Password-reset email could not be delivered. Please try again.",
        )

    logger.info("Password reset requested for username: %s", req.username)
    return {"message": "If the account exists, a password reset code has been sent."}


@router.post("/password-reset/confirm", response_model=MessageResponse)
def password_reset_confirm(req: PasswordResetConfirm):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")

    changed = reset_password_with_code(
        req.username,
        str(req.email),
        req.code,
        req.new_password,
        settings.PASSWORD_RESET_MAX_ATTEMPTS,
    )
    if not changed:
        raise HTTPException(status_code=400, detail="Invalid or expired reset code")

    from src.database.db import _connect
    with _connect() as conn:
        conn.execute("UPDATE refresh_tokens SET revoked = 1 WHERE user_id = (SELECT id FROM users WHERE username = ?)", (req.username,))
        conn.commit()

    logger.info("Password reset confirmed for username: %s", req.username)
    return {"message": "Password reset complete"}


@router.delete("/account", response_model=MessageResponse)
def delete_account(req: AccountDeletionRequest, user: dict = Depends(get_current_user)):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")

    user_auth = authenticate_user(user["username"], req.password)
    if not user_auth:
        raise HTTPException(status_code=401, detail="Invalid password")

    from src.database.db import _connect, delete_portfolio
    with _connect() as conn:
        portfolios = conn.execute("SELECT id FROM portfolios WHERE user_id = ?", (user["id"],)).fetchall()
        for p in portfolios:
            delete_portfolio(p["id"], user["id"])

        conn.execute("UPDATE refresh_tokens SET revoked = 1 WHERE user_id = ?", (user["id"],))
        conn.execute("DELETE FROM users WHERE id = ?", (user["id"],))
        conn.commit()

    logger.info("Account deleted for user: %s (ID: %d)", user["username"], user["id"])
    return {"message": "Account deleted successfully"}