"""Account management router for /api/v1/account."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.app.schemas.account import (
    AccountDeletionRequest,
    AccountDeletionResponse,
    AccountResponse,
    AccountUpdateRequest,
)
from backend.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/account", tags=["account"])
security = HTTPBearer(auto_error=False)

try:
    from src.database.db import (
        authenticate_user,
        get_user_by_id,
    )
    SRC_AVAILABLE = True
except Exception as e:
    print(f"Warning: src modules not available: {e}")
    SRC_AVAILABLE = False

settings = get_settings()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        from jose import JWTError, jwt
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
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


@router.get("", response_model=AccountResponse)
def get_account(user: dict = Depends(get_current_user)):
    return user


@router.patch("", response_model=AccountResponse)
def update_account(req: AccountUpdateRequest, user: dict = Depends(get_current_user)):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")

    from src.database.db import _connect, _hash_password

    with _connect() as conn:
        if req.email is not None:
            existing = conn.execute(
                "SELECT id FROM users WHERE lower(email) = ? AND id != ?",
                (req.email.lower(), user["id"]),
            ).fetchone()
            if existing:
                raise HTTPException(status_code=400, detail="Email already in use")
            conn.execute("UPDATE users SET email = ? WHERE id = ?", (req.email, user["id"]))

        if req.new_password is not None:
            if req.current_password is None:
                raise HTTPException(status_code=400, detail="Current password required to change password")
            auth_user = authenticate_user(user["username"], req.current_password)
            if not auth_user:
                raise HTTPException(status_code=401, detail="Current password is incorrect")
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (_hash_password(req.new_password), user["id"]),
            )
            conn.execute("UPDATE refresh_tokens SET revoked = 1 WHERE user_id = ?", (user["id"],))

        conn.commit()
        updated_user = get_user_by_id(user["id"])
        return updated_user


@router.delete("", response_model=AccountDeletionResponse)
def delete_account(req: AccountDeletionRequest, user: dict = Depends(get_current_user)):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")

    if req.confirmation != "DELETE":
        raise HTTPException(status_code=400, detail="Confirmation must be 'DELETE'")

    user_auth = authenticate_user(user["username"], req.password)
    if not user_auth:
        logger.warning("Failed account deletion attempt for user: %s (invalid password)", user["username"])
        raise HTTPException(status_code=401, detail="Invalid password")

    from src.database.db import _connect, delete_portfolio
    deleted_at = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        portfolios = conn.execute("SELECT id FROM portfolios WHERE user_id = ?", (user["id"],)).fetchall()
        for p in portfolios:
            delete_portfolio(p["id"], user["id"])

        conn.execute("UPDATE refresh_tokens SET revoked = 1 WHERE user_id = ?", (user["id"],))
        conn.execute("DELETE FROM users WHERE id = ?", (user["id"],))
        conn.commit()

    logger.info("Account deleted for user: %s (ID: %d)", user["username"], user["id"])
    return {"message": "Account deleted successfully", "deleted_at": deleted_at}