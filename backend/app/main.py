"""
backend/main.py  — FastAPI Backend for PARHARIQ AI
=======================================================================
REST API with JWT auth that wraps the existing src.* modules.
Endpoints: Auth, Portfolios, Holdings, Analysis, History, Benchmark, Account
Version: /api/v1
"""

import logging
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

sys.path.insert(0, PROJECT_ROOT)

from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, Field

from backend.app.api.v1 import account, auth, portfolio
from backend.app.middleware import (
    AuditLoggingMiddleware,
    RateLimitMiddleware,
    RequestIDMiddleware,
)
from backend.config import get_settings

logger = logging.getLogger(__name__)

try:
    from src.database.db import (
        get_portfolio_for_user,
        get_user_by_id,
        init_db,
    )

    SRC_AVAILABLE = True
except Exception as e:
    print(f"Warning: src modules not available: {e}")
    SRC_AVAILABLE = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    if SRC_AVAILABLE:
        init_db()
    yield


settings = get_settings()
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=60, auth_requests_per_minute=10)
app.add_middleware(AuditLoggingMiddleware)

security = HTTPBearer(auto_error=False)

ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"iat": now, "exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
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


INDIAN_STOCKS = {
    "TCS": "TCS.NS",
    "INFY": "INFY.NS",
    "RELIANCE": "RELIANCE.NS",
    "WIPRO": "WIPRO.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "ICICIBANK": "ICICIBANK.NS",
    "TATAMOTORS": "TATAMOTORS.NS",
    "BAJFINANCE": "BAJFINANCE.NS",
    "SBIN": "SBIN.NS",
    "AXISBANK": "AXISBANK.NS",
    "BHARTIARTL": "BHARTIARTL.NS",
    "ITC": "ITC.NS",
    "LT": "LT.NS",
    "MARUTI": "MARUTI.NS",
    "NESTLEIND": "NESTLEIND.NS",
    "TITAN": "TITAN.NS",
    "HINDUNILVR": "HINDUNILVR.NS",
    "KOTAKBANK": "KOTAKBANK.NS",
    "ASIANPAINT": "ASIANPAINT.NS",
    "ULTRACEMCO": "ULTRACEMCO.NS",
}


def normalize_ticker(ticker: str) -> tuple:
    t = ticker.strip().upper()
    if t in INDIAN_STOCKS:
        return INDIAN_STOCKS[t], t, "IN"
    if t.endswith(".NS"):
        return t, t.replace(".NS", ""), "IN"
    return t, t, "US"


def require_portfolio(portfolio_id: int, user_id: int) -> dict:
    portfolio = get_portfolio_for_user(portfolio_id, user_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=1, max_length=72)


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    email: EmailStr
    password: str = Field(..., min_length=12, max_length=72)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str
    user: dict


class PasswordResetRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    code: str = Field(..., pattern=r"^\d{6}$")
    new_password: str = Field(..., min_length=12, max_length=72)


class PortfolioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field("", max_length=500)
    currency: Literal["USD", "INR"] = "USD"


class HoldingCreate(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20, pattern=r"^[A-Za-z0-9.^-]+$")
    quantity: float = Field(..., gt=0)
    buy_price: float = Field(..., gt=0)
    buy_currency: Literal["USD", "INR"] = "USD"


class AnalysisRequest(BaseModel):
    portfolio_id: int = Field(..., gt=0)
    alpha: float = Field(0.6, ge=0.0, le=1.0)
    portfolio_value: float = Field(100000, ge=1000)
    use_llm: bool = True


app.include_router(auth.router, prefix="/api/v1")
app.include_router(portfolio.router, prefix="/api/v1")
app.include_router(account.router, prefix="/api/v1")


@app.get("/api/v1/health")
def health():
    return {
        "status": "ok",
        "version": settings.VERSION,
        "src_available": SRC_AVAILABLE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/v1")
def api_root():
    return {
        "message": "PARHARIQ AI API",
        "version": settings.VERSION,
        "docs": "/api/v1/docs",
        "health": "/api/v1/health",
    }


@app.get("/")
def root():
    return {
        "message": "PARHARIQ AI API",
        "version": settings.VERSION,
        "api": "/api/v1",
        "docs": "/api/v1/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)